"""Fixed primary score inference; explicitly separate exploratory outputs."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, math, platform
import importlib.metadata as metadata
import numpy as np
import pandas as pd
from scipy import optimize, stats

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def score_z(x1,n1,x0,n0,delta=0.0):
    """MN-corrected score for a risk difference, via constrained binomial MLE.

    Intended for nonboundary cells; the approved min-cell gate runs first.
    p0 is nuisance, p1=p0+delta; log-likelihood is strictly concave.
    """
    if min(x1,n1-x1,x0,n0-x0)<=0:
        raise ValueError('Boundary binomial cell: review required')
    if delta==0:
        p0=p1=(x1+x0)/(n1+n0)
    else:
        lo=max(0.,-delta); hi=min(1.,1.-delta)
        eps=min(1e-12,(hi-lo)/1000)
        def derivative(p):
            p1=p+delta
            return x1/p1-(n1-x1)/(1-p1)+x0/p-(n0-x0)/(1-p)
        p0=optimize.brentq(derivative,lo+eps,hi-eps,xtol=1e-14,rtol=1e-14)
        p1=p0+delta
    variance=(p1*(1-p1)/n1+p0*(1-p0)/n0)*(n1+n0)/(n1+n0-1)
    return float((x1/n1-x0/n0-delta)/math.sqrt(variance))

def score_interval(x1,n1,x0,n0,alpha):
    estimate=x1/n1-x0/n0
    critical=stats.norm.isf(alpha/2)
    # Fixed expanding bracket around estimate, never selected on a resulting p-value.
    def bound(direction):
        target=critical if direction<0 else -critical
        endpoint=estimate
        step=1e-4
        for _ in range(30):
            endpoint=max(-.999999,min(.999999,estimate+direction*step))
            value=score_z(x1,n1,x0,n0,endpoint)-target
            if (direction<0 and value>=0) or (direction>0 and value<=0):
                a,b=sorted([estimate,endpoint])
                return float(optimize.brentq(lambda d:score_z(x1,n1,x0,n0,d)-target,a,b,xtol=1e-13))
            step*=2
        raise RuntimeError('Score interval bracketing failed')
    return bound(-1),bound(1)

def benchmark_interpretation(low,high,benchmark):
    if low>=benchmark:
        return '区间下限超过+0.10pp：支持至少达到情景基准；不代表已证明盈利。'
    if high<0:
        return '区间完全低于0：存在负向效果证据。'
    if low>0:
        if high<benchmark:
            return '正向效果有证据，但区间上限低于+0.10pp，未达到情景基准。'
        return '正向效果有证据，但区间仍包含低于+0.10pp的提升，无法确认至少达到基准。'
    if high<benchmark:
        return '未检出正向效果，区间上限低于+0.10pp；可排除该大小提升，但不是证明严格零效果。'
    return '区间跨零且包含+0.10pp：证据不足，不能排除无效、负面或有意义的正向提升。'

def binary_comparison(df,treatment,control,outcome,alpha,primary=False,minimum=10):
    t=df[df.segment.eq(treatment)][outcome]
    c=df[df.segment.eq(control)][outcome]
    x1,n1,x0,n0=int(t.sum()),len(t),int(c.sum()),len(c)
    result={'treatment':treatment,'control':control,'outcome':outcome,'n_treatment':n1,'n_control':n0,
            'events_treatment':x1,'events_control':x0,'rate_treatment':x1/n1,'rate_control':x0/n0,
            'difference':x1/n1-x0/n0,'confidence_level':1-alpha,'status':'ok'}
    if min(x1,n1-x1,x0,n0-x0)<minimum:
        result.update(status='paused_sparse_cell',ci_low=None,ci_high=None)
        return result
    try:
        low,high=score_interval(x1,n1,x0,n0,alpha)
    except Exception as error:
        result.update(status='paused_interval_failure',ci_low=None,ci_high=None,error=str(error))
        return result
    result.update(ci_low=low,ci_high=high)
    if primary:
        z=score_z(x1,n1,x0,n0)
        p=float(2*stats.norm.sf(abs(z)))
        result.update(z=z,p_raw=p,p_bonferroni=min(2*p,1.),significant_bonferroni=min(2*p,1.)<.05,
                      delta_per_10000=result['difference']*10000,
                      interpretation=benchmark_interpretation(low,high,.001))
    return result

def bootstrap_means(values,resamples,seed):
    """Ordinary empirical row bootstrap via multinomial counts, retaining zeros."""
    unique,counts=np.unique(np.asarray(values,dtype=float),return_counts=True)
    n=len(values); rng=np.random.default_rng(seed)
    result=np.empty(resamples)
    for start in range(0,resamples,1000):
        size=min(1000,resamples-start)
        draws=rng.multinomial(n,counts/n,size=size)
        result[start:start+size]=(draws@unique)/n
    return result

def freeze():
    paths=['config/execution.json','docs/EXECUTION_SCOPE.md','scripts/analyze.py','requirements.txt','tests/test_inference.py']
    manifest={p:sha(ROOT/p) for p in paths}
    path=ROOT/'docs/pre_run_freeze.json'
    if path.exists():
        assert json.loads(path.read_text(encoding='utf-8'))['sha256']==manifest,'Frozen analysis implementation changed'
    else:
        path.write_text(json.dumps({'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'sha256':manifest},indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--out',type=Path,default=ROOT/'reports')
    args=parser.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    freeze()
    cfg=json.loads((ROOT/'config/execution.json').read_text(encoding='utf-8')); primary_cfg=cfg['primary']
    source=json.loads((ROOT/'data/raw/source_manifest.json').read_text(encoding='utf-8'))
    raw=ROOT/'data/raw/hillstrom.csv'; assert sha(raw)==source['csv_sha256']
    audit=json.loads((ROOT/'history/audit/reports/audit_results.json').read_text(encoding='utf-8'))
    assert not audit['structural_blockers'], 'Unresolved audit blockers'
    df=pd.read_csv(raw); assert len(df)==audit['n']==64000
    assert not df[['segment','conversion','visit','spend']].isna().any().any()
    assert set(df.segment)=={*primary_cfg['treatments'],primary_cfg['control']}
    assert df.conversion.isin([0,1]).all() and df.visit.isin([0,1]).all() and df.spend.ge(0).all()
    df['region']=df.zip_code.replace({'Surburban':'Suburban'})
    assert df.region.isin(cfg['regions']).all()
    primary=[]; region=[]; visit=[]; spend=[]
    for t in primary_cfg['treatments']:
        primary.append(binary_comparison(df,t,primary_cfg['control'],'conversion',primary_cfg['per_comparison_alpha'],True))
        visit.append(binary_comparison(df,t,primary_cfg['control'],'visit',cfg['exploratory_alpha']))
        for r in cfg['regions']:
            region.append({'region':r,**binary_comparison(df[df.region.eq(r)],t,primary_cfg['control'],'conversion',cfg['exploratory_alpha'])})
    boot=cfg['bootstrap']; draws={}
    for i,g in enumerate([primary_cfg['control'],*primary_cfg['treatments']]):
        draws[g]=bootstrap_means(df.loc[df.segment.eq(g),'spend'],boot['resamples'],[boot['seed'],i])
    for t in primary_cfg['treatments']:
        c=primary_cfg['control']; a=df.loc[df.segment.eq(t),'spend']; b=df.loc[df.segment.eq(c),'spend']
        diff=draws[t]-draws[c]
        low,high=np.quantile(diff,[.025,.975],method=boot['quantile_method'])
        spend.append({'treatment':t,'control':c,'n_treatment':len(a),'n_control':len(b),
            'mean_treatment':float(a.mean()),'mean_control':float(b.mean()),'difference':float(a.mean()-b.mean()),
            'ci_low':float(low),'ci_high':float(high),'confidence_level':.95,'resamples':boot['resamples'],
            'method':'within-group empirical bootstrap percentile; exploratory; no multiplicity correction'})
    for name,rows in [('primary_conversion',primary),('exploratory_regions',region),('exploratory_visit',visit),('exploratory_spend',spend)]:
        pd.DataFrame(rows).to_csv(args.out/(name+'.csv'),index=False,encoding='utf-8',lineterminator='\n',float_format='%.15g')
    pd.DataFrame(draws).to_csv(args.out/'bootstrap_group_means.csv',index=False,float_format='%.15g',lineterminator='\n')
    result={'primary':primary,'exploratory_regions':region,'exploratory_visit':visit,'exploratory_spend':spend,
        'n_retained':len(df),'rows_dropped':0,'identical_rows_retained':audit['identical_rows_all_members'],
        'data_sha256':sha(raw),'execution_sha256':sha(ROOT/'config/execution.json'),
        'method':'MN-corrected score test and numerical inversion; Bonferroni only for 2 overall conversion comparisons',
        'regional_note':'Six nominal 95% intervals; exploratory, not simultaneous, no p-values or interaction tests',
        'benchmark':primary_cfg['benchmark'],'published':False,
        'environment':{'python':platform.python_version(),**{p:metadata.version(p) for p in ['numpy','pandas','scipy','statsmodels']}}}
    (args.out/'effects_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'primary':primary,'regions':region,'spend':spend},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
