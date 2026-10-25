"""Reverse forensics: from failing trajectories to a validated constraint.

Implements the four steps of manuscript Sec. 3.2.2 with strict separation of the
discovery, validation and test trajectory sets:

1. **Failure-episode sampling (discovery set).**  The worst 5% of handover
   attempts by outcome in the violating region are encoded as temporal
   narratives.
2. **Hypothesis generation.**  The LLM (or its surrogate) proposes candidate
   predicates over the declared telemetry grammar.  Hypotheses are generated
   *only* from the discovery set.
3. **Counterfactual validation (validation set).**  Each audited candidate is
   replayed in the twin on a validation set drawn from disjoint time intervals
   and traffic realisations.  Acceptance requires ``delta >= delta_min`` and no
   latency-budget violation.
4. **Independent test and commitment.**  Accepted rules are replayed on a
   held-out test set; only if the improvement replicates are they committed to
   the knowledge graph (with provenance, confidence and scope tags).
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field

import numpy as np

from ..llm.surrogate import EFFECT_GRAMMAR, FIELD_SCHEMA
from .auditor import Auditor
from .kg import Constraint, KnowledgeGraph
from .shield import compile_constraints


@dataclass
class SplitConfig:
    """Time/scope splits of the twin horizon (fractions of ``n_time``)."""

    train: tuple[float, float] = (0.0, 0.60)
    validation: tuple[float, float] = (0.65, 0.75)
    test: tuple[float, float] = (0.82, 0.95)
    test_traffic: tuple[float, ...] = (0.5, 1.0, 2.0)

    def indices(self, n_time: int, which: str, episode_steps: int) -> tuple[int, int]:
        a, b = getattr(self, which)
        return int(a * n_time), max(int(a * n_time) + episode_steps + 2, int(b * n_time))


@dataclass
class ForensicResult:
    hypothesis: dict | None
    constraint: Constraint | None
    delta_val: float
    delta_test: float
    accepted: bool
    stage_log: list[dict] = field(default_factory=list)
    n_candidates: int = 0


# --------------------------------------------------------------------------- #
# narratives
# --------------------------------------------------------------------------- #
def episodes_to_narratives(rows: list[dict], per_line: int = 4, enriched: bool = True) -> list[str]:
    """Encode failure attempts as temporal narratives the LLM can reason over.

    With ``enriched`` the narrative carries the gateway error code (``cause``) and
    spells out route availability instead of exposing the ``-1`` hop sentinel,
    which earlier caused the model to propose rules such as
    ``isl_hop_count == -1`` — a predicate over an encoding artefact rather than
    over a telemetry field.
    """
    out = []
    for i in range(0, len(rows), per_line):
        chunk = rows[i: i + per_line]
        lines = []
        for r in chunk:
            hops = int(r["isl_hop_count"])
            route = "routable" if hops >= 0 and r.get("path_available", 1.0) > 0 else "NO ROUTE"
            hop_txt = f"{hops}" if hops >= 0 else "n/a"
            base = (
                f"at t={r['step'] * 10}s on {r['site']} (lat {r['lat']:.0f} deg, satellite lat "
                f"{r.get('satellite_latitude_deg', float('nan')):.0f} deg), elevation "
                f"{r['elevation_deg']:.1f} deg, handover advance {r['handover_advance_s']:.0f} s, "
                f"ISL hops {hop_txt} ({route}), plane change {int(r.get('plane_change', 0))}, "
                f"remaining visibility {r['remaining_visibility_s']:.0f} s, acquisition took "
                f"{r.get('t_setup_s', float('nan')):.1f} s"
            )
            if enriched:
                cause = r.get("cause", "unknown")
                base += f", feeder load {r.get('buffer_occupancy', float('nan')):.2f} -> session lost (error code: {cause})"
            else:
                base += " -> session lost"
            lines.append(base)
        out.append(" | ".join(lines))
    return out


# --------------------------------------------------------------------------- #
# replay
# --------------------------------------------------------------------------- #
def replay_rule(
    env,
    policy_fn,
    constraint_or_none: Constraint | None,
    episodes: int,
    t_range: tuple[int, int],
    deterministic: bool = True,
) -> dict:
    """Replay the frozen policy with and without the constraint on one split.

    ``policy_fn`` maps ``(obs, x, adj)`` to ``(target, advance)``.  The actor is
    never updated, so any difference is attributable to the constraint alone.
    """
    shield = compile_constraints([constraint_or_none], env.cfg) if constraint_or_none else None
    rows, attempts = [], []
    for _ in range(episodes):
        obs = env.reset(t_range=t_range)
        for _s in range(env.cfg.episode_steps):
            x, adj = env.candidate_graph()
            at, aa = policy_fn(obs, x, adj, deterministic)
            obs, rew, done, info = env.step(at, aa, shield=shield, record=True)
        st = env.episode_stats()
        lat = env.site_lat[env.site]
        for i in range(env.batch):
            rows.append(
                dict(
                    lat=float(lat[i]),
                    hsr=float(st["hsr"][i]),
                    attempts=int(st["attempts"][i]),
                    successes=int(st["successes"][i]),
                    lat_p95=float(st["lat_p95"][i]) if not np.isnan(st["lat_p95"][i]) else float("nan"),
                )
            )
        attempts.extend(env.attempt_log)
    return dict(rows=rows, attempts=attempts)


def score(rows: list[dict], region: str = "arctic") -> dict:
    """Aggregate HSR (attempt-weighted) over a region."""
    if region == "arctic":
        sel = [r for r in rows if abs(r["lat"]) > 70]
    elif region == "subarctic":
        sel = [r for r in rows if 65 <= abs(r["lat"]) <= 70]
    elif region == "midlat":
        sel = [r for r in rows if 30 <= abs(r["lat"]) < 65]
    elif region == "equatorial":
        sel = [r for r in rows if abs(r["lat"]) < 30]
    else:
        sel = rows
    if not sel:
        return dict(hsr=float("nan"), attempts=0, lat_p95=float("nan"))
    att = sum(r["attempts"] for r in sel)
    suc = sum(r["successes"] for r in sel)
    lats = [r["lat_p95"] for r in sel if not np.isnan(r["lat_p95"])]
    return dict(
        hsr=suc / att if att else float("nan"),
        attempts=att,
        lat_p95=float(np.median(lats)) if lats else float("nan"),
    )


# --------------------------------------------------------------------------- #
# the forensic loop
# --------------------------------------------------------------------------- #
class ForensicEngine:
    def __init__(
        self,
        twin,
        env,
        policy_fn,
        llm,
        kg: KnowledgeGraph,
        auditor: Auditor,
        splits: SplitConfig | None = None,
        delta_min: float = 0.05,
        region: str = "arctic",
        scope_tags: dict | None = None,
        log: list[dict] | None = None,
        magnitude_override: float | None = None,
    ):
        self.twin = twin
        self.env = env
        self.policy_fn = policy_fn
        self.llm = llm
        self.kg = kg
        self.auditor = auditor
        self.splits = splits or SplitConfig()
        self.delta_min = delta_min
        self.region = region
        self.scope_tags = scope_tags or dict(polar=True, regime="arctic", traffic_class="video", density="ref350")
        self.stage_log = log if log is not None else []
        self.n_candidates = 0
        #: probe-calibrated magnitude (PCS).  The LLM proposes the *condition*; this
        #: number comes from an active de-censoring sweep, so a shifted physics
        #: changes the threshold even when the failure narrative does not.
        self.magnitude_override = magnitude_override

    def _split(self, which: str) -> tuple[int, int]:
        return self.splits.indices(self.twin.n_time, which, self.env.cfg.episode_steps)

    def discovery_rows(
        self,
        episodes: int = 4,
        worst_frac: float = 0.05,
        mode: str = "enriched",
        per_cause: int = 8,
    ) -> list[dict]:
        """Collect failing attempts on the discovery split.

        ``mode="legacy"`` reproduces the earlier selection (sort by route
        availability then by acquisition time), which over-sampled the ``no_route``
        class and is the reason only routing/timing rules were ever mined.
        ``mode="enriched"`` stratifies the discovery set by the gateway error code
        so every failure class the twin can produce is represented, which is what
        raises forensic recall.
        """
        res = replay_rule(self.env, self.policy_fn, None, episodes, self._split("train"))
        fails = [r for r in res["attempts"] if not r["success"] and abs(r["lat"]) > 60]
        if not fails:
            fails = [r for r in res["attempts"] if not r["success"]]
        if not fails:
            return []
        if mode == "legacy":
            fails.sort(key=lambda r: (r.get("path_available", 1.0), -r.get("t_setup_s", 0.0)))
            k = max(5, int(len(fails) * worst_frac / 0.05))
            return fails[:k]
        # ---- stratified by error code ------------------------------------- #
        by_cause: dict[str, list[dict]] = {}
        for r in fails:
            by_cause.setdefault(str(r.get("cause", "unknown")), []).append(r)
        picked: list[dict] = []
        for cause, rows in sorted(by_cause.items()):
            # within a class keep the most severe cases: longest acquisition and
            # least remaining visibility, but always keep a few mild ones so the
            # model can see the boundary rather than only the extreme tail
            rows = sorted(rows, key=lambda r: (-r.get("t_setup_s", 0.0), r.get("remaining_visibility_s", 0.0)))
            head = rows[: max(2, per_cause - 2)]
            tail = rows[len(rows) // 2: len(rows) // 2 + 2] if len(rows) > per_cause else []
            picked.extend(head + tail)
        return picked

    def run(
        self,
        max_attempts: int = 1,
        validate_episodes: int = 3,
        test_episodes: int = 4,
        policy_id: str = "pi_almon",
        discovery_mode: str = "enriched",
    ) -> ForensicResult:
        disc = self.discovery_rows(mode=discovery_mode)
        if not disc:
            self._log(dict(event="no_failures"))
            return ForensicResult(None, None, 0.0, 0.0, False, self.stage_log)
        hist: dict[str, int] = {}
        for r in disc:
            hist[str(r.get("cause", "unknown"))] = hist.get(str(r.get("cause", "unknown")), 0) + 1
        self._log(dict(event="discovery", mode=discovery_mode, rows=len(disc), causes=hist))

        # ---- step 1: baseline on validation (frozen actor) --------------- #
        base_val = replay_rule(self.env, self.policy_fn, None, validate_episodes, self._split("validation"))
        base_val_score = score(base_val["rows"], self.region)
        self._log(dict(event="baseline", split="validation", **base_val_score))

        payload = dict(
            policy_id=policy_id,
            region_tags=self.scope_tags,
            kpi="hsr",
            kpi_value=base_val_score["hsr"],
            threshold=0.85,
            failure_narratives=episodes_to_narratives(disc, enriched=(discovery_mode == "enriched")),
            failure_rows=disc,
            success_rows=[r for r in base_val["attempts"] if r["success"]],
            field_schema=FIELD_SCHEMA,
            effect_grammar=EFFECT_GRAMMAR,
        )

        best: ForensicResult | None = None
        seen: list[ForensicResult] = []
        for attempt in range(max_attempts):
            hyp = self.llm("forensic_hypothesis", payload, seed=attempt)
            cands = hyp.get("hypotheses", [])
            self.n_candidates += len(cands)
            for h in cands:
                atoms = h["if"]["all"]
                eff = h["then"]
                if self.magnitude_override is not None:
                    eff = dict(eff, magnitude=float(self.magnitude_override))
                    self._log(dict(event="magnitude_override", magnitude=float(self.magnitude_override)))
                audit = self.auditor.audit_constraint(
                    atoms, eff["effect"], eff["magnitude"], payload.setdefault("intent", {}), self.scope_tags
                )
                self._log(
                    dict(
                        event="audit",
                        atoms=atoms,
                        effect=eff["effect"],
                        magnitude=eff["magnitude"],
                        ok=audit.ok,
                        stage=audit.stage,
                        reason=audit.reason,
                    )
                )
                if not audit.ok:
                    continue
                c = Constraint(
                    id="cand",
                    version=1,
                    atoms=atoms,
                    effect=eff["effect"],
                    magnitude=float(eff["magnitude"]),
                    nl_reading=h.get("rationale", json.dumps(h)),
                    scope_tags=dict(self.scope_tags),
                )
                with_c = replay_rule(
                    self.env, self.policy_fn, c, validate_episodes, self._split("validation")
                )
                s = score(with_c["rows"], self.region)
                delta = s["hsr"] - base_val_score["hsr"]
                self._log(dict(event="validation", delta=delta, hsr=s["hsr"], effect=c.effect))
                if delta < self.delta_min:
                    continue
                if not np.isnan(s["lat_p95"]) and s["lat_p95"] > 60.0:
                    self._log(dict(event="latency_violation", lat_p95=s["lat_p95"]))
                    continue
                # ---- step 4: independent test ---------------------------- #
                deltas_test = []
                for mult in self.splits.test_traffic:
                    old = self.env.cfg.traffic_scale
                    self.env.cfg.traffic_scale = mult
                    base_t = replay_rule(self.env, self.policy_fn, None, test_episodes, self._split("test"))
                    with_t = replay_rule(self.env, self.policy_fn, c, test_episodes, self._split("test"))
                    self.env.cfg.traffic_scale = old
                    d = score(with_t["rows"], self.region)["hsr"] - score(base_t["rows"], self.region)["hsr"]
                    deltas_test.append(d)
                d_test = float(np.mean(deltas_test))
                self._log(dict(event="test", delta_test=d_test, per_multiplier=deltas_test))
                res = ForensicResult(h, c, delta, d_test, d_test >= self.delta_min, self.stage_log, self.n_candidates)
                seen.append(res)
                if best is None or res.delta_test > best.delta_test:
                    best = res
            if best is not None and best.accepted:
                break

        if best is None or not best.accepted:
            return best or ForensicResult(
                None, None, 0.0, 0.0, False, self.stage_log, self.n_candidates
            )

        # ---- commit -------------------------------------------------------- #
        # With the gate enabled only the best validated candidate is committed.  With
        # the gate disabled (``delta_min < 0``) every proposal that passed the auditor
        # and the test is committed, which is what "accept what the model says" means;
        # committing only the best would silently keep the gate's selection step.
        to_commit = [best] if self.delta_min >= 0.0 else [r for r in seen if r.constraint is not None]
        for res in to_commit:
            c = self.kg.commit(
                atoms=res.constraint.atoms,
                effect=res.constraint.effect,
                magnitude=res.constraint.magnitude,
                nl_reading=res.constraint.nl_reading,
                provenance=dict(
                    delta_val=res.delta_val,
                    delta_test=res.delta_test,
                    discovery_rows=len(disc),
                    replay_config=dict(
                        validate_episodes=validate_episodes,
                        test_episodes=test_episodes,
                        traffic_multipliers=list(self.splits.test_traffic),
                    ),
                    hypothesis=res.hypothesis,
                ),
                confidence=float(np.clip(0.5 + 0.5 * min(res.delta_test / 0.3, 1.0), 0.5, 0.99)),
                scope_tags=dict(self.scope_tags),
            )
            res.constraint = c
            self._log(dict(event="commit", id=c.id, effect=c.effect, magnitude=c.magnitude))
        best.constraint = to_commit[-1].constraint
        self.kg.save()
        return best

    def _log(self, rec: dict) -> None:
        self.stage_log.append(rec)
