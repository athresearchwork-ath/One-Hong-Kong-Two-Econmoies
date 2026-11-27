#!/usr/bin/env python3
"""Proofread paper: formulas and available reproducible calculations.
All ratios are explicitly named fractions, percent or percentage points.
Source data not supplied remain unavailable; see README for coverage.
"""
from __future__ import annotations

def capitalised_price(payment, yield_percent):
    if yield_percent <= 0: raise ValueError('yield must be positive')
    return payment/(yield_percent/100)

def investment_rate_percent(investment, surplus):
    if surplus<=0:raise ValueError('positive surplus required')
    return 100*investment/surplus

def interest_scenario(rate_percent, loan_stock):
    return rate_percent/100*loan_stock

def surplus_ratio_percent(gross_surplus, gross_output):
    if gross_output<=0:raise ValueError('positive output required')
    return 100*gross_surplus/gross_output

def wage_share_consumption_percent(wages, consumption):
    if consumption<=0:raise ValueError('positive consumption required')
    return 100*wages/consumption

def kalecki_residual(gross_surplus,gfcf,net_exports,government_consumption):
    return gross_surplus-gfcf-net_exports-government_consumption

def kalecki_residual_expenditure(private_consumption,wages,net_taxes,inventory_change,statistical_discrepancy):
    """R = PCE - W - NIT + ΔInv - SD; SD follows paper sign convention."""
    return private_consumption-wages-net_taxes+inventory_change-statistical_discrepancy

def pim_series(investment_by_year, depreciation, previous_stock):
    """K_t=(1−δ)K_(t−1)+I_t; nominal inputs yield nominal model, not real stock."""
    if not 0<depreciation<1:raise ValueError('depreciation must be in (0,1)')
    years=sorted(investment_by_year)
    if any(b-a != 1 for a,b in zip(years,years[1:])):raise ValueError('years must be consecutive')
    out={};stock=previous_stock
    for y in years:
        stock=(1-depreciation)*stock+investment_by_year[y];out[y]=stock
    return out

def price_rent_yield_decomposition(price_start,price_end,rent_start,rent_end):
    """P=Q/y; multiplicative total = rent factor × yield-compression factor."""
    if min(price_start,price_end,rent_start,rent_end)<=0:raise ValueError('positive values required')
    total=price_end/price_start;rent=rent_end/rent_start
    return {'price_factor':total,'rent_factor':rent,'yield_compression_factor':total/rent}

# ================= PROOFREAD-EDITION ADDITIONS =================
# File-based workflows write into output/; uploaded inputs are read-only.
import argparse
import math
import os
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "data"
UPLOADS = Path(os.environ.get("TWO_ECONOMIES_UPLOADS", ROOT / "uploads"))
RAW = ROOT / "raw"
PROCESSED = ROOT / "proceed"
OUT = ROOT / "output"

def read_json(path: Path):
    """Read JSON as UTF-8 regardless of the operating-system locale."""
    return json.loads(Path(path).read_text(encoding="utf-8"))

def pct_change(start, end):
    if not start: raise ValueError("Zero base")
    return (end / start - 1.0) * 100.0

def realisation_components(gfcf, net_exports, gov_consumption, residual):
    """Π = GFCF + NX + G + R; all four inputs in the same currency."""
    return gfcf + net_exports + gov_consumption + residual

def profit_rate_account(gross_surpluses, consumption_fixed_capital, capital):
    """Sector GOS/common K contributions and aggregate net (not sector returns)."""
    if capital <= 0: raise ValueError('capital must be positive')
    contributions={name: value/capital*100 for name,value in gross_surpluses.items()}
    return {'contributions_pct':contributions,'depreciation_pct':consumption_fixed_capital/capital*100,
            'net_rate_pct':(sum(gross_surpluses.values())-consumption_fixed_capital)/capital*100}

