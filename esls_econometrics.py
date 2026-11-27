"""Checked AEHS inputs and official short quarterly wage series.
Rolling history is a user-provided series only spot-checked, not fully verified.
"""
import json, math
from pathlib import Path
from proofread import aehs_user_sdid, esls_quarterly_phase_check, esls_rolling_placebo
ROOT=Path(__file__).resolve().parent
RAW=ROOT/'data/raw'
def main():
    ae=RAW/'aehs_fulltime_median_10industries_2020_2025.json'
    wage=RAW/'esls_censtatd_220_19024_extract.json'
    historic=RAW/'esls_placebo_user_series.json'
    names=json.loads(ae.read_text())['industries']; treated='Food_beverage'
    pools={'all9':[x for x in names if x!=treated],
      'excluded7':[x for x in names if x not in (treated,'Construction','Land_transport')],
      'white4':['Import_export','Information_communication','Finance_insurance','Professional_technical'],
      'low3':['Retail','Estate_security_cleaning','Miscellaneous']}
    annual={}
    for k,pool in pools.items():
        v=aehs_user_sdid(ae,treated,pool);v['hypothetical_2025_hkd']=17000*math.exp(-v['contrast_last_post']/100);annual[k]=v
    quarters=esls_quarterly_phase_check(wage)
    rolling=esls_rolling_placebo(historic,restore_2019q4=True)
    actual=next(x for x in rolling if x['onset']=='2024Q3')
    comp=[x for x in rolling if '2018Q1'<=x['onset']<='2023Q1']
    print(json.dumps({'annual':annual,'quarterly_phase':quarters,'rolling':{'actual':actual,'rank':1+sum(x['beta']<=actual['beta'] for x in comp),'comparisons':len(comp),'warning':'historical data only spot-checked; overlap and partly post-policy windows; descriptive rank'}},indent=2))
if __name__=='__main__':main()
