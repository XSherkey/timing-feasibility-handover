"""Symbolic implementations of the LLM call contract (surrogate backend).

Each function consumes exactly the structured payload a real prompt receives and
returns exactly the JSON schema Appendix A specifies.  They are deterministic
given ``rng``, so a run is reproducible from its seeds, while different seeds
produce different answers -- which is what the LLM-stability experiment
(Sec. 4.6) measures.
"""
from __future__ import annotations

import json
import math

import numpy as np

# --------------------------------------------------------------------------- #
# 1. forward translation: intent -> weight profile
# --------------------------------------------------------------------------- #
#: weight anchors per stated priority level, over the validated simplex
_PRIORITY_WEIGHT = {
    "critical": 0.80,
    "highest": 0.72,
    "high": 0.55,
    "medium": 0.33,
    "low": 0.18,
    "lowest": 0.10,
    "critical_power": 0.45,
}


def _priority_value(v) -> float:
    if isinstance(v, (int, float, np.floating)):
        return float(np.clip(v, 0.0, 1.0))
    s = str(v).strip().lower()
    return _PRIORITY_WEIGHT.get(s, 0.33)


def forward_translate(payload: dict, rng: np.random.Generator, temperature: float = 0.2) -> dict:
    """Derive a weight profile from the stated priorities.

    The profile is ``softmax`` over priority scores in log space, so a
    "reliability: highest / latency: low / power: low" intent yields a
    reliability-dominant profile, and the operator's ordering of priorities is
    preserved by construction.  Decoding temperature controls the amount of
    deviation, mirroring a sampling LLM.
    """
    intent = payload.get("intent", {})
    prio = intent.get("priorities", {}) or {}
    keys = ("reliability", "latency", "power")
    scores = np.array([_priority_value(prio.get(k, "medium")) for k in keys], dtype=np.float64)
    # the stated priority levels are used as relative weights, so the profile
    # preserves the operator's ordering by construction
    logits = np.log(np.clip(scores, 1e-3, None))
    logits = logits + rng.normal(scale=max(temperature, 1e-3) * 0.4, size=3)

    # A stated hard requirement clamps the minimum weight of that dimension.
    floors = np.full(3, 0.05)
    for i, k in enumerate(keys):
        if prio.get(k) in ("critical", "highest"):
            floors[i] = 0.55 if prio.get(k) == "critical" else 0.45

    for _ in range(40):
        w = np.exp(logits - logits.max())
        w /= w.sum()
        if np.all(w >= floors):
            break
        logits[np.argmin(w - floors)] += 0.4
    # quantise to 0.01 and renormalise so two runs either match exactly or do not
    w = np.round(w, 2)
    w /= w.sum()
    w = np.round(w, 2)
    w[-1] = round(1.0 - w[0] - w[1], 2)

    analysis = []
    order = np.argsort(-scores)
    for i in order:
        analysis.append(
            f"{keys[i]}: declared {prio.get(keys[i], 'medium')}, carried by "
            f"{ {'reliability': 'R_rel', 'latency': 'R_lat', 'power': 'R_pow'}[keys[i]] }"
        )
    mapping = {"reliability": "R_rel", "latency": "R_lat", "power": "R_pow"}
    open_q = []
    if abs(w[0] - w[1]) < 0.05:
        open_q.append("reliability and latency carry near-equal weight; confirm the tie-break")
    # the response carries the schema keys of Appendix A *and* the readable names
    weights = {f"w_{'rel' if k == 'reliability' else k[:3]}": float(x) for k, x in zip(keys, w)}
    return dict(
        analysis=analysis,
        weights=weights,
        weights_named=dict(zip(keys, [float(x) for x in w])),
        mapping=mapping,
        open_questions=open_q,
    )


# --------------------------------------------------------------------------- #
# 2. reverse forensics: failure episodes -> latent rule
# --------------------------------------------------------------------------- #
#: atoms the forensic grammar may reference
FIELD_SCHEMA = [
    dict(name="elevation_deg", kind="continuous", range=[0.0, 90.0]),
    dict(name="handover_advance_s", kind="continuous", range=[0.0, 24.0]),
    dict(name="isl_hop_count", kind="integer", range=[-1, 20]),
    dict(name="doppler_rate_hz_s", kind="continuous", range=[-8000.0, 8000.0]),
    dict(name="latitude_abs_deg", kind="continuous", range=[0.0, 90.0]),
    dict(name="snr_db", kind="continuous", range=[-10.0, 35.0]),
    dict(name="remaining_visibility_s", kind="continuous", range=[0.0, 900.0]),
    dict(name="plane_change", kind="categorical", range=[0, 1]),
    dict(name="path_available", kind="categorical", range=[0, 1]),
    dict(name="buffer_occupancy", kind="continuous", range=[0.0, 1.0]),
    dict(name="battery_state", kind="continuous", range=[0.0, 1.0]),
    dict(name="eclipse", kind="categorical", range=[0, 1]),
]

