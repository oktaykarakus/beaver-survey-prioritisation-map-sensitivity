"""P2-C3 H4 reference (freeze §12): robust core of the 4 core A1 allocations expected from the observed reach-level rank-correlation
matrix alone. Gaussian copula with correlation 2 sin(pi rho_s / 6), empirical marginals, 200 replicates (seeds 30001-30200, as the
copula null of freeze §9), 5% budget; also 1% and 10%. Independence reference f^4 is analytic. Writes analysis/alloc/core_reference.json."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2c3_alloc as A
R = Path(__file__).resolve().parents[2]; AN = R / '05_Experiments/BHSI_v2_P2C3/analysis'
T = pd.read_parquet(AN / 'reach_table_B40.parquet'); L = T.length_m.values; n = len(T)
CORE = ['C_lo', 'C_hi', 'LEg_lo', 'LEg_hi']
S = np.column_stack([np.nan_to_num(T[f'{j.split("_")[0]}_s_{j.split("_")[1]}'].values) for j in CORE])
rho = stats.spearmanr(S).correlation; Rg = 2 * np.sin(np.pi * rho / 6); ch = np.linalg.cholesky(Rg)
perm = np.random.default_rng(20261117).permutation(n); Q = np.sort(S, axis=0); out = {}
for f in (0.01, 0.05, 0.10):
    B = f * L.sum(); cs = []
    for k in range(200):
        z = np.random.default_rng(30001 + k).standard_normal((n, 4)) @ ch.T
        Y = np.empty_like(S)
        for c in range(4): Y[np.argsort(z[:, c]), c] = Q[:, c]
        X = np.vstack([A.a1_reach(Y[:, c], L, B, perm) for c in range(4)])
        cs.append(float((X.min(0) * L).sum() / B))
    out[f'{f*100:g}'] = {'copula_core_mean': float(np.mean(cs)), 'p2.5': float(np.percentile(cs, 2.5)), 'p97.5': float(np.percentile(cs, 97.5)), 'independence_core': f ** 3}
out['spearman_matrix'] = {f'{a}|{b}': float(rho[i, j]) for i, a in enumerate(CORE) for j, b in enumerate(CORE) if i < j}
(AN / 'alloc/core_reference.json').write_text(json.dumps(out, indent=1) + '\n'); print(json.dumps(out, indent=1))