def funds_account(I, gross_surplus, interest_scenario, delta_loan):
    """I = Π - Q + B - U, B = ΔL; U is balancing other uses, not observed profit."""
    U=gross_surplus-interest_scenario+delta_loan-I
    return {'U':U,'I_over_Pi':I/gross_surplus,'Q_over_Pi':interest_scenario/gross_surplus,
            'B_over_Pi':delta_loan/gross_surplus,'U_over_Pi':U/gross_surplus}

def proofread_log_decomposition(g0,q0,b0,g1,q1,b1, order='interest_first'):
    """B15 ordered decomposition. Fractions not percent inputs; contributions sum to 100%."""
    if min(g0,g1,1-q0,1-q1,1+b0,1+b1,1-q0+b0,1-q1+b1)<=0:
        raise ValueError('logs require positive arguments')
    d=math.log(g1/g0); h=math.log((1-q1+b1)/(1-q0+b0))
    if abs(d)<1e-12: raise ValueError('zero change, shares undefined')
    if order=='interest_first':
        interest=math.log((1-q1)/(1-q0)); borrowing=h-interest
    elif order=='borrowing_first':
        borrowing=math.log((1+b1)/(1+b0)); interest=h-borrowing
    else: raise ValueError('unknown order')
    return {'interest_pct':100*interest/d,'borrowing_pct':100*borrowing/d,
            'conversion_pct':100*(d-h)/d,'change_log_g':d}

def symmetric_shift_share(groups):
    """Input list [(investment0, surplus0, investment1, surplus1), ...]."""
    s0=sum(r[1] for r in groups); s1=sum(r[3] for r in groups)
    if not s0 or not s1 or any(r[1]==0 or r[3]==0 for r in groups): raise ValueError('zero surplus')
    within=sum(((a[2]/a[3])-(a[0]/a[1]))*((a[1]/s0)+(a[3]/s1))/2 for a in groups)
    between=sum(((a[3]/s1)-(a[1]/s0))*((a[0]/a[1])+(a[2]/a[3]))/2 for a in groups)
    return {'ratio0_pct':100*sum(a[0] for a in groups)/s0,'ratio1_pct':100*sum(a[2] for a in groups)/s1,
            'within_pp':100*within,'composition_pp':100*between}

def leontief_components(A, y, financial_row):
    """Leontief inverse from supplied coefficients and final demand; requires numpy.
    No built-in claim that the data reproduce ADB tables or the household share.
    """
    import numpy as np
    A=np.asarray(A,dtype=float);y=np.asarray(y,dtype=float);L=np.linalg.inv(np.eye(len(A))-A)
    output=L@y
    return {'inverse':L, 'output':output, 'financial_output':output[financial_row]}

def annual_window_means(rows, years, rate_key):
    rr=[rows[str(y)] for y in years]
    return tuple(statistics.mean(x[k] for x in rr) for k in ('g','b'))+(statistics.mean(x['q'][rate_key] for x in rr),)

def b15_from_processed():
    """Reproduce B15 window shares from retained, processed linked annual series."""
    rows=read_json(PROCESSED/'linked_loan_investment_results.json')['rows']
    windows=[range(2012,2015),range(2017,2020),range(2022,2025)]; result={}
    for rate in ('hib','mid','prime'):
        means=[annual_window_means(rows,w,rate) for w in windows]
        result[rate]=[]
        for (g0,b0,q0),(g1,b1,q1) in zip(means,means[1:]):
            result[rate].append({o:proofread_log_decomposition(g0,q0,b0,g1,q1,b1,o)
                                 for o in ('interest_first','borrowing_first')})
    return result

