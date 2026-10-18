import csv, json, math, sys, unittest
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit import scenario_power, required_n, mde, quality_checks, count_table

class AuditTests(unittest.TestCase):
    def test_null_size_and_sample_growth(self):
        self.assertAlmostEqual(scenario_power(20000,20000,.01,0),.025,places=5)
        self.assertGreater(scenario_power(40000,40000,.01,.001),scenario_power(20000,20000,.01,.001))

    def test_equal_n_closed_form_planning(self):
        # Independent common textbook large-sample formula; tiny lower tail and finite-n correction differ.
        p0,p1,alpha,power=.01,.011,.025,.8
        q=(p0+p1)/2
        n=((stats.norm.isf(alpha/2)*math.sqrt(2*q*(1-q))+
            stats.norm.ppf(power)*math.sqrt(p0*(1-p0)+p1*(1-p1)))/(p1-p0))**2
        self.assertLess(abs(required_n(p0,p1-p0,power,alpha)-n)/n,0.0001)

    def test_root_and_integer_minimum(self):
        n=required_n(.01,.001,.8,.025)
        self.assertGreaterEqual(scenario_power(n,n,.01,.001),.8)
        self.assertLess(scenario_power(n-1,n-1,.01,.001),.8)
        self.assertAlmostEqual(scenario_power(21307,21306,.01,mde(21307,21306,.01,.8,.025)),.8,places=9)

    def test_scenario_power_binomial_check(self):
        # Synthetic scenarios, not observed treatment effects or an A/A experiment.
        rng=np.random.default_rng(20261017)
        nt,nc=21307,21306
        for delta in [0,.001,.003]:
            a=rng.binomial(nt,.01+delta,50000)
            b=rng.binomial(nc,.01,50000)
            pool=(a+b)/(nt+nc)
            variance=pool*(1-pool)*(1/nt+1/nc)*(nt+nc)/(nt+nc-1)
            reject=np.abs(a/nt-b/nc)>stats.norm.isf(.025/2)*np.sqrt(variance)
            self.assertLess(abs(reject.mean()-scenario_power(nt,nc,.01,delta)),.012)

    def test_alias_invalid_values_and_missing_not_zero(self):
        row={'recency':2,'history_segment':'1) $0 - $100','history':29.99,'mens':1,'womens':0,
             'zip_code':'Surburban','newbie':0,'channel':'Web','segment':'No E-Mail',
             'visit':0,'conversion':np.nan,'spend':0}
        f,m=quality_checks(pd.DataFrame([row]),['No E-Mail'],['Suburban'])
        self.assertEqual(f.region.iloc[0],'Suburban')
        self.assertEqual(f.zip_code.iloc[0],'Surburban')
        c=count_table(f,['segment']).iloc[0]
        self.assertEqual(c.missing_purchase,1)
        self.assertEqual(c.nonpurchases,0)
        row.update(conversion=1,spend=-1)
        _,m=quality_checks(pd.DataFrame([row]),['No E-Mail'],['Suburban'])
        self.assertTrue(m['conversion1_spend_not_positive'].iloc[0])
        self.assertTrue(m['conversion1_visit0'].iloc[0])
        self.assertTrue(m['spend:negative'].iloc[0])

    def test_independent_csv_census(self):
        # Standard-library reader independently checks pandas counts and exact duplicate accounting.
        with (ROOT/'data/raw/hillstrom.csv').open(newline='',encoding='utf-8') as file:
            rows=list(csv.DictReader(file))
        report=json.loads((ROOT/'reports/audit_results.json').read_text(encoding='utf-8'))
        groups=Counter(r['segment'] for r in rows)
        recorded=pd.read_csv(ROOT/'reports/group_counts.csv').set_index('segment')
        self.assertEqual(groups,Counter(recorded.n.to_dict()))
        self.assertEqual(len(rows),report['n'])
        patterns=Counter(tuple(r.values()) for r in rows)
        self.assertEqual(sum(n for n in patterns.values() if n>1),report['identical_rows_all_members'])
        self.assertEqual(sum(n-1 for n in patterns.values() if n>1),report['identical_rows_excess'])
        self.assertEqual(sum(v.strip()=='' for r in rows for v in r.values()),report['missing_cells'])
        region=pd.read_csv(ROOT/'reports/region_group_counts.csv')
        self.assertEqual(region.n.sum(),len(rows))
        self.assertEqual(region.purchases.sum(),sum(r['conversion']=='1' for r in rows))
        self.assertFalse(report['effects_computed'])
        self.assertEqual(report['rows_dropped'],0)

if __name__=='__main__':
    unittest.main()
