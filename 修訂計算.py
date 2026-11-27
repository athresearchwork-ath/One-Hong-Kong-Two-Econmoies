#!/usr/bin/env python3
"""Recompute revised paper estimates from adjacent 修訂數據.json.
Run: python 修訂計算.py [data.json]. Requires numpy. Values are HK$mn except ADB (US$mn).
See source metadata and assumptions embedded in JSON and manuscript notes.
"""
import json, sys
from pathlib import Path
import numpy as np

def load(path):
    return json.loads(Path(path).read_text(encoding='utf8'))

def external(data, first, last):
    rows=[data['iip_annual'][str(y)] for y in range(first,last+1)]
    def s(key): return sum(r[key] for r in rows)
    niip=s('niip_change'); net_transactions=s('financial_account_net_transactions')
    port=s('portfolio_change'); port_transactions=s('portfolio_asset_transactions')
    return {'net_iip_change_hkd_mn':niip, 'financial_account_transactions_hkd_mn':net_transactions,
      'net_iip_nontransaction_and_reconciliation_hkd_mn':niip-net_transactions,
      'net_iip_residual_pct':100*(niip-net_transactions)/niip,
      'portfolio_change_hkd_mn':port,'portfolio_transactions_hkd_mn':port_transactions,
      'portfolio_residual_hkd_mn':port-port_transactions}

def fisim_scenario(data):
    a=data['a10_2019'];b=data['a10_2024']; baseline=a['gos']/a['output']*b['output']; difference=b['gos']-baseline
    return {'baseline_finance_gos_hkd_mn':baseline,'excess_gos_hkd_mn':difference,'excess_pct_gdp':100*difference/b['gdp'],'baseline_pct_gdp':100*baseline/b['gdp']}

def financial_content(data):
    results={};fin=27
    for year,t in data['ADB_HKG'].items():
        z=np.asarray(t['Z'],float);x=np.asarray(t['output'],float);h=np.asarray(t['household_local'],float)
        a=np.divide(z,x[np.newaxis,:],out=np.zeros_like(z),where=x[np.newaxis,:]!=0);L=np.linalg.inv(np.eye(len(x))-a)
        v=t['finance_value_added']/x[fin]; split=t['cs_fin_gos']/(t['cs_fin_gos']+t['cs_fin_ce']); g=v*split
        direct=100*g*h[fin]/t['household_total'];indirect=100*g*((L@h)[fin]-h[fin])/t['household_total']
        results[year]={'estimated_gos_coefficient':g,'direct_pct':direct,'indirect_pct':indirect,'total_pct':direct+indirect}
    return results

def capital_scenarios(data):
    """Independent historical-cost PIM; 2024 is a scenario, not official PWT."""
    a=['Struc','Mach','TraEq','Other'];p=data['PWT_HKG'];K=dict(p['1960']['Nc']);result={}
    for year in range(1961,2024):
        t=p[str(year)]
        for asset in a:
            nc=t['Nc'][asset]; delta=t['Dc'][asset]/nc if nc else 0
            K[asset]=(1-delta)*K[asset]+t['Ic'][asset]
        if str(year) in data['total_gos']:
            hc=sum(K.values());cc=sum(t['Nc'].values());depr=sum(t['Dc'].values());net=data['total_gos'][str(year)]-depr
            result[str(year)]={'hc':hc,'cc':cc,'historical_net_pct':100*net/hc,'current_net_pct':100*net/cc,'wedge_pct':100*(1-hc/cc),
              'sector_gross_pct':{k:100*v/hc for k,v in data['sector_gos'][str(year)].items()},'cfc_pct':100*depr/hc}
    t=p['2023']; i=data['gdfcf_2024'];mach=t['Ic']['Mach'];trans=t['Ic']['TraEq']
    invest={'Struc':i['structures']+i['ownership_transfer'],'Mach':i['equipment_ip']*mach/(mach+trans),'TraEq':i['equipment_ip']*trans/(mach+trans),'Other':0}
    cc=0;hc=0
    for asset in a:
        nc=t['Nc'][asset];delta=t['Dc'][asset]/nc if nc else 0
        hc+=K[asset]*(1-delta)+invest[asset];cc+=nc*(1-delta)+invest[asset]
    result['2024_scenario']={'hc':hc,'cc_assuming_no_revaluation':cc,'wedge_pct':100*(1-hc/cc),'note':'2023 depreciation rates and investment mix; 2024 asset prices fixed; not PWT official'}
    return result

def main():
    data=load(sys.argv[1] if len(sys.argv)>1 else Path(__file__).with_name('修訂數據.json'))
    out={'B3_2004_2024_flows':external(data,2004,2024),'portfolio_2005_2024_flows':external(data,2005,2024),'A10':fisim_scenario(data),'Table_X':financial_content(data),'PWT_PIM':capital_scenarios(data)}
    assert abs(out['B3_2004_2024_flows']['net_iip_change_hkd_mn']-12537487)<.01
    assert abs(out['portfolio_2005_2024_flows']['portfolio_residual_hkd_mn']-4466814)<.01
    assert abs(out['Table_X']['2024']['total_pct']-15.7974593)<1e-5
    assert abs(out['A10']['excess_gos_hkd_mn']-123390.2356)<.001
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
