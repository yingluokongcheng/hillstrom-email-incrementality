from pathlib import Path
import sys, unittest, math
import numpy as np
from scipy import stats
from statsmodels.stats.proportion import test_proportions_2indep as reference_test
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from analyze import score_z,score_interval,bootstrap_means,benchmark_interpretation,binary_comparison
import pandas as pd

def corrected_polynomial_reference(x1,n1,x0,n0,delta):
    # Independent cubic formulation from the restricted likelihood, using n0 (not x0) in d^2.
    total=n1+n0; events=x1+x0
    roots=np.roots([total,(n1+2*n0)*delta-total-events,
                    (n0*delta-total-2*x0)*delta+events,x0*delta*(1-delta)])
    valid=[float(r.real) for r in roots if abs(r.imag)<1e-9 and max(0,-delta)<r.real<min(1,1-delta)]
    assert len(valid)==1
    p0=valid[0]; p1=p0+delta
    variance=(p1*(1-p1)/n1+p0*(1-p0)/n0)*total/(total-1)
    return (x1/n1-x0/n0-delta)/math.sqrt(variance)

class InferenceTests(unittest.TestCase):
    def test_independent_reference_statistics(self):
        # All synthetic count scenarios, fixed before real-data execution.
        for counts in [(120,10000,90,11000),(50,3000,40,2800),(330,5000,300,5100)]:
            for null in [0,.001,-.001,.004]:
                expected=corrected_polynomial_reference(*counts,null)
                self.assertAlmostEqual(score_z(*counts,delta=null),expected,places=7)
                if null==0:
                    library=reference_test(*counts,value=0,compare='diff',method='score',correction=True).statistic
                    self.assertAlmostEqual(score_z(*counts),library,places=12)

    def test_ci_endpoints_match_independent_score(self):
        for alpha in [.025,.05]:
            for counts in [(120,10000,90,11000),(50,3000,40,2800),(330,5000,300,5100)]:
                lo,hi=score_interval(*counts,alpha)
                for endpoint in [lo,hi]:
                    p=2*stats.norm.sf(abs(corrected_polynomial_reference(*counts,endpoint)))
                    self.assertAlmostEqual(p,alpha,places=7)

    def test_sign_reversal(self):
        a=score_interval(120,10000,90,11000,.025)
        b=score_interval(90,11000,120,10000,.025)
        np.testing.assert_allclose(a,[-b[1],-b[0]],rtol=0,atol=1e-10)
        self.assertAlmostEqual(score_z(120,10000,90,11000),-score_z(90,11000,120,10000))

    def test_bonferroni_shared_control_simulation(self):
        rng=np.random.default_rng(20261017); n=21000; p=.01; b=50000
        control=rng.binomial(n,p,b); a=rng.binomial(n,p,b); c=rng.binomial(n,p,b)
        def reject(t):
            q=(t+control)/(2*n)
            z=(t/n-control/n)/np.sqrt(q*(1-q)*(2/n)*(2*n)/(2*n-1))
            return np.abs(z)>stats.norm.isf(.025/2)
        family=float(np.mean(reject(a)|reject(c)))
        self.assertLess(family,.055)
        self.assertGreater(family,.025)

    def test_known_effect_coverage_via_score_inversion(self):
        rng=np.random.default_rng(20261018); b=5000; nt,nc=20000,22000; delta=.003
        a=rng.binomial(nt,.013,b); c=rng.binomial(nc,.01,b)
        covered=np.array([abs(score_z(int(x),nt,int(y),nc,delta))<=stats.norm.isf(.025/2) for x,y in zip(a,c)])
        self.assertLess(abs(covered.mean()-.975),.012)

    def test_bootstrap_zero_inclusion_and_sampling_variance(self):
        x=np.array([0.]*90+[10.]*10)
        means=bootstrap_means(x,20000,20261017)
        self.assertLess(abs(means.mean()-1),.015)
        self.assertLess(abs(means.var()-x.var()/len(x)),.003)
        np.testing.assert_array_equal(means,bootstrap_means(x,20000,20261017))

    def test_interpretation_keeps_small_positive_and_null_distinct(self):
        self.assertIn('无法确认',benchmark_interpretation(.0001,.002,.001))
        self.assertIn('至少达到',benchmark_interpretation(.002,.004,.001))
        self.assertIn('证据不足',benchmark_interpretation(-.001,.003,.001))
        self.assertIn('负向',benchmark_interpretation(-.003,-.001,.001))
        self.assertIn('不是证明',benchmark_interpretation(-.001,.0008,.001))

    def test_sparse_stops_inference_without_deleting_rows(self):
        frame=pd.DataFrame({'segment':['T']*100+['C']*100,'conversion':[1]*5+[0]*95+[1]*20+[0]*80})
        r=binary_comparison(frame,'T','C','conversion',.025,True)
        self.assertEqual(r['status'],'paused_sparse_cell')
        self.assertEqual(r['n_treatment'],100)
        self.assertNotIn('p_bonferroni',r)

if __name__=='__main__': unittest.main()
