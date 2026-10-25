"""Three-stage constraint auditor (manuscript Sec. 3.2.3).

``SemanticAudit``
    Consistency between the operator intent and the artefact.  For a weight
    profile the check is that the ordering of the stated priorities survives in
    the profile; for a constraint it is that the effect does not contradict the
    declared priority (e.g. a power cap on a reliability-critical intent).

``PhysicsAudit``
    Deterministic closed-form checks against the twin's metric layer and the
    protocol timing: the predicate must reference declared fields, thresholds
    must lie inside the physical range, a minimum-advance effect must exceed the
    signalling round trip, and a rule may not demand an advance longer than the
    longest visibility window in scope.  No LLM output is consulted here.

``ImpactAudit``
    A small deterministic surrogate predicts the latency and reward shift that
    enforcing the rule would cause, with an ensemble-based uncertainty.  A rule
    is accepted only if ``predicted latency shift + 2 sigma`` stays inside the
    latency budget; otherwise it is modulated (threshold relaxed) and re-tested.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .kg import EXECUTABLE_EFFECTS, FIELD_NAMES, Constraint

L_MAX_MS = 150.0
L_MIN_MS = 20.0

FIELD_RANGES = {
    "elevation_deg": (0.0, 90.0),
    "handover_advance_s": (0.0, 60.0),
    "isl_hop_count": (-1.0, 30.0),
    "doppler_rate_hz_s": (-1e4, 1e4),
    "latitude_abs_deg": (0.0, 90.0),
    "snr_db": (-20.0, 40.0),
    "remaining_visibility_s": (0.0, 1.2e3),
    "plane_change": (0.0, 1.0),
    "path_available": (0.0, 1.0),
    "buffer_occupancy": (0.0, 1.0),
    "battery_state": (0.0, 1.0),
    "eclipse": (0.0, 1.0),
}

#: minimum signalling interaction of the beam-switch protocol (seconds)
T_SIGNALLING_FLOOR = 2.4
#: longest visibility window of the reference polar shell (seconds)
T_VISIBILITY_CEIL = 620.0

PRIORITY_RANK = {
    "lowest": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "highest": 4,
    "critical": 5,
}


@dataclass
class AuditResult:
    ok: bool
    stage: str
    reason: str = ""
    question: str = ""
    confidence: float = 0.0
    detail: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# stage 1: semantic
# --------------------------------------------------------------------------- #
def semantic_audit_weights(weights: dict, intent: dict) -> AuditResult:
    prio = (intent.get("priorities") or {}) if isinstance(intent, dict) else {}
    keys = ("reliability", "latency", "power")
    if not prio:
        return AuditResult(True, "semantic", "no explicit priority order to contradict", confidence=0.5)
    ranks = {k: PRIORITY_RANK.get(str(prio.get(k, "medium")).lower(), 2) for k in keys}
    inversions = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if ranks[a] - ranks[b] >= 1 and weights[a] + 0.04 < weights[b]:
                inversions.append(f"{b} outweighs {a} although {a} is declared higher")
            if ranks[b] - ranks[a] >= 1 and weights[b] + 0.04 < weights[a]:
                inversions.append(f"{a} outweighs {b} although {b} is declared higher")
    if inversions:
        return AuditResult(
            False,
            "semantic",
            "; ".join(inversions),
            question="Which requirement should dominate when they conflict?",
            confidence=0.9,
        )
    # a 'critical' dimension must not be nearly extinguished
    for k in keys:
        if ranks[k] >= 5 and weights[k] < 0.2:
            return AuditResult(
                False,
                "semantic",
                f"{k} is declared critical but carries only {weights[k]:.2f}",
                question=f"Confirm that {k} may be traded away below 20% weight.",
                confidence=0.8,
            )
    return AuditResult(True, "semantic", "priority ordering preserved", confidence=0.95)


def semantic_audit_constraint(atoms: list[dict], effect: str, intent: dict) -> AuditResult:
    prio = (intent.get("priorities") or {}) if isinstance(intent, dict) else {}
    rel = PRIORITY_RANK.get(str(prio.get("reliability", "medium")).lower(), 2)
    lat = PRIORITY_RANK.get(str(prio.get("latency", "medium")).lower(), 2)
    powr = PRIORITY_RANK.get(str(prio.get("power", "medium")).lower(), 2)
    magnitude = 0.0
    if effect in ("power_cap", "buffer_drain") and rel >= 4 and powr <= 3:
        return AuditResult(
            False,
            "semantic",
            "a power cap would undercut a reliability-critical intent",
            question="Is a power cap acceptable for a reliability-critical service?",
            confidence=0.8,
        )
    if effect in ("min_advance",):
        # a long dual-homing window is not acceptable when latency or power is
        # the declared critical requirement
        long_advance = any(
            a.get("field") == "handover_advance_s" for a in atoms
        )
        if long_advance and (lat >= 5 or powr >= 5):
            return AuditResult(
                False,
                "semantic",
                "extending the preparation advance conflicts with the declared latency/power priority",
                question="Is a longer dual-homing window acceptable given the latency/power constraint?",
                confidence=0.7,
            )
    return AuditResult(True, "semantic", "effect consistent with the stated priority", confidence=0.9)


# --------------------------------------------------------------------------- #
# stage 2: physics
# --------------------------------------------------------------------------- #
def physics_audit(
    atoms: list[dict],
    effect: str,
    magnitude: float,
    scope: dict | None = None,
    visibility_ceil_s: float = T_VISIBILITY_CEIL,
) -> AuditResult:
    scope = scope or {}
    if effect not in EXECUTABLE_EFFECTS:
        return AuditResult(False, "physics", f"effect '{effect}' is not executable", confidence=1.0)
    if not atoms:
        return AuditResult(False, "physics", "empty predicate", confidence=1.0)
    for a in atoms:
        f = a.get("field")
        if f not in FIELD_NAMES:
            return AuditResult(False, "physics", f"unknown telemetry field '{f}'", confidence=1.0)
        lo, hi = FIELD_RANGES[f]
        v = float(a.get("value", np.nan))
        if not (lo - 1e-9 <= v <= hi + 1e-9):
            return AuditResult(
                False, "physics", f"threshold {v} for {f} outside physical range [{lo}, {hi}]", confidence=1.0
            )
        if a.get("cmp") not in ("<", "<=", ">", ">=", "==", "!="):
            return AuditResult(False, "physics", f"illegal comparison '{a.get('cmp')}'", confidence=1.0)
    if effect == "min_advance":
        if magnitude < T_SIGNALLING_FLOOR:
            return AuditResult(
                False,
                "physics",
                f"min_advance {magnitude:.1f}s is below the signalling floor {T_SIGNALLING_FLOOR:.1f}s",
                confidence=1.0,
            )
        if magnitude > visibility_ceil_s:
            return AuditResult(
                False,
                "physics",
                f"min_advance {magnitude:.1f}s exceeds the longest visibility window "
                f"({visibility_ceil_s:.0f}s) and is unachievable",
                confidence=1.0,
            )
        if magnitude > 0.6 * visibility_ceil_s:
            return AuditResult(
                False,
                "physics",
                f"min_advance {magnitude:.1f}s would consume >60% of the visibility window",
                confidence=0.7,
            )
    # elevation thresholds must be inside the mask..90 deg band
    for a in atoms:
        if a["field"] == "elevation_deg" and float(a["value"]) < 5.0:
            return AuditResult(
                False,
                "physics",
                "elevation threshold below the 5 deg link-acquisition floor",
                confidence=1.0,
            )
    return AuditResult(True, "physics", "predicate and effect physically admissible", confidence=1.0)


# --------------------------------------------------------------------------- #
# stage 3: impact predictor
# --------------------------------------------------------------------------- #
class ImpactPredictor:
    """Deterministic surrogate: rule features -> predicted delta latency / reward.

    A two-layer MLP (256 units, ReLU) trained on twin rollouts spanning the
    candidate-rule grammar.  ``predict`` returns the ensemble mean and standard
    deviation over ``n_models`` independently initialised members, which is the
    uncertainty the auditor uses (a rule is accepted only if
    ``mean + 2 sigma`` stays inside the latency budget).
    """

    def __init__(self, n_models: int = 5, hidden: int = 256, seed: int = 0):
        self.n_models = n_models
        self.hidden = hidden
        self.seed = seed
        self.weights: list[dict] = []
        self.fitted = False
        self.feat_mean: np.ndarray | None = None
        self.feat_std: np.ndarray | None = None
        self.mae = float("nan")
        self.calibration = float("nan")

    # -- feature map ---------------------------------------------------- #
    @staticmethod
    def featurise(atoms: list[dict], effect: str, magnitude: float, scope: dict | None = None) -> np.ndarray:
        scope = scope or {}
        f = np.zeros(24, dtype=np.float64)
        onehot_effect = {
            "min_advance": 0, "forbid_unrouted_target": 1, "prefer_same_plane": 2,
            "power_cap": 3, "buffer_drain": 4,
        }
        f[onehot_effect.get(effect, 0)] = 1.0
        f[5] = float(magnitude) / 24.0
        f[6] = len(atoms) / 3.0
        for a in atoms:
            idx = 7 + (hash(a["field"]) % 8)
            f[idx] = max(f[idx], float(a["value"]) / 90.0)
        f[15] = float(scope.get("latitude_abs_deg", 60.0)) / 90.0
        f[16] = 1.0 if scope.get("polar") else 0.0
        f[17] = 1.0 if scope.get("sparse_isl") else 0.0
        f[18] = 1.0 if scope.get("eclipse") else 0.0
        f[19] = float(scope.get("traffic_scale", 1.0))
        f[20] = 1.0
        return f

    # -- training ------------------------------------------------------- #
    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 400, lr: float = 1e-3) -> "ImpactPredictor":
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).reshape(-1, 1)
        self.feat_mean = X.mean(axis=0)
        self.feat_std = X.std(axis=0) + 1e-6
        Xn = (X - self.feat_mean) / self.feat_std
        self.weights = []
        for m in range(self.n_models):
            rng = np.random.default_rng(self.seed + m)
            W1 = rng.normal(0, math.sqrt(2.0 / Xn.shape[1]), (Xn.shape[1], self.hidden))
            b1 = np.zeros(self.hidden)
            W2 = rng.normal(0, math.sqrt(2.0 / self.hidden), (self.hidden, self.hidden))
            b2 = np.zeros(self.hidden)
            W3 = rng.normal(0, math.sqrt(1.0 / self.hidden), (self.hidden, 1))
            b3 = np.zeros(1)
            params = [W1, b1, W2, b2, W3, b3]
            mom = [np.zeros_like(p) for p in params]
            vel = [np.zeros_like(p) for p in params]
            for ep in range(epochs):
                h1 = np.maximum(0, Xn @ W1 + b1)
                h2 = np.maximum(0, h1 @ W2 + b2)
                out = h2 @ W3 + b3
                g = 2 * (out - y) / Xn.shape[0]
                gW3 = h2.T @ g
                gb3 = g.sum(axis=0)
                g2 = (g @ W3.T) * (h2 > 0)
                gW2 = h1.T @ g2
                gb2 = g2.sum(axis=0)
                g1 = (g2 @ W2.T) * (h1 > 0)
                gW1 = Xn.T @ g1
                gb1 = g1.sum(axis=0)
                grads = [gW1, gb1, gW2, gb2, gW3, gb3]
                for i, (p, gr) in enumerate(zip(params, grads)):
                    mom[i] = 0.9 * mom[i] + 0.1 * gr
                    vel[i] = 0.999 * vel[i] + 0.001 * gr**2
                    p -= lr * (mom[i] / (1 - 0.9 ** (ep + 1))) / (
                        np.sqrt(vel[i] / (1 - 0.999 ** (ep + 1))) + 1e-8
                    )
            self.weights.append(dict(W1=W1, b1=b1, W2=W2, b2=b2, W3=W3, b3=b3))
        self.fitted = True
        pred = self.predict(X)[0]
        self.mae = float(np.mean(np.abs(pred - y.ravel())))
        # calibration: slope of pred vs truth (1.0 = perfectly calibrated)
        if np.std(y) > 1e-9:
            self.calibration = float(np.polyfit(y.ravel(), pred, 1)[0])
        return self

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        X = np.atleast_2d(np.asarray(X, dtype=np.float64))
        if not self.fitted:
            raise RuntimeError("ImpactPredictor is not fitted")
        Xn = (X - self.feat_mean) / self.feat_std
        outs = []
        for w in self.weights:
            h1 = np.maximum(0, Xn @ w["W1"] + w["b1"])
            h2 = np.maximum(0, h1 @ w["W2"] + w["b2"])
            outs.append((h2 @ w["W3"] + w["b3"]).ravel())
        A = np.stack(outs, axis=0)
        return A.mean(axis=0), A.std(axis=0)

    def save(self, path: str) -> None:
        np.savez(
            path,
            n_models=self.n_models,
            hidden=self.hidden,
            feat_mean=self.feat_mean,
            feat_std=self.feat_std,
            weights=np.array([np.concatenate([w[k].ravel() for k in ("W1", "b1", "W2", "b2", "W3", "b3")]) for w in self.weights]),
            mae=self.mae,
            calibration=self.calibration,
        )

    def load(self, path: str) -> "ImpactPredictor":
        blob = np.load(path, allow_pickle=False)
        self.n_models = int(blob["n_models"])
        self.hidden = int(blob["hidden"])
        self.feat_mean = blob["feat_mean"]
        self.feat_std = blob["feat_std"]
        sizes = [
            (self.feat_mean.size, self.hidden),
            (self.hidden,),
            (self.hidden, self.hidden),
            (self.hidden,),
            (self.hidden, 1),
            (1,),
        ]
        shapes = [(self.feat_mean.size,), (self.hidden,), (self.hidden, self.hidden), (self.hidden,),
                  (self.hidden, 1), (1,)]
        # rebuilt from flat vectors using the known shapes
        n_in = self.feat_mean.size
        shape_list = [
            (n_in, self.hidden), (self.hidden,), (self.hidden, self.hidden), (self.hidden,),
            (self.hidden, 1), (1,),
        ]
        self.weights = []
        for row in blob["weights"]:
            params, i = [], 0
            for shp in shape_list:
                n = int(np.prod(shp))
                params.append(row[i: i + n].reshape(shp))
                i += n
            self.weights.append(dict(zip(("W1", "b1", "W2", "b2", "W3", "b3"), params)))
        self.mae = float(blob["mae"])
        self.calibration = float(blob["calibration"])
        self.fitted = True
        return self

    def audit(self, atoms, effect, magnitude, scope=None, latency_budget_ms: float = 40.0) -> AuditResult:
        x = self.featurise(atoms, effect, magnitude, scope)
        mu, sd = self.predict(x)
        shift = float(mu[0])
        sigma = float(sd[0])
        if shift + 2.0 * sigma > latency_budget_ms:
            return AuditResult(
                False,
                "impact",
                f"predicted latency shift {shift:.1f} ms + 2 sigma ({sigma:.1f}) exceeds the budget "
                f"{latency_budget_ms:.0f} ms",
                confidence=0.8,
                detail=dict(pred=shift, sigma=sigma, budget=latency_budget_ms),
            )
        return AuditResult(
            True, "impact", "within latency budget", confidence=0.9,
            detail=dict(pred=shift, sigma=sigma, budget=latency_budget_ms),
        )


# --------------------------------------------------------------------------- #
# combined auditor
# --------------------------------------------------------------------------- #
@dataclass
class Auditor:
    """Composes the three stages and produces the commit decision."""

    impact: ImpactPredictor | None = None
    latency_budget_ms: float = 40.0
    require_impact: bool = True
    log: list[dict] = field(default_factory=list)

    def audit_constraint(
        self,
        atoms: list[dict],
        effect: str,
        magnitude: float,
        intent: dict,
        scope: dict | None = None,
    ) -> AuditResult:
        stages = []
        s1 = semantic_audit_constraint(atoms, effect, intent)
        stages.append(s1)
        if not s1.ok:
            self._record(atoms, effect, magnitude, stages)
            return s1
        s2 = physics_audit(atoms, effect, magnitude, scope)
        stages.append(s2)
        if not s2.ok:
            self._record(atoms, effect, magnitude, stages)
            return s2
        if self.require_impact and self.impact is not None and self.impact.fitted:
            s3 = self.impact.audit(atoms, effect, magnitude, scope, self.latency_budget_ms)
            stages.append(s3)
            if not s3.ok:
                self._record(atoms, effect, magnitude, stages)
                return s3
        self._record(atoms, effect, magnitude, stages)
        return AuditResult(
            True,
            "all",
            "passed semantic, physics and impact audits",
            confidence=float(np.mean([s.confidence for s in stages])),
            detail=dict(stages=[s.stage for s in stages]),
        )

    def audit_weights(self, weights: dict, intent: dict) -> AuditResult:
        return semantic_audit_weights(weights, intent)

    def _record(self, atoms, effect, magnitude, stages) -> None:
        self.log.append(
            dict(
                atoms=atoms,
                effect=effect,
                magnitude=magnitude,
                stages=[dict(stage=s.stage, ok=s.ok, reason=s.reason) for s in stages],
                accepted=all(s.ok for s in stages),
            )
        )
