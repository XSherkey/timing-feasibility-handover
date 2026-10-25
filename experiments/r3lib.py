"""Shared helpers for the R3 (TNSM) experiment suite.

Every script in ``experiments/`` reads ``experiments/manifest_r3.json`` and writes into
``results/routeA_r3/``.  Nothing here hard-codes a seed list or an episode id.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "routeA_r3"
PY = sys.executable

MANIFEST = json.loads((ROOT / "experiments" / "manifest_r3.json").read_text(encoding="utf-8"))
SEEDS = MANIFEST["policy_seeds"]
TRAFFIC = MANIFEST["traffic_eval"]
LOCKBOX_EPOCHS = MANIFEST["lockbox_epochs"]
DRIFT_ACQ = MANIFEST["physics_drift_acq_signaling"]
EPOCH = MANIFEST["twin"]["epoch_doy"]

CACHE = OUT / "_cache"
CACHE.mkdir(parents=True, exist_ok=True)


def _key(params: dict) -> str:
    import hashlib
    import re

    items = sorted((k, str(v)) for k, v in params.items())
    raw = "_".join(f"{k}{v}" for k, v in items)
    slug = re.sub(r"[^A-Za-z0-9_=-]+", "-", raw)[:60].strip("-")
    return f"{slug}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"


def evaluate(
    label: str,
    *,
    run: str | None = None,
    policy: str = "ckpt",
    rule: str | None = None,
    rules: list[str] | None = None,
    oracle: bool = False,
    window: str = "test",
    epoch_doy: float | None = None,
    acq: float | None = None,
    lead: float | None = None,
    traffic: float | None = None,
    seed: int = 0,
    steps: int | None = None,
) -> dict:
    """Run one eval_shield.py call (cached on its arguments) and return the parsed JSON."""
    rules = list(rules or ([] if rule is None else [rule]))
    params = dict(label=label, run=run, policy=policy, rule="|".join(rules), oracle=oracle, window=window,
                  epoch=epoch_doy, acq=acq, lead=lead, traffic=traffic, seed=seed, steps=steps)
    cp = CACHE / (_key(params) + ".json")
    if cp.exists():
        return _normalise(json.loads(cp.read_text(encoding="utf-8")))
    cmd = [PY, str(ROOT / "scripts" / "eval_shield.py")]
    if run:
        cmd += ["--run", run]
    else:
        cmd += ["--policy", policy]
    if lead is not None:
        cmd += ["--lead", str(lead)]
    for r in rules:
        cmd += ["--rule", r]
    if oracle:
        cmd += ["--oracle-shield"]
    if window != "test":
        cmd += ["--window", window]
    if epoch_doy is not None:
        cmd += ["--epoch-doy", str(epoch_doy)]
    if acq is not None:
        cmd += ["--acq-signaling", str(acq)]
    if traffic is not None:
        cmd += ["--traffic", str(traffic)]
    if steps is not None:
        cmd += ["--steps", str(steps)]
    cmd += ["--seed", str(seed), "--out", str(cp), "--label", label]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT))
    if r.returncode != 0 or not cp.exists():
        raise RuntimeError(f"eval failed: {' '.join(cmd)}\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    raw = json.loads(cp.read_text(encoding="utf-8"))
    return _normalise(raw)


def _normalise(raw):
    """eval_shield writes one record per traffic multiplier; collapse to attempts-weighted means."""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, list) or not raw:
        raise RuntimeError("empty eval output")
    if len(raw) == 1:
        return raw[0]
    def wavg(key):
        num = sum(float(r[key][0]) * float(r[key][1]) for r in raw if r.get(key) and r[key][1])
        den = sum(float(r[key][1]) for r in raw if r.get(key) and r[key][1])
        return [num / den if den else None, int(den)]
    first = dict(raw[0])
    for key in ("arctic", "midlat", "equatorial", "overall"):
        if all(r.get(key) for r in raw):
            first[key] = wavg(key)
    first["sat_records"] = [dict(satisfaction=r.get("satisfaction"),
                                 arctic=r.get("satisfaction_arctic")) for r in raw]
    return first


def arctic(res: dict) -> float:
    v = res["arctic"][0]
    return float("nan") if v is None else 100.0 * float(v)


def late_share(res: dict) -> float:
    for k in ("late_share", "late_handover_share"):
        if k in res and res[k] is not None:
            return 100.0 * float(res[k])
    pc = res.get("polar_causes") or {}
    if "late_handover" in pc:
        return 100.0 * float(pc["late_handover"])
    return float("nan")


def summarise(values: list[float]) -> dict:
    v = np.asarray([x for x in values if np.isfinite(x)], dtype=float)
    if v.size == 0:
        return dict(mean=None, sd=None, n=0)
    return dict(mean=float(v.mean()), sd=float(v.std(ddof=1)) if v.size > 1 else 0.0,
                n=int(v.size), min=float(v.min()), max=float(v.max()))


def paired_stats(a: list[float], b: list[float]) -> dict:
    """Paired over seeds: exact Wilcoxon, bootstrap CI of the mean difference, Cohen's dz, TOST."""
    from scipy import stats

    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    d = a - b
    out = dict(n=int(d.size), mean_diff=float(d.mean()) if d.size else None,
               sd_diff=float(d.std(ddof=1)) if d.size > 1 else None)
    if d.size >= 5 and np.any(d != 0):
        try:
            out["wilcoxon_p"] = float(stats.wilcoxon(a, b, alternative="two-sided", method="exact").pvalue)
        except Exception:  # pragma: no cover
            out["wilcoxon_p"] = float(stats.wilcoxon(a, b, alternative="two-sided").pvalue)
    else:
        out["wilcoxon_p"] = None
    rng = np.random.default_rng(0)
    if d.size:
        boot = rng.choice(d, size=(10000, d.size), replace=True).mean(axis=1)
        out["ci95"] = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
    else:
        out["ci95"] = [None, None]
    if d.size > 1 and d.std(ddof=1) > 0:
        out["cohen_dz"] = float(d.mean() / d.std(ddof=1))
    else:
        out["cohen_dz"] = None
    return out


def tost(a: list[float], b: list[float], margin: float = 1.0) -> dict:
    """Two one-sided tests for equivalence of paired means (normal approximation)."""
    from scipy import stats

    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ok = np.isfinite(a) & np.isfinite(b)
    d = a[ok] - b[ok]
    n = d.size
    if n < 3 or d.std(ddof=1) == 0:
        return dict(n=int(n), equivalent=None)
    se = d.std(ddof=1) / np.sqrt(n)
    t1 = (d.mean() - (-margin)) / se
    t2 = (d.mean() - margin) / se
    p1 = 1 - stats.t.cdf(t1, n - 1)
    p2 = stats.t.cdf(t2, n - 1)
    return dict(n=int(n), p_lower=float(p1), p_upper=float(p2), p_max=float(max(p1, p2)),
                equivalent=bool(max(p1, p2) < 0.05), margin=margin)


def holm(pvals: dict[str, float]) -> dict[str, float]:
    items = [(k, p) for k, p in pvals.items() if p is not None]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    out, prev = {}, 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, max(prev, (m - i) * p))
        out[k] = adj
        prev = adj
    return out


def write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print("wrote", path)