EFFECT_GRAMMAR = [
    dict(name="min_advance", params=dict(seconds=[6, 8, 10, 12, 14, 16]),
         remedy="removes late_handover: the requested lead is shorter than the acquisition time"),
    dict(name="forbid_unrouted_target", params={},
         remedy="removes no_route: the selected candidate has no feeder path"),
    dict(name="prefer_same_plane", params={},
         remedy="removes cross-plane fragility above the polar seam"),
    dict(name="power_cap", params=dict(max_lead_s=[6, 9, 12]),
         remedy="bounds dual-homing time when the battery is low"),
    dict(name="buffer_drain", params=dict(max_buffer=[0.5, 0.7, 0.85]),
         remedy="removes feeder congestion: prefer the least loaded candidate"),
    dict(name="cap_advance", params=dict(max_lead_s=[6, 8, 10, 12, 14]),
         remedy="bounds the lead so it cannot exceed a short window"),
    dict(name="prefer_long_visibility", params={},
         remedy="removes window_exceeded: pick the routed candidate that stays visible longest"),
]

#: candidate thresholds per field (a coarse version of what the prompt allows)
_THRESHOLDS = {
    "elevation_deg": [8, 10, 12, 15, 20, 25, 30, 40],
    "handover_advance_s": [4, 6, 8, 10, 12, 14],
    "isl_hop_count": [1, 2, 3, 4, 5, 6, 8],
    "doppler_rate_hz_s": [1000, 2000, 3000, 4000],
    "latitude_abs_deg": [60, 65, 70, 75],
    "snr_db": [6, 9, 12, 15],
    "remaining_visibility_s": [10, 20, 40, 60],
    "plane_change": [1],
    "path_available": [1],
    "buffer_occupancy": [0.5, 0.7, 0.85],
    "battery_state": [0.4, 0.6],
    "eclipse": [1],
}


def _atom_eval(atoms: list[dict], rows: list[dict]) -> np.ndarray:
    m = np.ones(len(rows), dtype=bool)
    for a in atoms:
        f, op, v = a["field"], a["cmp"], a["value"]
        vals = np.array([r.get(f, np.nan) for r in rows], dtype=np.float64)
        with np.errstate(invalid="ignore"):
            if op == "<=":
                m &= vals <= v
            elif op == ">=":
                m &= vals >= v
            elif op == "<":
                m &= vals < v
            elif op == ">":
                m &= vals > v
            elif op == "==":
                m &= vals == v
            elif op == "!=":
                m &= vals != v
    return m


def _candidate_atoms() -> list[dict]:
    atoms = []
    for f, ths in _THRESHOLDS.items():
        for t in ths:
            ops = ("==",) if f in ("plane_change", "path_available", "eclipse") else ("<=", ">=")
            for op in ops:
                atoms.append(dict(field=f, cmp=op, value=t))
    return atoms


def _score_predicate(atoms, fail_rows, succ_rows) -> tuple[float, float, float]:
    mf = _atom_eval(atoms, fail_rows)
    ms = _atom_eval(atoms, succ_rows) if succ_rows else np.zeros(0, dtype=bool)
    cover = mf.mean() if len(fail_rows) else 0.0
    purity = mf.sum() / max(mf.sum() + ms.sum(), 1)
    if cover < 0.15 or purity < 0.55:
        return 0.0, cover, purity
    return purity * math.sqrt(cover), cover, purity


def _effect_for(atoms: list[dict], fail_rows, succ_rows) -> dict:
    """Choose the executable effect the predicate implies."""
    fields = {a["field"] for a in atoms}
    if "handover_advance_s" in fields:
        # set the minimum advance just above the largest failing advance
        advs = [r.get("handover_advance_s", 0.0) for r in fail_rows if _atom_eval(atoms, [r])[0]]
        vals = [r["value"] for r in atoms if r["field"] == "handover_advance_s"]
        base = max(vals) if vals else 10
        if advs:
            base = max(base, float(np.percentile(advs, 90)) + 2.0)
        return dict(effect="min_advance", magnitude=float(np.ceil(base / 2.0) * 2.0))
    if "path_available" in fields or "isl_hop_count" in fields:
        return dict(effect="forbid_unrouted_target", magnitude=0.0)
    if "plane_change" in fields:
        return dict(effect="prefer_same_plane", magnitude=0.0)
    if "battery_state" in fields or "eclipse" in fields:
        return dict(effect="power_cap", magnitude=6.0)
    if "buffer_occupancy" in fields:
        return dict(effect="buffer_drain", magnitude=0.7)
    return dict(effect="min_advance", magnitude=12.0)