def rebuild_b15_from_uploaded(uploads_dir: Path = UPLOADS, raw_dir: Path = RAW):
    """Rebuild B15 using the 2018 overlap; loan use and industries differ."""
    uploads_dir, raw_dir = Path(uploads_dir), Path(raw_dir)
    old = {x["end_of_month"]: x for x in read_json(uploads_dir / "c03_old.json")["result"]["records"]}
    new = {x["end_of_month"]: x for x in read_json(uploads_dir / "c03_new.json")["result"]["records"]}

    def loan(x):
        return x["loan_inhk"] - sum(x[k] for k in ("misc_fin", "misc_stockbrok", "misc_prof", "bcpi"))

    factor = loan(new["2018-12"]) / loan(old["2018-12"])
    inv = read_json(uploads_dir / "revise_compute_2.json")
    hib = read_json(uploads_dir / "hibor3m_2004_2024.json")["annual_avg"]
    sec_by_year = defaultdict(dict)
    for z in read_json(uploads_dir / "iot34201_new.json")["dataSet"]:
        if z["sv"] == "CURGOS":
            sec_by_year[z["period"]][z["ACTIVITY"]] = z["figure"]
    prime_by_year = defaultdict(list)
    for x in read_json(raw_dir / "HKMA_period_average_rates.json")["result"]["records"]:
        prime_by_year[x["end_of_month"][:4]].append(x["best_lending_rate"])

    rows = {}
    for year in range(2004, 2025):
        date, prev_date = str(year), str(year - 1)
        db, scale = (old, factor) if year <= 2018 else (new, 1.0)
        curr_raw = loan(db[f"{date}-12"])
        prev_raw = loan(db[f"{prev_date}-12"])
        L, B = curr_raw * scale, (curr_raw - prev_raw) * scale
        sec = sec_by_year[date]
        pi = sec[""] - sum(sec[k] for k in ("SECT_F", "SECT_K", "SECT_LMN", "SECT_OWN"))
        prime_rate = statistics.mean(prime_by_year[date])
        rates = {"hib": hib[date], "mid": hib[date] + 1.5, "prime": prime_rate}
        priv_m = inv[date]["PRIVM"]
        rows[date] = {"L": L, "B": B, "pi": pi, "I": priv_m,
                      "g": priv_m / pi, "b": B / pi,
                      "q": {k: L / pi * v / 100.0 for k, v in rates.items()}}
    return {"factor": factor, "rows": rows}

def transport_shift_from_processed(exclude_air=False):
    groups=defaultdict(lambda:[[0.0,0.0],[0.0,0.0]])
    rows = read_json(PROCESSED/'asea'/'transport_full.json')
    for r in rows:
        name=r['industry']; yr=int(r['year'])
        if name=='總計' or (exclude_air and name=='航空及輔助'):continue
        if yr not in (*range(2012,2015),*range(2017,2020)): continue
        slot=0 if yr<=2014 else 1
        groups[name][slot][0]+=float(r['fixed_net_HKD_m']);groups[name][slot][1]+=float(r['gross_surplus_HKD_m'])
    return symmetric_shift_share([(v[0][0],v[0][1],v[1][0],v[1][1]) for v in groups.values()])

def proofread_checks(uploads_dir: Path = UPLOADS):
    """Replicate key numeric checks; results remain descriptive, not effects."""
    b15=b15_from_processed(); rebuilt=rebuild_b15_from_uploaded(uploads_dir=uploads_dir)
    saved=read_json(PROCESSED/'linked_loan_investment_results.json')
    assert abs(rebuilt['factor']-saved['factor'])<1e-10
    for y in ('2014','2019','2024'):
        for key in ('L','B','pi','I','g','b'):
            assert abs(rebuilt['rows'][y][key]-saved['rows'][y][key]) < 1e-7,(y,key)
    assert round(b15['hib'][0]['interest_first']['interest_pct'],1)==11.4
    assert round(b15['prime'][1]['interest_first']['interest_pct'],1)==3.8
    t1=transport_shift_from_processed(False);t2=transport_shift_from_processed(True)
    assert abs(t1['ratio0_pct']-72.09)<0.03 and abs(t2['composition_pp']-(-3.66))<0.03
    m={int(x['year']):x for x in read_json(OUT/'mortgage_stock_to_wages.json')}
    assert round(float(m[2022]['end_stock_to_comp_pct']),1)==127.2
    return {'real_private_meip_change_2014_2016_pct':pct_change(249007,206320),
            'real_private_meip_change_2014_2024_pct':pct_change(249007,133925),
            'mortgage_2022_stock_to_wages_pct':float(m[2022]['end_stock_to_comp_pct']),
            'b15_2018_link_factor':rebuilt['factor'],'b15_window_decomposition':b15,
            'transport_all':t1,'transport_ex_air':t2}

