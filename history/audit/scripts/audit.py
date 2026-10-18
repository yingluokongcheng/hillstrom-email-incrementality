"""Offline audit only. No treatment effect estimates, tests or effect intervals."""
from pathlib import Path
import argparse, hashlib, itertools, json, math, platform
import importlib.metadata as metadata
import numpy as np
import pandas as pd
from scipy import stats, optimize

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COLUMNS = ['recency','history_segment','history','mens','womens','zip_code',
                    'newbie','channel','segment','visit','conversion','spend']
REGION_ALIAS = {'Surburban': 'Suburban'}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def scenario_power(n_t, n_c, baseline, delta, alpha=0.025):
    """Normal score planning approximation; no observed outcomes are accepted."""
    p_t, p_c = baseline + delta, baseline
    if not (n_t > 1 and n_c > 1 and 0 < p_t < 1 and 0 < p_c < 1):
        raise ValueError('Invalid planning parameters')
    p_pool = (n_t*p_t + n_c*p_c)/(n_t+n_c)
    null_var = p_pool*(1-p_pool)*(1/n_t + 1/n_c)
    null_var *= (n_t+n_c)/(n_t+n_c-1)  # same finite-n variance correction as planned score test
    alt_var = p_t*(1-p_t)/n_t + p_c*(1-p_c)/n_c
    cutoff = stats.norm.isf(alpha/2)*math.sqrt(null_var)
    sd = math.sqrt(alt_var)
    return float(stats.norm.sf((cutoff-delta)/sd) + stats.norm.cdf((-cutoff-delta)/sd))

def mde(n_t, n_c, baseline, power, alpha):
    return float(optimize.brentq(lambda d: scenario_power(n_t,n_c,baseline,d,alpha)-power,
                                1e-10, min(0.5, 0.999-baseline)))

def required_n(baseline, delta, power, alpha):
    return math.ceil(optimize.brentq(lambda n: scenario_power(n,n,baseline,delta,alpha)-power,
                                    2, 1e8))

def count_table(frame, keys):
    # Counts expose outcomes for audit; deliberately do not compute rates or differences.
    table = frame.groupby(keys, observed=True, dropna=False).agg(
        n=('conversion','size'), purchases=('conversion',lambda s: int((s==1).sum())),
        nonpurchases=('conversion',lambda s: int((s==0).sum())),
        missing_purchase=('conversion',lambda s: int(s.isna().sum())))
    return table.reset_index()

def balance(frame, groups):
    columns = {'history': frame.history, 'recency': frame.recency}
    for name in ['mens','womens','newbie']:
        columns[name] = frame[name]
    for name in ['history_segment','region','channel']:
        for level in sorted(frame[name].dropna().unique()):
            columns[f'{name}={level}'] = frame[name].eq(level).astype(float).where(frame[name].notna())
    rows = []
    for name, series in columns.items():
        for a,b in itertools.combinations(groups,2):
            x = series[frame.segment.eq(a)].dropna()
            y = series[frame.segment.eq(b)].dropna()
            denom = math.sqrt((x.var(ddof=1)+y.var(ddof=1))/2)
            smd = (x.mean()-y.mean())/denom if denom else (0 if x.mean()==y.mean() else float('inf'))
            rows.append({'variable':name,'group_a':a,'group_b':b,'n_a':len(x),'n_b':len(y),
                         'mean_or_share_a':float(x.mean()),'mean_or_share_b':float(y.mean()),
                         'smd':float(smd),'abs_smd':float(abs(smd))})
    return pd.DataFrame(rows)

