"""Macro account reconstructions; source extracts are snapshots, not raw PWT."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
D=ROOT/'data/uploads'
def load(name): return json.loads((D/name).read_text(encoding='utf8'))

def profit_rates():
    """Net surplus / K, and sector GOS/K. PWT-derived stocks are supplied extracts."""
    rows=load('unified_round1_data.json'); out={}
    for year,x in rows.items():
        net=x['netOS']; kh=x['Khc']; kc=x['Kcc']
        out[year]={'historical_pct':100*net/kh,'current_pct':100*net/kc,
            'wedge_pct_of_historical':100*(1-kh/kc),
            'sector_gross_contributions_pct':{k:100*x[k]/kh for k in ('nf','fc','own','other')},
            'cfc_pct':100*(x['tot']-net)/kh}
    return out

def iip_reconciliation(start_year=2004,end_year=2024):
    """Stock dates are year ends; flow series run from start+1 through end.
    CA residual includes valuation, other changes, capital account and errors;
    it is not a pure observed valuation measure. Input is an older derived file.
    """
    data=load('nfa_decomp.json')['nfa_decomp']
    changes=sum(data[str(y)]['dNFA'] for y in range(start_year+1,end_year+1))
    ca=sum(data[str(y)]['CA'] for y in range(start_year+1,end_year+1))
    stockdiff=data[str(end_year)]['NFA']-data[str(start_year)]['NFA']
    return {'stock_change_hkd_mn':stockdiff,'sum_annual_changes_hkd_mn':changes,
            'current_account_hkd_mn':ca,'residual_hkd_mn':changes-ca,
            'residual_pct_of_change':100*(changes-ca)/changes,
            'reconciles_stocks':abs(stockdiff-changes)<1e-6,
            'status':'older processed input, not a fresh IIP validation; portfolio valuation unavailable'}

def ageing_adjusted():
    """W/[PCE*(1 - elderly_share * assumed elderly/overall consumption)]."""
    pop=load('pop_11001001.json')['dataSet']; accounts=load('five_step_timeseries.json'); s=accounts['step5']; out={}
    for year in (2004,2024):
        subset=[r for r in pop if r['period']==f'{year}06' and r['SEX']=='' and r['sv']=='POP' and r['svDesc']=="Number ('000)"]
        total=next(r['figure'] for r in subset if r['AGE']=='')
        elderly=sum(r['figure'] for r in subset if r['AGE'] in ['65-69','70-74','75-79','80-84','85_and_over'])
        fraction=elderly/total; wage=s['CE'][str(year)]; pce=accounts['step1'][str(year)]['PCE']*s['GDP'][str(year)]
        out[year]={'elderly_fraction':fraction,'W':wage,'PCE':pce,
          'coverage_05_pct':100*wage/(pce*(1-.5*fraction)),
          'coverage_08_pct':100*wage/(pce*(1-.8*fraction))}
    return out

def fisim_fixed_ratio():
    """Two explicit baselines; not an estimate or upper bound on FISIM itself."""
    x=load('heavy_round_data.json'); f19=x['fc_gos']['2019']; f24=x['fc_gos']['2024']; g19=x['gdp']['2019']; g24=x['gdp']['2024']; o19=x['fc_go']['2019']; o24=x['fc_go']['2024']
    a=f24-f19/g19*g24;b=f24-f19/o19*o24
    return {'holding_fin_gos_to_gdp_constant':{'difference_hkd_mn':a,'difference_pct_2024_gdp':100*a/g24},
            'holding_fin_gos_to_fin_output_constant':{'difference_hkd_mn':b,'difference_pct_2024_gdp':100*b/g24},
            'status':'Neither baseline reproduces manuscript HK$185bn; not isolated FISIM or causal windfall.'}

if __name__=='__main__':
    print(json.dumps({'profit_rates':profit_rates(),'iip':iip_reconciliation(),'ageing':ageing_adjusted(),'fisim':fisim_fixed_ratio()},indent=2))