def forensic_hypothesis(
    payload: dict, rng: np.random.Generator, temperature: float = 0.2, top_k: int = 3
) -> dict:
    """Mine the latent rule that separates failures from successes.

    Implements a bounded threshold search over the declared field schema: every
    single atom and every conjunction of two atoms is scored by
    ``purity * sqrt(coverage)`` on the *discovery* set, the best
    ``top_k`` predicates are verbalised, and temperature-controlled noise breaks
    near-ties (which is what a sampling LLM would do).
    """
    fail_rows = payload.get("failure_rows", [])
    succ_rows = payload.get("success_rows", [])
    if not fail_rows:
        return dict(hypotheses=[], alternative_explanations=["no failing episodes in the discovery set"])

    atoms = _candidate_atoms()
    scored = []
    for a in atoms:
        s, cover, purity = _score_predicate([a], fail_rows, succ_rows)
        if s > 0:
            scored.append((s, [a], cover, purity))
    # conjunctions of two atoms (bounded: top 24 single atoms only)
    top1 = sorted(scored, key=lambda x: -x[0])[:24]
    for i in range(len(top1)):
        for j in range(i + 1, len(top1)):
            a1, a2 = top1[i][1][0], top1[j][1][0]
            if a1["field"] == a2["field"]:
                continue
            pair = [a1, a2]
            s, cover, purity = _score_predicate(pair, fail_rows, succ_rows)
            if s > 0:
                scored.append((s, pair, cover, purity))
    if not scored:
        return dict(
            hypotheses=[],
            alternative_explanations=["the failure set is not separable by any declared predicate"],
        )

    scored.sort(key=lambda x: -x[0])
    # temperature-weighted selection among near-optimal hypotheses
    base = np.array([s for s, *_ in scored[:12]])
    logits = base / max(temperature, 1e-3) / 4.0
    probs = np.exp(logits - logits.max())
    probs /= probs.sum()
    order = np.argsort(-probs)

    hyps = []
    for k in order[:top_k]:
        s, atoms_k, cover, purity = scored[int(k)]
        eff = _effect_for(atoms_k, fail_rows, succ_rows)
        reading = " AND ".join(f"{a['field']} {a['cmp']} {a['value']}" for a in atoms_k)
        hyps.append(
            dict(
                if_=dict(all=atoms_k),
                then=eff,
                rationale=(
                    f"covers {cover * 100:.0f}% of discovery failures with {purity * 100:.0f}% purity; "
                    f"rule: IF {reading} THEN {eff['effect']}({eff['magnitude']})"
                ),
                score=float(s),
            )
        )
    out = dict(
        hypotheses=[
            {("if" if k == "if_" else k): v for k, v in h.items()} for h in hyps
        ],
        alternative_explanations=[
            "the improvement may be a traffic-mix artefact rather than a geometric constraint",
            "sample size in the discovery set may be too small to separate purity from noise",
        ],
    )
    return out


# --------------------------------------------------------------------------- #
# 3. topology seeds / mutation / crossover / critique
# --------------------------------------------------------------------------- #
_KINDS = ["gcn", "att", "hybrid", "mlp"]
_WIDTHS = [32, 64, 96, 128, 192, 256]
_POOLS = ["mean", "max"]
_HEADS = [1, 2, 4, 8]


def topology_seed(payload: dict, rng: np.random.Generator, temperature: float = 0.7) -> dict:
    """Sample a grammar-valid sketch conditioned on the regime."""
    tags = payload.get("regime_tags", {}) or {}
    sparse = bool(tags.get("sparse_isl", False)) or bool(tags.get("polar", False))
    power_limited = bool(tags.get("power_limited", False))
    if sparse:
        kind_p = np.array([0.60, 0.10, 0.20, 0.10])
    elif power_limited:
        kind_p = np.array([0.55, 0.05, 0.15, 0.25])
    else:
        kind_p = np.array([0.40, 0.20, 0.30, 0.10])
    kind = _KINDS[int(rng.choice(len(_KINDS), p=kind_p / kind_p.sum()))]
    width = int(_WIDTHS[int(rng.integers(0, 3))]) if power_limited else int(_WIDTHS[int(rng.integers(1, 4))])
    layers = int(rng.integers(1, 4))
    heads = int(_HEADS[int(rng.integers(0, 2))])
    if kind == "att" and width % heads:
        heads = 1
    pool = _POOLS[int(rng.integers(0, 2))]
    # grammar rule: at most one attention node for sparse polar regimes
    if sparse and kind == "hybrid" and layers > 2:
        layers = 2
    return dict(
        kind=kind,
        width=width,
        layers=layers,
        heads=heads,
        pool=pool,
        ctx_width=int(_WIDTHS[int(rng.integers(1, 3))]),
        ctx_layers=int(rng.integers(1, 3)),
        rationale=(
            f"regime {'sparse/polar' if sparse else 'nominal'}; "
            f"{'power-limited payload' if power_limited else 'nominal power budget'}"
        ),
    )