def quality_checks(df, groups, regions):
    numeric = ['recency','history','mens','womens','newbie','visit','conversion','spend']
    f = df.copy()
    masks = {}
    for col in numeric:
        x = pd.to_numeric(f[col], errors='coerce')
        masks[f'{col}:non_numeric_or_nonfinite'] = f[col].notna() & (~np.isfinite(x))
        f[col] = x
    for col in ['mens','womens','newbie','visit','conversion']:
        masks[f'{col}:not_binary'] = f[col].notna() & ~f[col].isin([0,1])
    masks['recency:outside_integer_1_12'] = f.recency.notna() & (~f.recency.between(1,12) | (f.recency%1!=0))
    for col in ['history','spend']:
        masks[f'{col}:negative'] = f[col].lt(0)
    masks['segment:unknown'] = f.segment.notna() & ~f.segment.isin(groups)
    f['region'] = f.zip_code.replace(REGION_ALIAS)
    masks['region:unknown'] = f.region.notna() & ~f.region.isin(regions)
    masks['channel:unknown'] = f.channel.notna() & ~f.channel.isin(['Phone','Web','Multichannel'])
    bands = ['1) $0 - $100','2) $100 - $200','3) $200 - $350','4) $350 - $500',
             '5) $500 - $750','6) $750 - $1,000','7) $1,000 +']
    masks['history_segment:unknown'] = f.history_segment.notna() & ~f.history_segment.isin(bands)
    # Inclusive endpoints avoid imposing undocumented boundary rounding rules.
    bounds = [(0,100),(100,200),(200,350),(350,500),(500,750),(750,1000),(1000,np.inf)]
    mismatch = pd.Series(False,index=f.index)
    for band,(lo,hi) in zip(bands,bounds):
        mismatch |= f.history_segment.eq(band) & f.history.notna() & ~f.history.between(lo,hi)
    masks['history:outside_labeled_band'] = mismatch
    masks['conversion1_spend_not_positive'] = f.conversion.eq(1) & f.spend.notna() & f.spend.le(0)
    masks['conversion0_spend_positive'] = f.conversion.eq(0) & f.spend.gt(0)
    masks['conversion1_visit0'] = f.conversion.eq(1) & f.visit.eq(0)
    return f, masks

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data',type=Path, default=ROOT/'data/raw/hillstrom.csv')
    parser.add_argument('--out',type=Path, default=ROOT/'reports')
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    plan = json.loads((ROOT/'config/plan.json').read_text(encoding='utf-8'))
    source = json.loads((ROOT/'data/raw/source_manifest.json').read_text(encoding='utf-8'))
    assert sha(args.data) == source['csv_sha256'], 'Raw data hash mismatch'
    for rel, expected in source['frozen_plan_sha256_before_download'].items():
        assert sha(ROOT/rel.replace('\\','/')) == expected, 'Frozen plan changed'
    df = pd.read_csv(args.data, keep_default_na=True)
    assert list(df.columns) == EXPECTED_COLUMNS, 'Unexpected schema; review before proceeding'
    strings = df.select_dtypes(include=['object','string']).columns
    for col in strings:
        # Treat whitespace-only text as missing for audit, but do not alter valid raw values.
        df[col] = df[col].replace(r'^\s*$', np.nan, regex=True)
    f, masks = quality_checks(df,plan['groups'],plan['regions'])
    tables = {}
    tables['missingness'] = pd.DataFrame({'column':df.columns,'missing':df.isna().sum().values,
                                         'dtype':[str(t) for t in df.dtypes]})
    missing_by_group = []
    for label,g in df.groupby('segment',dropna=False):
        for col in df.columns:
            missing_by_group.append({'segment':str(label),'column':col,'n':len(g),'missing':int(g[col].isna().sum())})
    tables['missingness_by_group'] = pd.DataFrame(missing_by_group)
    tables['group_counts'] = count_table(f,['segment'])
    tables['group_counts']['allocation_pct'] = 100*tables['group_counts'].n/len(f)
    tables['region_group_counts'] = count_table(f,['region','segment'])
    tables['anomaly_summary'] = pd.DataFrame([{'check':k,'rows':int(v.sum())} for k,v in masks.items()])
    anomaly_rows = [{'csv_line':int(i)+2,'check':name} for name,mask in masks.items() for i in f.index[mask]]
    tables['anomaly_rows'] = pd.DataFrame(anomaly_rows,columns=['csv_line','check'])
    duplicate_all = df.duplicated(keep=False)
    duplicate_excess = df.duplicated(keep='first')
    tables['identical_rows'] = df.loc[duplicate_all].copy()
    tables['identical_rows'].insert(0,'csv_line',df.index[duplicate_all]+2)
    tables['region_alias'] = pd.DataFrame([{'raw_label':k,'display_label':v,'rows':int(df.zip_code.eq(k).sum())} for k,v in REGION_ALIAS.items()])
    counts = f.segment.value_counts().reindex(plan['groups'],fill_value=0)
    srm = stats.chisquare(counts.to_numpy(),np.full(3,len(f)/3))
    tables['baseline_balance'] = balance(f,plan['groups'])
    numeric_cols = ['recency','history','mens','womens','newbie','visit','conversion','spend']
    tables['numeric_ranges'] = f[numeric_cols].agg(['min','max']).T.reset_index(names='column')
    # Only pre-specified baseline/effect scenarios and observed allocation sizes enter planning.
    sizes = [('Overall',f)] + [(r,f[f.region.eq(r)]) for r in plan['regions']]
    power_rows,mde_rows=[],[]
    for label, subset in sizes:
        ns = subset.segment.value_counts()
        for treatment in plan['groups'][:2]:
            nt,nc = int(ns.get(treatment,0)),int(ns.get('No E-Mail',0))
            if min(nt,nc) < 2:
                continue
            for base in plan['baseline_rates']:
                for delta in plan['effects']:
                    power_rows.append({'population':label,'treatment':treatment,'n_treatment':nt,'n_control':nc,
                        'baseline_scenario':base,'delta_scenario':delta,'alpha':plan['comparison_alpha'],
                        'power_approx':scenario_power(nt,nc,base,delta,plan['comparison_alpha'])})
                for target in plan['powers']:
                    mde_rows.append({'population':label,'treatment':treatment,'baseline_scenario':base,
                        'target_power':target,'mde_probability':mde(nt,nc,base,target,plan['comparison_alpha'])})
    tables['scenario_power'] = pd.DataFrame(power_rows)
    tables['scenario_mde'] = pd.DataFrame(mde_rows)
    requirements=[]
    for base,delta,target in itertools.product(plan['baseline_rates'],plan['effects'],plan['powers']):
        n = required_n(base,delta,target,plan['comparison_alpha'])
        requirements.append({'baseline_scenario':base,'delta_scenario':delta,'target_power':target,
                             'n_per_arm_equal':n,'n_three_arms_equal':3*n})
    tables['scenario_required_n'] = pd.DataFrame(requirements)
    blockers=[]
    if len(df)!=plan['expected_n']: blockers.append('Row count differs from published description')
    if float(srm.pvalue)<plan['srm_alpha']: blockers.append('Global SRM flag')
    if df[['segment','conversion']].isna().any().any(): blockers.append('Missing group or primary outcome')
    if sum(int(v.sum()) for k,v in masks.items() if k.startswith(('segment:','conversion:'))):
        blockers.append('Invalid group or primary outcome')
    if any(int(masks[k].sum()) for k in ['conversion1_spend_not_positive','conversion0_spend_positive','conversion1_visit0']):
        blockers.append('Outcome inconsistency requires review')
    if tables['group_counts'][['purchases','nonpurchases']].min().min()<plan['sparse_cell_min']:
        blockers.append('Sparse overall outcome cell')
    sparse_regions = tables['region_group_counts'].loc[
        tables['region_group_counts'][['purchases','nonpurchases']].min(axis=1)<plan['sparse_cell_min'], ['region','segment']].to_dict('records')
    result = {
        'stage':'audit_only_awaiting_user_review','n':len(df),'columns':len(df.columns),
        'raw_sha256':sha(args.data),'plan_sha256':sha(ROOT/'config/plan.json'),
        'srm':{'chi2':float(srm.statistic),'df':2,'p':float(srm.pvalue),'threshold':plan['srm_alpha']},
        'missing_cells':int(df.isna().sum().sum()),
        'anomaly_flags':int(sum(int(v.sum()) for v in masks.values())),
        'identical_rows_all_members':int(duplicate_all.sum()),'identical_rows_excess':int(duplicate_excess.sum()),
        'identical_row_patterns':int(df.loc[duplicate_all].drop_duplicates().shape[0]),
        'identical_rows_with_history_29_99':int((duplicate_all & f.history.eq(29.99)).sum()),
        'rows_dropped':0,'rows_imputed':0,'customer_id_available':False,
        'baseline_max_abs_smd':float(tables['baseline_balance'].abs_smd.max()),
        'baseline_features_abs_smd_over_0_1':int((tables['baseline_balance'].abs_smd>0.1).sum()),
        'minimum_overall_outcome_cell':int(tables['group_counts'][['purchases','nonpurchases']].min().min()),
        'minimum_region_outcome_cell':int(tables['region_group_counts'][['purchases','nonpurchases']].min().min()),
        'sparse_regions':sparse_regions,'structural_blockers':blockers,
        'effects_computed':False,
        'outcome_exposure':'Group/region purchase counts and row logic inspected for audit. This is not blinded analysis.',
        'limitations':['Mirror checksum matches its documentation, but original bytes not compared.',
            'No customer ID, assignment log, delivery log, exact timestamps, costs or unsubscribe data.',
            'Identical rows retained: unique customers and original roster coverage cannot be independently verified.',
            'Region has three urbanicity labels, not city/province or cultural preference measures.',
            'Power and MDE use hypothetical rates, not observed treatment differences; approximations, not guarantees.'],
        'environment':{'python':platform.python_version(),**{p:metadata.version(p) for p in ['numpy','pandas','scipy']}}
    }
    for name,table in tables.items():
        table.to_csv(out/(name+'.csv'),index=False,encoding='utf-8',lineterminator='\n',float_format='%.12g')
    (out/'audit_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