def rebuild_mortgage():
    """Rebuild mortgage scenario: monthly and annual series, then year-end L/W.

    2009–16 HIBOR stock weights are assumed, not observed; post-2016 stock
    composition is modelled from draws and implied outflow. Rates are scenarios.
    """
    import calendar
    read = read_json
    def keyed(n):return {x['end_of_month']:x for x in read(RAW/n)['result']['records']}
    loans=keyed('HKMA_residential_mortgage_survey.json')
    old=read(PROCESSED/'HKMA_T0307_old_sheet_values.json')['cell_values'];year=None
    for row in old:
        yearcell,mon,_,value=row[:4]
        if isinstance(yearcell,int) and 1990<=yearcell<=2030:year=yearcell
        if year and mon in list(calendar.month_abbr)[1:] and isinstance(value,(int,float)):
            date=f'{year}-{list(calendar.month_abbr).index(mon):02}'
            loans.setdefault(date,{'outstanding_loans_amt':value})
    H=keyed('HKMA_1m_hibor.json');P=keyed('HKMA_period_average_rates.json')
    W=read(PROCESSED/'wage_share_total_official.json'); states={.25:.25,.50:.50,.75:.75}; rows=[]
    for y in range(2004,2025):
        for m in range(1,13):
            date=f'{y}-{m:02}';prev=f'{y-1}-12' if m==1 else f'{y}-{m-1:02}'
            rec=loans[date];start=loans[prev]['outstanding_loans_amt'];end=rec['outstanding_loans_amt'];avg=(start+end)/2
            hib=H[date]['1m_hibor_fixing'];prime=P[date]['best_lending_rate'];hr=min(hib+1.3,prime-2.5);pr=prime-2.5
            weights={};share=None;draw=None;outflow=None
            if y<=2016:
                for seed in states:weights[seed]=0 if y<=2008 else seed*((y-2009)*12+m-.5)/96
            else:
                draw=rec['new_loans_drawn_amt'];outflow=start+draw-end;share=rec['ir_new_loans_approved_hibor']
                if not 0<=outflow<=start or not 0<=share<=1:raise ValueError(date)
                for seed,previous in list(states.items()):
                    closing=(previous*(start-outflow)+draw*share)/end
                    weights[seed]=(previous+closing)/2;states[seed]=closing
            rates={seed:(1-weight)*pr+weight*hr for seed,weight in weights.items()}
            rows.append(dict(month=date,opening=start,closing=end,avg_stock=avg,hibor1m_pct=hib,hsbc_prime_pct=prime,hibor_contract_pct=hr,prime_contract_pct=pr,new_approved_h_share=share,drawn=draw,implied_outflow=outflow,estimated_h_stock_weight=weights[.50],hybrid_rate_pct=rates[.50],hybrid_interest_HK_m=avg*rates[.50]/1200,low_weight_interest_HK_m=avg*rates[.25]/1200,high_weight_interest_HK_m=avg*rates[.75]/1200,prior_all_h_interest_HK_m=avg*hr/1200,wage_HK_m=W[str(y)]['comp']))
    annual=[]; ratios=[]
    for y in range(2004,2025):
        rr=[x for x in rows if x['month'].startswith(str(y))];Wage=rr[0]['wage_HK_m'];end=rr[-1]['closing']
        avg=sum(x['avg_stock'] for x in rr)/12; intr=sum(x['hybrid_interest_HK_m'] for x in rr)
        high=sum(x['avg_stock']*(x['estimated_h_stock_weight']*min(x['hibor1m_pct']+1.3,x['hsbc_prime_pct']-1.75)+(1-x['estimated_h_stock_weight'])*(x['hsbc_prime_pct']-1.75))/1200 for x in rr)
        annual.append(dict(year=y,avg_stock=avg,rate=intr/avg*100,interest=intr,wage=Wage,q=intr/Wage*100,weight=sum(x['estimated_h_stock_weight'] for x in rr)/12,q_25=sum(x['low_weight_interest_HK_m'] for x in rr)/Wage*100,q_75=sum(x['high_weight_interest_HK_m'] for x in rr)/Wage*100))
        ratios.append(dict(year=y,end_stock_HK_m=end,annual_compensation_HK_m=Wage,end_stock_to_comp_pct=end/Wage*100,avg_stock_HK_m=avg,avg_stock_to_comp_pct=avg/Wage*100,model_q=intr/Wage*100,high_cap_q=high/Wage*100,model_rate=intr/avg*100,high_cap_rate=high/avg*100))
    for name,data in [('mortgage_monthly',rows),('mortgage_annual',annual),('mortgage_stock_to_wages',ratios)]:
        (OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return ratios

def quarter_rate_average(monthly_values):
    """Unweighted arithmetic mean of three monthly average rates."""
    if len(monthly_values)!=3: raise ValueError("Three months required")
    return statistics.mean(monthly_values)

def loan_sensitivity_percentage_points(loan_stock, annual_income, rate_increase_pp=1):
    """Full-stock mechanical exposure, not actual debt service."""
    if annual_income<=0: raise ValueError("income must be positive")
    return rate_increase_pp*loan_stock/annual_income

def real_investment_ratio(investment_chained, nominal_surplus, nominal_gdp, chained_gdp):
    """Appendix B15 purchasing-power sensitivity, not additive real flows."""
    if nominal_surplus<=0 or nominal_gdp<=0 or chained_gdp<=0: raise ValueError("positive denominators required")
    return investment_chained/(nominal_surplus/(nominal_gdp/chained_gdp))

def output_price_components(base_output, nominal_parts0, nominal_parts1, price_index_increase):
    """Unit-cost contribution = 100 × Δ nominal component / base-year output.
    Requires components already converted to constant-output units; no implicit deflation.
    Returns accounting shares, not causal effects.
    """
    if base_output<=0 or price_index_increase==0: raise ValueError("positive base and nonzero price change required")
    return {k:{"points":100*(nominal_parts1[k]-nominal_parts0[k])/base_output,
               "share_of_price_rise_pct":100*(100*(nominal_parts1[k]-nominal_parts0[k])/base_output)/price_index_increase}
            for k in nominal_parts0}

def ordinary_ar1_by_industry(pairs):
    """Pooled AR(1) diagnostic; not a replication of Appendix B1."""
    p = list(pairs)
    if len(p) < 2:
        raise ValueError("at least two observations required")
    x, y = zip(*p)
    if len(set(x)) == 1:
        raise ValueError("no variation in lagged series")
    slope, intercept = statistics.linear_regression(x, y)
    return {"intercept": intercept, "ar1": slope, "annual_closure": 1.0 - slope, "n": len(p)}

def corr_log_changes(series_x, series_y, years, lead=0):
    """Correlation of Δln x_t with Δln y_(t+lead), matched annual observations."""
    pairs=[(math.log(series_x[t]/series_x[t-1]),math.log(series_y[t+lead]/series_y[t+lead-1]))
       for t in years if all(k in series_x for k in (t,t-1)) and all(k in series_y for k in (t+lead,t+lead-1))]
    return {"correlation":statistics.correlation(*zip(*pairs)),"n":len(pairs),"lead":lead}



def main():
    parser = argparse.ArgumentParser(description="Proofread formulas and available data checks")
    parser.add_argument("--uploads", type=Path, default=UPLOADS, help="directory holding uploaded JSON files")
    parser.add_argument("--mortgage", action="store_true", help="rebuild monthly mortgage scenario before checking")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.mortgage or not (OUT / "mortgage_stock_to_wages.json").exists():
        ratios = rebuild_mortgage()
        if round(next(x["end_stock_to_comp_pct"] for x in ratios if x["year"] == 2022), 1) != 127.2:
            raise ValueError("2022 mortgage ratio check failed")
    checks = proofread_checks(uploads_dir=args.uploads)
    (OUT / "proofread_checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASS: B15 linked loan decomposition; private MEIP; 2022 mortgage; transport shift-share")

def esls_rolling_placebo(raw_path, restore_2019q4=False):
    """Reproduce user rolling-window model; optionally restore official 2019Q4.

    Historical series transcribed from user; source checked only in part. Returned
    coefficients and rank fractions are descriptive, not exact randomization p-values.
    """
    import numpy as np
    import pandas as pd
    import statsmodels.formula.api as smf
    z = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    d = pd.DataFrame({"Quarter": z["quarter"], "Hotel": z["D55"], "FB": z["D56"]})
    if restore_2019q4:
        d.loc[d.Quarter == "2019Q4", ["Hotel", "FB"]] = [98.4, 111.9]
    d["Qtr"] = d.Quarter.str[-1].astype(int)
    d["Y_diff"] = 100 * np.log(d.FB / d.Hotel)
    ix = {q:i for i,q in enumerate(d.Quarter)}
    records = []
    for i in list(range(ix["2017Q1"], ix["2023Q1"] + 1)) + [ix["2024Q3"]]:
        if pd.isna(d.loc[i,"Y_diff"]):
            continue
        win = d.iloc[i-6:i+5].dropna(subset=["Y_diff"]).copy()
        win["Pipeline"] = win.index.isin([i-2,i-1]).astype(int)
        win["Post_5Q"] = win.index.isin(range(i,i+5)).astype(int)
        fit = smf.ols("Y_diff ~ C(Qtr) + Pipeline + Post_5Q", data=win).fit(cov_type="HC1")
        records.append({"onset":d.loc[i,"Quarter"], "n":len(win),
          "beta":float(fit.params["Post_5Q"]), "se":float(fit.bse["Post_5Q"]),
          "t":float(fit.tvalues["Post_5Q"]), "p":float(fit.pvalues["Post_5Q"])})
    return records

def aehs_annual_growth_check(raw_path):
    """Reproduce cumulative growth script and unequal-period sensitivity; descriptive only."""
    z = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    years = z["years"]; names = z["industries"]; treated = names.index("Food_beverage")
    all_controls = [i for i in range(len(names)) if i != treated]
    low = [names.index(i) for i in ["Retail", "Estate_security_cleaning", "Miscellaneous"]]
    def growth(a,b):
        return [100 * math.log(y/x) for x,y in zip(years[str(a)], years[str(b)])]
    pre,post,alt = growth(2020,2023),growth(2023,2025),growth(2022,2023)
    def mean(v,inds): return sum(v[i] for i in inds)/len(inds)
    def result(pre_values,controls,scale=1.0):
        gap = (post[treated]-mean(post,controls))-scale*(pre_values[treated]-mean(pre_values,controls))
        cf = years["2023"][treated]*math.exp((post[treated]-gap)/100)
        return {"growth_gap_log_points":gap,"counterfactual_hkd":cf,"difference_hkd":cf-years["2025"][treated]}
    return {"user_all":result(pre,all_controls), "user_low_wage":result(pre,low),
            "user_2022_pre":result(alt,all_controls), "annualized_trend_two_year":result(pre,all_controls,2/3),
            "simple_two_year_level_did":post[treated]-mean(post,all_controls),
            "pre_treated":pre[treated],"pre_controls":mean(pre,all_controls),
            "post_treated":post[treated],"post_controls":mean(post,all_controls),
            "warning":"descriptive, rounded published medians; no SE or causal identification; not SDiD"}

def aehs_user_sdid(raw_path, treated, donors, pre_years=(2020,2021,2022,2023), post_years=(2024,2025)):
    """User-supplied SDiD-style weights and 2025/average contrasts; not causal validation."""
    import numpy as np
    import pandas as pd
    from scipy.optimize import minimize
    z = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    d = pd.DataFrame({int(k):v for k,v in z["years"].items()},index=z["industries"])
    y = 100 * np.log(d)
    a = y.loc[treated,list(pre_years)].values; b = y.loc[treated,list(post_years)].values
    X = y.loc[donors,list(pre_years)].values; Z = y.loc[donors,list(post_years)].values
    n,k = X.shape; sigma = np.std(np.diff(X,axis=1),ddof=1)
    zu = len(post_years)**0.25 * sigma; zt = 1e-6*sigma
    u = minimize(lambda p: np.sum((p[0]+p[1:]@X-a)**2)+zu**2*k*np.sum(p[1:]**2),
        np.r_[0,np.ones(n)/n], method="SLSQP", bounds=[(None,None)]+[(0,1)]*n,
        constraints={"type":"eq","fun":lambda p: np.sum(p[1:])-1},options={"ftol":1e-12,"maxiter":2000})
    t = minimize(lambda p: np.sum((p[0]+X@p[1:]-Z.mean(axis=1))**2)+zt**2*n*np.sum(p[1:]**2),
        np.r_[0,np.ones(k)/k], method="SLSQP", bounds=[(None,None)]+[(0,1)]*k,
        constraints={"type":"eq","fun":lambda p: np.sum(p[1:])-1},options={"ftol":1e-12,"maxiter":2000})
    if not u.success or not t.success: raise RuntimeError(f"SDiD optimisation failed: {u.message}; {t.message}")
    omega, lam = u.x[1:],t.x[1:]; base=lam@a-omega@(X@lam)
    return {"contrast_last_post":float(b[-1]-omega@Z[:,-1]-base),
            "contrast_mean_post":float(b.mean()-omega@Z.mean(axis=1)-base),
            "unit_weights":dict(zip(donors,omega.tolist())),"time_weights":dict(zip(pre_years,lam.tolist()))}

def esls_quarterly_phase_check(raw_path):
    """User two-industry three-phase formula using official wage indices (HC1)."""
    import numpy as np
    import pandas as pd
    import statsmodels.formula.api as smf
    z = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    qs = z["quarters"]; n=len(qs)
    d = pd.DataFrame({"Quarter":qs*2,"QtrOfYr":[int(q[-1]) for q in qs]*2,
        "Division":["FB"]*n+["Hotel"]*n,"Treated":[1]*n+[0]*n,
        "Index":z["D56"]+z["D55"]})
    d["lnY"]=100*np.log(d["Index"])
    for name,period in {"Pipeline":["2024Q1","2024Q2"],"Ramp":["2024Q3","2024Q4","2025Q1","2025Q2","2025Q3"],"Stab":["2025Q4","2026Q1","2026Q2"]}.items():
        d[name]=d.Quarter.isin(period).astype(int)
    fit=smf.ols("lnY ~ C(Division)*C(QtrOfYr) + C(Quarter) + Treated:Pipeline + Treated:Ramp + Treated:Stab",data=d).fit(cov_type="HC1")
    return {name:{"beta":float(fit.params["Treated:"+name]),"hc1_se":float(fit.bse["Treated:"+name]),"p_normal":float(fit.pvalues["Treated:"+name])} for name in ["Pipeline","Ramp","Stab"]}

if __name__=='__main__': main()
