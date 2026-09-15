"""Forecast-error uncertainty assessment from finalized legitimate OOS residuals."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm

MAD_MULTIPLIER=1.4826
HORIZONS=(1,2,3,7,14,21,28)
SERVICE_TARGETS=(0.90,0.95,0.975,0.99)
EXPECTED_BLOCKS=("development_1_scale_seed","development_2","development_3","development_4","development_5","validation","anomaly_lockbox")

def load_final_oos_residuals(artifact_dir: str|Path="reports/anomalies/artifacts") -> pd.DataFrame:
    root=Path(artifact_dir)
    a=pd.read_csv(root/"oos_residual_blocks.csv")
    b=pd.read_csv(root/"lockbox_robust_scores_authentic.csv")
    required=["block","d","date","state_id","store_id","dept_id","actual_sales","expected_sales","residual"]
    if not set(required).issubset(a) or not set(required).issubset(b): raise ValueError("only provenance-complete OOS residual artifacts are accepted")
    frame=pd.concat([a[required],b[required]],ignore_index=True); frame["date"]=pd.to_datetime(frame.date)
    if len(frame)!=13720 or frame[["store_id","dept_id"]].drop_duplicates().shape[0]!=70 or frame.date.nunique()!=196:
        raise ValueError("final OOS corpus must contain 13,720 rows, 70 series, and 196 dates")
    if tuple(frame.block.drop_duplicates())!=EXPECTED_BLOCKS: raise ValueError("unexpected or non-OOS residual block provenance")
    if frame.duplicated(["date","store_id","dept_id"]).any() or not np.allclose(frame.actual_sales-frame.expected_sales,frame.residual):
        raise ValueError("invalid OOS residual corpus")
    return frame.sort_values(["date","store_id","dept_id"]).reset_index(drop=True)

def block_audit(frame: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for name,group in frame.groupby("block",sort=False):
        dates=pd.Series(sorted(group.date.unique()))
        if len(dates)>1 and not (dates.diff().dropna()==pd.Timedelta(days=1)).all(): raise ValueError(f"block {name} is not contiguous")
        rows.append({"block":name,"start_date":dates.iloc[0].date().isoformat(),"end_date":dates.iloc[-1].date().isoformat(),"dates":len(dates),"rows":len(group)})
    return pd.DataFrame(rows)

def series_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    def summarize(g):
        r=g.residual
        median=float(r.median()); mad=float(np.median(np.abs(r-median)))
        return pd.Series({"residual_count":len(r),"mean_residual":r.mean(),"median_residual":median,"residual_mad":mad,
            "robust_daily_scale":MAD_MULTIPLIER*mad,"residual_std":r.std(ddof=1),"positive_residual_share":(r>0).mean(),
            "skewness":r.skew(),"q90":r.quantile(.9),"q95":r.quantile(.95),"q975":r.quantile(.975),"q99":r.quantile(.99),
            "top_1pct_abs_share":r.abs().nlargest(max(1,int(np.ceil(len(r)*.01)))).sum()/r.abs().sum() if r.abs().sum() else 0})
    return frame.groupby(["store_id","dept_id"],sort=True).apply(summarize,include_groups=False).reset_index()

def cumulative_windows(frame: pd.DataFrame,horizon:int) -> pd.DataFrame:
    if horizon not in HORIZONS: raise ValueError("unsupported assessment horizon")
    rows=[]
    for (block,store,dept),g in frame.groupby(["block","store_id","dept_id"],sort=False):
        g=g.sort_values("date"); dates=g.date.to_numpy(); values=g.residual.to_numpy(float)
        for start in range(len(g)-horizon+1):
            window_dates=dates[start:start+horizon]
            if horizon>1 and not np.all(np.diff(window_dates).astype("timedelta64[D]")==np.timedelta64(1,"D")):
                raise ValueError("cumulative window crosses an OOS gap")
            rows.append({"block":block,"store_id":store,"dept_id":dept,"horizon":horizon,"window_end":window_dates[-1],"cumulative_residual":values[start:start+horizon].sum()})
    return pd.DataFrame(rows)

def cumulative_sample_counts(frame:pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for h in HORIZONS:
        windows=cumulative_windows(frame,h); counts=windows.groupby(["store_id","dept_id"]).size()
        rows.append({"horizon":h,"total_valid_windows":len(windows),"min_per_series":int(counts.min()),"median_per_series":float(counts.median()),"max_per_series":int(counts.max()),
                     "overlapping_windows_not_independent":h>1})
    return pd.DataFrame(rows)

def autocorrelation_summary(frame:pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for lag in (1,2,3,7):
        values=[]
        for _,series in frame.groupby(["store_id","dept_id"]):
            pairs=[]
            for _,block in series.groupby("block",sort=False):
                r=block.sort_values("date").residual.to_numpy(float)
                if len(r)>lag: pairs.extend(zip(r[:-lag],r[lag:]))
            pair=np.asarray(pairs,float)
            values.append(np.corrcoef(pair[:,0],pair[:,1])[0,1] if len(pair)>2 and pair[:,0].std()>0 and pair[:,1].std()>0 else np.nan)
        s=pd.Series(values).dropna()
        rows.append({"lag":lag,"series_count":len(s),"median":s.median(),"q25":s.quantile(.25),"q75":s.quantile(.75),"min":s.min(),"max":s.max()})
    return pd.DataFrame(rows)

def horizon_scale_ratios(frame:pd.DataFrame,distribution:pd.DataFrame) -> pd.DataFrame:
    daily=distribution.set_index(["store_id","dept_id"]).robust_daily_scale
    rows=[]
    for h in HORIZONS[1:]:
        w=cumulative_windows(frame,h)
        for key,g in w.groupby(["store_id","dept_id"]):
            med=np.median(g.cumulative_residual); observed=MAD_MULTIPLIER*np.median(np.abs(g.cumulative_residual-med)); denominator=daily.loc[key]*np.sqrt(h)
            rows.append({"horizon":h,"store_id":key[0],"dept_id":key[1],"scale_ratio":observed/denominator if denominator>0 else np.nan})
    detail=pd.DataFrame(rows)
    return detail.groupby("horizon").scale_ratio.agg(series_count="count",median="median",q25=lambda x:x.quantile(.25),q75=lambda x:x.quantile(.75),minimum="min",maximum="max").reset_index()

def empirical_safety_stock(windows:pd.DataFrame,service_target:float,min_tail_observations:int=10) -> tuple[float|None,str|None]:
    if not .5<=service_target<=.999: raise ValueError("service target outside frozen range")
    n=len(windows); expected_tail=n*(1-service_target)
    if expected_tail + 1e-12 < min_tail_observations: return None,f"insufficient_tail_evidence:{expected_tail:.2f}_expected_observations"
    return max(0.0,float(windows.cumulative_residual.quantile(service_target))),None

def robust_normal_safety_stock(scale:float,horizon:int,service_target:float) -> float:
    if not np.isfinite(scale) or scale<0 or horizon<1 or not .5<=service_target<=.999: raise ValueError("invalid normal safety-stock input")
    return max(0.0,float(norm.ppf(service_target)*scale*np.sqrt(horizon)))

def buffer_days_safety_stock(forecast_daily:pd.Series,buffer_days:int) -> float:
    if isinstance(buffer_days,bool) or not isinstance(buffer_days,(int,np.integer)) or not 0<=buffer_days<=28: raise ValueError("buffer days must be an integer in [0,28]")
    values=pd.to_numeric(forecast_daily,errors="coerce")
    if len(values)<buffer_days or not np.isfinite(values).all() or (values<0).any(): raise ValueError("buffer forecast must be finite, nonnegative, and long enough")
    return float(values.iloc[:buffer_days].sum())
