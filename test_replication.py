import math, unittest
import numpy as np
from macro_accounts import profit_rates,iip_reconciliation,ageing_adjusted,fisim_fixed_ratio
from io_accounts import finance_content
class Checks(unittest.TestCase):
 def test_profit(self):
  r=profit_rates();self.assertAlmostEqual(r['2007']['current_pct'],12.396223,places=4);self.assertAlmostEqual(r['2019']['wedge_pct_of_historical'],44.2615,places=3)
 def test_iip(self):
  r=iip_reconciliation();self.assertTrue(r['reconciles_stocks']);self.assertAlmostEqual(r['residual_pct_of_change'],72.7905,places=4)
 def test_age(self):
  x=ageing_adjusted();self.assertAlmostEqual(x[2004]['coverage_05_pct'],88.6712,places=3)
 def test_fixed_baseline(self):
  x=fisim_fixed_ratio()['holding_fin_gos_to_gdp_constant'];self.assertAlmostEqual(x['difference_hkd_mn'],197600.0902,places=3)
 def test_io_synthetic(self):
  r=finance_content(np.zeros((2,2)),[100,100],[30,70],0,0.4)
  self.assertAlmostEqual(r['direct_pct'],12);self.assertAlmostEqual(r['embedded_pct'],0)
if __name__=='__main__':unittest.main()
