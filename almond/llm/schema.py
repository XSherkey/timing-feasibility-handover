"""Response schema validation and repair hints for the LLM call contract.

A real model does not always honour the JSON schema of Appendix A.  Every
response is validated here; failures raise a repair hint that is fed back to the
model on the next attempt (the manuscript's "invalid outputs are re-requested
rather than post-processed heuristically").  The validator is also the metric
source for the LLM-stability experiment.
"""
from __future__ import annotations

from .kg_fields import EFFECTS, FIELDS

CMP = ("<", "<=", ">", ">=", "==", "!=")


def _num(x) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def validate_response(call_type: str, data) -> tuple[bool, str]:
    """Return ``(ok, hint)``; ``hint`` tells the model what to fix."""
    if not isinstance(data, dict):
        return False, "the response must be a single JSON object"
    if call_type == "forward_translate":
        w = data.get("weights")
        if not isinstance(w, dict):
            return False, 'missing "weights"; expected {"w_rel":..,"w_lat":..,"w_pow":..}'
        vals = {k: _num(w.get(k)) for k in ("w_rel", "w_lat", "w_pow")}
        if any(v is None for v in vals.values()):
            return False, 'weights must contain numeric "w_rel", "w_lat" and "w_pow"'
        if any(v < 0.0 or v > 1.0 for v in vals.values()):
            return False, "each weight must lie in [0, 1]"
        s = sum(vals.values())
        if abs(s - 1.0) > 0.02:
            return False, f"the three weights must sum to 1.0 (they sum to {s:.3f})"
        if not isinstance(data.get("analysis", []), list):
            return False, '"analysis" must be a list of strings'
        return True, ""
    if call_type == "forensic_hypothesis":
        hyps = data.get("hypotheses")
        if not isinstance(hyps, list):
            return False, 'missing "hypotheses" list'
        for h in hyps:
            if not isinstance(h, dict):
                return False, "each hypothesis must be an object"
            cond = h.get("if")
            if not isinstance(cond, dict) or not isinstance(cond.get("all"), list) or not cond["all"]:
                return False, 'each hypothesis needs {"if": {"all": [atoms...]}}'
            if len(cond["all"]) > 2:
                return False, "at most two atoms per predicate"
            for a in cond["all"]:
                if not isinstance(a, dict):
                    return False, "each atom must be an object"
                if a.get("field") not in FIELDS:
                    return False, f'unknown field "{a.get("field")}"; allowed: {sorted(FIELDS)}'
                if a.get("cmp") not in CMP:
                    return False, f'illegal comparator "{a.get("cmp")}"'
                if _num(a.get("value")) is None:
                    return False, "atom value must be numeric"
            then = h.get("then")
            if not isinstance(then, dict) or then.get("effect") not in EFFECTS:
                return False, f'each hypothesis needs "then": {{"effect": one of {sorted(EFFECTS)}}}'
            if _num(then.get("magnitude")) is None:
                return False, '"then.magnitude" must be numeric'
        return True, ""
    if call_type in ("topology_seed", "topology_mutation", "topology_crossover"):
        kind = data.get("kind")
        if kind not in ("mlp", "gcn", "att", "hybrid"):
            return False, 'kind must be one of "mlp", "gcn", "att", "hybrid"'
        for k, lo, hi in (("width", 32, 256), ("layers", 1, 8), ("ctx_width", 16, 256),
                          ("ctx_layers", 1, 4), ("heads", 1, 8),
                          ("head_width", 0, 256), ("edge_types", 0, 1)):
            default = 0 if k in ("head_width", "edge_types") else None
            v = _num(data.get(k, default))
            if v is None or not (lo <= v <= hi):
                return False, f'"{k}" must be a number in [{lo}, {hi}]'
        if data.get("pool") not in ("mean", "max"):
            return False, 'pool must be "mean" or "max"'
        return True, ""
    if call_type == "population_critique":
        for k, lo, hi in (("mutation_rate", 0.05, 0.8), ("crossover_rate", 0.05, 0.9)):
            v = _num(data.get(k))
            if v is None or not (lo <= v <= hi):
                return False, f'"{k}" must be a number in [{lo}, {hi}]'
        return True, ""
    return True, ""


def normalise(call_type: str, data: dict) -> dict:
    """Clamp numerics into the legal range and drop unknown keys.

    Only applied *after* validation succeeded, so it never rescues an invalid
    artifact -- it just removes harmless slack (e.g. ``layers: 3.0``).
    """
    if not isinstance(data, dict):
        return data
    if call_type in ("topology_seed", "topology_mutation", "topology_crossover"):
        out = dict(
            kind=data["kind"],
            width=int(round(float(data["width"]))),
            layers=int(round(float(data["layers"]))),
            heads=int(round(float(data.get("heads", 1)))),
            pool=data["pool"],
            ctx_width=int(round(float(data.get("ctx_width", 64)))),
            ctx_layers=int(round(float(data.get("ctx_layers", 1)))),
            head_width=int(round(float(data.get("head_width", 0) or 0))),
            edge_types=int(round(float(data.get("edge_types", 0) or 0))),
            rationale=str(data.get("rationale", ""))[:400],
        )
        if out["kind"] == "att" and out["width"] % out["heads"]:
            out["heads"] = 1
        return out
    if call_type == "population_critique":
        return dict(
            mutation_rate=float(data["mutation_rate"]),
            crossover_rate=float(data["crossover_rate"]),
            width_bias=float(data.get("width_bias", 0.0) or 0.0),
            depth_bias=float(data.get("depth_bias", 0.0) or 0.0),
            rationale=str(data.get("rationale", ""))[:400],
        )
    if call_type == "forward_translate":
        w = data["weights"]
        vals = [float(w["w_rel"]), float(w["w_lat"]), float(w["w_pow"])]
        s = sum(vals)
        vals = [v / s for v in vals]
        vals = [round(v, 2) for v in vals]
        vals[-1] = round(1.0 - vals[0] - vals[1], 2)
        data = dict(data)
        data["weights"] = dict(zip(("w_rel", "w_lat", "w_pow"), vals))
        return data
    return data
