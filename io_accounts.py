"""Financial value-added-content split using pre-extracted ADB I-O arrays.

Columns of Z are user industries, rows supplying industries; y is household
final demand by commodity; financial_v is sector financial GOS / gross output.
A is calculated as Z / output by column. All data must share the same price,
sector, geography, and year boundaries. Direct means the financial GOS content
of final demand for finance (including upstream input requirements); embedded
means content in non-financial household final-demand categories.
The 2024 matrix is NOT in this package; 2011 MRIO alone cannot establish 2024.
"""
import numpy as np

def finance_content(Z, output, household_demand, fin_index, financial_v):
    Z=np.asarray(Z,float); x=np.asarray(output,float); y=np.asarray(household_demand,float)
    if Z.shape != (len(x),len(x)) or y.shape != x.shape: raise ValueError('incompatible dimensions')
    if np.any(x<=0) or y.sum()<=0: raise ValueError('positive output and household demand required')
    A=Z/x[np.newaxis,:]; L=np.linalg.inv(np.eye(len(x))-A)
    per_product=financial_v * L[fin_index,:]*y
    direct=100*per_product[fin_index]/y.sum()
    embedded=100*(per_product.sum()-per_product[fin_index])/y.sum()
    return {'direct_pct':direct,'embedded_pct':embedded,'total_pct':direct+embedded}

def main():
    raise SystemExit('UNAVAILABLE: provide documented 2024 ADB I-O table extraction and verify exact manuscript definition; saved split is not raw replication.')
if __name__=='__main__':main()
