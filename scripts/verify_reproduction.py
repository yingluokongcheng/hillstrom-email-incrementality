from pathlib import Path
from datetime import datetime, timezone
import argparse,csv,hashlib,json,math,os,shutil,subprocess,sys
from collections import Counter
import numpy as np
from scipy import stats
from statsmodels.stats.proportion import test_proportions_2indep
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_inference import corrected_polynomial_reference

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args(); dest=args.destination.resolve()
    assert not dest.exists(), 'Use a new directory; existing evidence is preserved'
    dest.mkdir(parents=True)
    for folder in ['config','docs','data','scripts','tests','history']:
        shutil.copytree(ROOT/folder,dest/folder,ignore=shutil.ignore_patterns('__pycache__'))
    for name in ['requirements.txt','README.md','README.zh-CN.md']:
        shutil.copy2(ROOT/name,dest/name)
    env={**os.environ,'PYTHONIOENCODING':'utf-8'}
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],capture_output=True,text=True,encoding='utf-8',env=env)
    (ROOT/'reports/packaging_test_results.txt').write_text(tests.stdout+tests.stderr,encoding='utf-8')
    assert tests.returncode==0
    rerun=subprocess.run([sys.executable,str(dest/'scripts/run_offline.py')],cwd=dest,capture_output=True,text=True,encoding='utf-8',env=env)
    (dest/'run.log').write_text(rerun.stdout+rerun.stderr,encoding='utf-8'); assert rerun.returncode==0,rerun.stderr
    compared=[]
    for p in sorted((dest/'reports').iterdir()):
        same=p.read_bytes()==(ROOT/'reports'/p.name).read_bytes()
        compared.append({'file':p.name,'sha256':sha(p),'byte_identical':same})
    assert all(x['byte_identical'] for x in compared)
    # Separate standard-library census verifies data denominators without pandas aggregation.
    with (ROOT/'data/raw/hillstrom.csv').open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    counts=Counter(x['segment'] for x in rows)
    events=Counter(x['segment'] for x in rows if x['conversion']=='1')
    result=json.loads((ROOT/'reports/effects_results.json').read_text(encoding='utf-8'))
    assert len(rows)==result['n_retained']==64000 and result['rows_dropped']==0
    checked=[]
    for r in result['primary']+result['exploratory_regions']+result['exploratory_visit']:
        assert r['status']=='ok'
        if r in result['primary']:
            assert counts[r['treatment']]==r['n_treatment'] and events[r['treatment']]==r['events_treatment']
            ref=test_proportions_2indep(r['events_treatment'],r['n_treatment'],r['events_control'],r['n_control'],
                                       value=0,method='score',compare='diff',correction=True)
            assert abs(ref.pvalue-r['p_raw'])<1e-12
            assert r['p_bonferroni']==min(2*r['p_raw'],1.)
            assert (r['ci_low']>0 or r['ci_high']<0)==r['significant_bonferroni']
        elif r in result['exploratory_regions']:
            assert 'p_raw' not in r and 'p_bonferroni' not in r
        for edge in ['ci_low','ci_high']:
            z=corrected_polynomial_reference(r['events_treatment'],r['n_treatment'],r['events_control'],r['n_control'],r[edge])
            p=float(2*stats.norm.sf(abs(z)))
            assert abs(p-(1-r['confidence_level']))<1e-7
        checked.append({'outcome':r['outcome'],'region':r.get('region','Overall'),'treatment':r['treatment'],'endpoint_reference_passed':True})
    preservation=json.loads((ROOT/'docs/audit_preservation.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/'history/audit'/p)==h for p,h in preservation.items())
    from html.parser import HTMLParser
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            if tag=='a':self.links += [v for k,v in attrs if k=='href' and not v.startswith(('http:','https:','#'))]
    links=Links();links.feed((ROOT/'reports/Hillstrom总体效果与地区探索.html').read_text(encoding='utf-8'))
    missing=[p for p in links.links if p!='verification.json' and not (ROOT/'reports'/p).exists()]
    assert not missing,missing
    payload={'verified_at_utc':datetime.now(timezone.utc).isoformat(),'tests_passed':True,'test_methods':8,
             'independent_census_passed':True,'independent_score_checks':checked,
             'reproduced_outputs':compared,'all_byte_identical':True,'verification_scope':'Standalone package; original sibling project is not required',
             'archived_audit_files_byte_identical':len(preservation),'local_html_links_checked':len(links.links),
             'network_block':'Python socket connection and DNS disabled, not operating-system firewall',
             'independent_directory':str(dest),'published':False,
             'pre_effect_validation_history':'Two synthetic reference failures with statsmodels 0.14.4 and 0.15.0; nonzero-null library coefficient bug. Kept MN-score direct likelihood solver, validated with corrected independent polynomial. No tolerance relaxation or effect-driven change.'}
    (ROOT/'reports/packaging_verification.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'tests':8,'reproduced_outputs':len(compared),'independent_score_checks':len(checked),
                      'archived_audit_verified':len(preservation),'all_byte_identical':True}))
if __name__=='__main__':main()
