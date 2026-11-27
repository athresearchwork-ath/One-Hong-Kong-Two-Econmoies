"""Exact Module 3 demeaned OLS, substituting C&SD volume and wage indices and
HKMA monthly 1M HIBOR averages. ESLS path remains assumed, NOT official.
This is exploratory, not a causal or fully verified demand-shock control.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
ROOT=Path(__file__).resolve().parent
q=json.loads((ROOT/'data/raw/esls_censtatd_220_19024_extract.json').read_text())
V=[118.7,117.2,115.0,115.8,117.8,111.8,111.2,114.5,115.7,111.5,109.7,114.3,115.9,111.1]
# Assumed path copied from user model, NOT audited employment observations.
ESLS=[0,0,0,.1,.5,2.2,5.8,9.6,12.8,15,16.62,17.5,18,18.2]
rows=json.loads((ROOT/'data/raw/HKMA_1m_hibor.json').read_text())['result']['records']
monthly={r['end_of_month']:r['1m_hibor_fixing'] for r in rows if r['1m_hibor_fixing'] is not None}
def qmean(year,quarter):
    vals=[monthly[f'{year}-{m:02d}'] for m in range(quarter*3-2,quarter*3+1)]
    return sum(vals)/3
quarters=q['quarters']; inds=[int(x[-1]) for x in quarters]
hibor=[]
for x in quarters:
 y=int(x[:4]);n=int(x[-1]);hibor.append(qmean(y if n>1 else y-1,n-1 if n>1 else 4))
df=pd.DataFrame({'Quarter':quarters,'q':inds,'Y':100*np.log(np.array(q['D56'])/np.array(q['D55'])), 'V':100*np.log(V),'H':hibor,'E':np.array(ESLS)/190*100})
for c in ['Y','V','H','E']:
 df[c+'_dm']=df[c]-df.groupby('q')[c].transform('mean')
 base=df.iloc[:4].set_index('q')[c];df[c+'_d23']=df[c]-df.q.map(base)
fit=sm.OLS(df.Y_dm,df[['V_dm','H_dm','E_dm']]).fit()
phase=df.Quarter.isin(['2024Q3','2024Q4','2025Q1','2025Q2','2025Q3'])
result={'actual_gap':float(df.loc[phase,'Y_d23'].mean()),'coefficient':fit.params.to_dict(),'terms':{c:float(fit.params[c+'_dm']*df.loc[phase,c+'_d23'].mean()) for c in ['V','H','E']}, 'status':'Official wage and volume extracts; monthly HIBOR quarterly simple means; ESLS trajectory and 190k denominator assumed. Descriptive model, no causal shares; HIBOR aggregation differs from original model.', 'volume_source':'https://www.censtatd.gov.hk/api/get.php?id=625-68001&lang=en&full_series=1'}
if __name__=='__main__':print(json.dumps(result,indent=2))
