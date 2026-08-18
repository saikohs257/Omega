from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss

RNG_SEED = 42
EPS = 1e-9


def _future_target(df: pd.DataFrame, horizon_h: int = 6) -> np.ndarray:
    t = df['open_time'].to_numpy(dtype='datetime64[ns]')
    ep = df['episode_type'].astype(str).to_numpy()
    y = np.zeros(len(df), dtype=np.int8)
    for i in range(len(df) - 1):
        end = t[i] + np.timedelta64(horizon_h, 'h')
        j = int(np.searchsorted(t, end, side='right'))
        if j > i + 1:
            y[i] = int(np.any(ep[i+1:j] != 'none'))
    return y


def add_causal_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy().sort_values('open_time').reset_index(drop=True)
    close = pd.to_numeric(x['close'], errors='coerce').clip(lower=1e-12)
    ret = np.log(close).diff().fillna(0.0)
    x['ret_1h'] = ret
    x['rv6'] = ret.rolling(6, min_periods=3).std()
    x['rv24'] = ret.rolling(24, min_periods=12).std()
    x['down24'] = (-ret.clip(upper=0)).rolling(24, min_periods=6).mean()
    x['ld_lag1'] = x['LiveDeficit'].shift(1)
    x['ld_slope3'] = x['LiveDeficit'].shift(1) - x['LiveDeficit'].shift(4)
    x['ld_slope6'] = x['LiveDeficit'].shift(1) - x['LiveDeficit'].shift(7)
    x['ld_slope24'] = x['LiveDeficit'].shift(1) - x['LiveDeficit'].shift(25)
    x['ld_max6'] = x['LiveDeficit'].shift(1).rolling(6, min_periods=3).max()
    x['ld_min24'] = x['LiveDeficit'].shift(1).rolling(24, min_periods=6).min()
    x['ss_lag1'] = x['SimpleShock'].shift(1)
    x['ss_max6'] = x['SimpleShock'].shift(1).rolling(6, min_periods=3).max()
    x['ss_slope6'] = x['SimpleShock'].shift(1) - x['SimpleShock'].shift(7)
    x['rr'] = x['RecoveryWeakness_v1'].shift(1) - x['LiveDeficit'].shift(1)
    x['burden'] = x['LiveDeficit'].shift(1)
    x['hazard'] = x['hazard_raw'].shift(1)
    # Strictly causal duration since LD crossed .70/.85.
    ld_prev = x['LiveDeficit'].shift(1)
    for thr, name in [(0.70, 'ld_age70'), (0.85, 'ld_age85')]:
        age = np.full(len(x), np.nan)
        last = None
        vals = ld_prev.to_numpy()
        for i, v in enumerate(vals):
            if not np.isfinite(v):
                continue
            if v > thr:
                if last is None:
                    last = i
                age[i] = i - last
            else:
                last = None
        x[name] = age
    x['future6'] = _future_target(x, 6)
    return x


def fit_auc(train, test, cols):
    a = train[cols].replace([np.inf, -np.inf], np.nan).dropna()
    b = test[cols].replace([np.inf, -np.inf], np.nan).dropna()
    common = a.index.intersection(b.index)
    a = train.loc[common, cols].replace([np.inf, -np.inf], np.nan).dropna()
    common = a.index
    b = test.loc[common, cols].replace([np.inf, -np.inf], np.nan).dropna()
    common = a.index.intersection(b.index)
    a, b = train.loc[common, cols], test.loc[common, cols]
    ytr, yte = train.loc[common, 'future6'].to_numpy(), test.loc[common, 'future6'].to_numpy()
    if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
        return None
    model = LogisticRegression(max_iter=2000, solver='liblinear', random_state=RNG_SEED)
    model.fit(a, ytr)
    p = model.predict_proba(b)[:, 1]
    return {
        'n': int(len(common)),
        'positives': int(yte.sum()),
        'auc': float(roc_auc_score(yte, p)),
        'brier': float(brier_score_loss(yte, p)),
        'mean_pred': float(p.mean()),
    }


def twin_test(test: pd.DataFrame, state_cols, history_cols, bin_steps=None):
    z = test.copy()
    steps = bin_steps or {c: 0.02 for c in state_cols}
    for c in state_cols:
        z[c + '_b'] = np.round(z[c] / steps[c]) * steps[c]
    key_cols = [c + '_b' for c in state_cols]
    # Actual rows only: require complete records; never groupby.first() across rows.
    z = z.dropna(subset=state_cols + history_cols + ['future6']).copy()
    groups = []
    diffs = []
    for _, g in z.groupby(key_cols, sort=False):
        if len(g) < 4 or g['future6'].nunique() < 2:
            continue
        # Within a present-state cell, split by an orthogonal history score.
        h = g[history_cols].rank(pct=True).mean(axis=1)
        med = float(h.median())
        lo = g[h <= med]
        hi = g[h > med]
        if len(lo) < 2 or len(hi) < 2:
            continue
        d = float(hi.future6.mean() - lo.future6.mean())
        groups.append({'n': int(len(g)), 'lo_n': int(len(lo)), 'hi_n': int(len(hi)), 'rate_diff': d})
        diffs.append(d)
    if not diffs:
        return {'n_cells': 0}
    return {
        'n_cells': len(diffs),
        'mean_abs_rate_diff': float(np.mean(np.abs(diffs))),
        'mean_rate_diff': float(np.mean(diffs)),
        'median_abs_rate_diff': float(np.median(np.abs(diffs))),
        'max_abs_rate_diff': float(np.max(np.abs(diffs))),
    }


def run(path, out):
    df = pd.read_csv(path)
    required = {'open_time','close','SimpleShock','LiveDeficit','episode_type','hazard_raw','RecoveryWeakness_v1'}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f'missing required columns: {sorted(missing)}')
    df['open_time'] = pd.to_datetime(df['open_time'], utc=True)
    df = add_causal_features(df)
    # Candidate models: sufficiency ladder.
    m0 = ['ld_lag1']
    m1 = ['ld_lag1','ss_lag1','rv6','rv24','down24','hazard']
    m2 = m1 + ['ld_slope3','ld_slope6','ld_slope24','ld_max6','ld_min24','ss_max6','ss_slope6','ld_age70','ld_age85']
    m3 = ['hazard','burden','rr','ss_lag1']
    m4 = m3 + ['ld_slope3','ld_slope6','ld_slope24','ld_max6','ld_min24','ss_max6','ss_slope6','ld_age70','ld_age85']
    models = {'M1_LD': m0, 'M2_present': m1, 'M3_history': m2, 'M4_state': m3, 'M5_state_history': m4}
    years = sorted(df.open_time.dt.year.unique())
    results = {'rows': int(len(df)), 'years': years, 'holdouts': {}, 'twin_tests': {}}
    for yr in years:
        if yr < 2021:
            continue
        train = df[df.open_time.dt.year < yr]
        test = df[df.open_time.dt.year == yr]
        if len(train) < 500 or len(test) < 100:
            continue
        results['holdouts'][str(yr)] = {}
        for name, cols in models.items():
            r = fit_auc(train, test, cols)
            results['holdouts'][str(yr)][name] = r
        state_cols = ['ld_lag1','ss_lag1','hazard','burden','rr']
        history_cols = ['ld_slope24','ld_age70','ld_age85','ss_max6','ss_slope6']
        results['twin_tests'][str(yr)] = twin_test(test, state_cols, history_cols)
    Path(out).write_text(json.dumps(results, indent=2, sort_keys=True))
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    run(args.csv, args.out)