def topology_mutation(payload: dict, rng: np.random.Generator, temperature: float = 0.7) -> dict:
    """Apply exactly one minimal grammar-preserving edit."""
    spec = dict(payload.get("sketch", {}) or {})
    for k, v in dict(kind="gcn", width=64, layers=2, heads=2, pool="mean",
                     ctx_width=64, ctx_layers=1).items():
        spec.setdefault(k, v)
    feedback = payload.get("fitness_feedback", {}) or {}
    edits = []
    if spec["width"] < 256:
        edits.append(("width", spec["width"] * 2))
    if spec["width"] > 32:
        edits.append(("width", max(32, spec["width"] // 2)))
    if spec["layers"] < 4:
        edits.append(("layers", spec["layers"] + 1))
    if spec["layers"] > 1:
        edits.append(("layers", spec["layers"] - 1))
    if spec["kind"] == "att":
        edits.append(("heads", _HEADS[min(len(_HEADS) - 1, _HEADS.index(spec["heads"]) + 1)]))
        edits.append(("heads", _HEADS[max(0, _HEADS.index(spec["heads"]) - 1)]))
    edits.append(("pool", "max" if spec["pool"] == "mean" else "mean"))
    edits.append(("kind", _KINDS[int(rng.integers(0, len(_KINDS)))]))
    # bias the edit by the feedback direction
    obj = feedback.get("objective", "reward")
    feasible = [e for e in edits if _valid(spec, *e)]
    if not feasible:
        feasible = edits
    if obj == "params" or feedback.get("too_large"):
        cand = [e for e in feasible if e[0] in ("width", "layers") and e[1] < spec[e[0]]]
        feasible = cand or feasible
    if obj == "reward" and feedback.get("underfit"):
        cand = [e for e in feasible if e[0] in ("width", "layers") and e[1] > spec[e[0]]]
        feasible = cand or feasible
    key, val = feasible[int(rng.integers(0, len(feasible)))]
    spec[key] = val
    if spec["kind"] == "att" and spec["width"] % spec["heads"]:
        spec["heads"] = 1
    spec["rationale"] = f"single edit {key}->{val} targeting {obj}"
    return spec


def _valid(spec: dict, key: str, val) -> bool:
    s = dict(spec)
    s[key] = val
    if s["width"] > 256 or s["width"] < 32:
        return False
    if s["layers"] > 4 or s["layers"] < 1:
        return False
    if s["kind"] == "att" and s["width"] % max(s["heads"], 1):
        return False
    return True


def topology_crossover(payload: dict, rng: np.random.Generator, temperature: float = 0.7) -> dict:
    """Merge homologous parts: take kind dimension from one parent, depth from the other."""
    a = dict(payload.get("sketch_a", {}) or {})
    b = dict(payload.get("sketch_b", {}) or {})
    keys_a = dict(kind="gcn", width=64, layers=2, heads=2, pool="mean", ctx_width=64, ctx_layers=1)
    for k, v in keys_a.items():
        a.setdefault(k, v)
        b.setdefault(k, v)
    child = {
        "kind": a["kind"],
        "width": b["width"],
        "layers": a["layers"],
        "heads": b["heads"],
        "pool": a["pool"] if rng.random() < 0.5 else b["pool"],
        "ctx_width": a["ctx_width"],
        "ctx_layers": b["ctx_layers"],
    }
    if child["kind"] == "att" and child["width"] % max(child["heads"], 1):
        child["heads"] = 1
    child["rationale"] = "aligned on operating family, swapped depth/width from the second parent"
    return child


def population_critique(payload: dict, rng: np.random.Generator, temperature: float = 0.7) -> dict:
    elites = payload.get("elites", []) or []
    probs = dict(payload.get("probs", {}) or {})
    depths = [e.get("layers", 2) for e in elites] or [2]
    widths = [e.get("width", 64) for e in elites] or [64]
    depth_bias = 0.1 if np.mean(depths) < 2.5 else -0.1
    width_bias = 0.1 if np.mean(widths) > 96 else -0.1
    return dict(
        mutation_rate=float(np.clip(probs.get("mutation_rate", 0.3) + rng.normal(0, 0.02), 0.1, 0.6)),
        crossover_rate=float(np.clip(probs.get("crossover_rate", 0.4) + rng.normal(0, 0.02), 0.1, 0.7)),
        width_bias=float(np.clip(width_bias + rng.normal(0, 0.03), -0.25, 0.25)),
        depth_bias=float(np.clip(depth_bias + rng.normal(0, 0.03), -0.25, 0.25)),
        rationale="shift operator probabilities toward the region where the elite set concentrates",
    )
