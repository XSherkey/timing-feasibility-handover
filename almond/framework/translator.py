"""Forward translation: natural-language intent -> audited reward profile.

Implements manuscript Sec. 3.2.1 and Algorithm 1 lines 1-6: retrieve a context
bundle from the knowledge graph, ask the LLM for a weight profile over the fixed
normalized sub-rewards, audit the draft, and re-prompt with a clarifying
question when the audit fails.  If the audit budget is exhausted the request is
escalated and no unvalidated reward is ever used for training.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np

from .auditor import Auditor, AuditResult
from .kg import KnowledgeGraph

ENV_DESCRIPTION = """\
LEO satellite handover control twin.
State: 14 validated telemetry fields of the serving link plus a K=8 candidate shortlist
(elevation, SNR, ISL hop count to the feeder gateway, capacity, same-plane flag, path flag).
Action: target satellite among the shortlist (or keep) and a preparation lead time in
[4, 24] s for make-before-break dual homing.
Dynamics: SGP4-propagated 350-satellite constellation; cross-plane ISL links are disabled
above 70 deg latitude, so a cross-plane handover above the seam must rebuild its feeder route;
session continuity requires the preparation to finish before the serving link dies.
"""

INTENT_TEMPLATES = {
    "reliability_first": {
        "name": "uninterrupted Arctic video",
        "priorities": {"reliability": "highest", "latency": "low", "power": "medium"},
        "requirements": [
            "no session interruption for video above 70 N",
            "handover must complete before the serving link is lost",
            "stay inside the on-board power budget",
        ],
    },
    "latency_first": {
        "name": "interactive emergency service",
        "priorities": {"reliability": "high", "latency": "critical", "power": "low"},
        "requirements": [
            "95th percentile one-way latency below the 150 ms SLA",
            "session continuity must not regress below the service floor",
        ],
    },
    "power_first": {
        "name": "eclipse-season battery preservation",
        "priorities": {"reliability": "medium", "latency": "medium", "power": "critical"},
        "requirements": [
            "minimise transmit power and dual-homing during eclipse",
            "keep reliability above the availability objective",
        ],
    },
    "balanced": {
        "name": "mixed regional service",
        "priorities": {"reliability": "high", "latency": "medium", "power": "medium"},
        "requirements": [
            "balance reliability, latency and power across regions",
        ],
    },
}

#: the twelve intent statements of the human-effort protocol (Sec. 4.5)
EFFORT_TASKS = [
    ("reliability_first", "Alert"),
    ("reliability_first", "Longyearbyen"),
    ("reliability_first", "Resolute"),
    ("reliability_first", "SachsHarbour"),
    ("latency_first", "Tromso"),
    ("latency_first", "Edinburgh"),
    ("latency_first", "Nairobi"),
    ("power_first", "Alert"),
    ("power_first", "Kiruna"),
    ("power_first", "Singapore"),
    ("balanced", "Longyearbyen"),
    ("balanced", "Rome"),
]


@dataclass
class Translation:
    weights: dict
    reward: AuditResult
    attempts: int
    escalated: bool
    context: dict
    raw: dict = field(default_factory=dict)


class ForwardTranslator:
    def __init__(self, llm, kg: KnowledgeGraph, auditor: Auditor, budget: int = 5, env_desc: str = ENV_DESCRIPTION):
        self.llm = llm
        self.kg = kg
        self.auditor = auditor
        self.budget = budget
        self.env_desc = env_desc
        self.log: list[dict] = []

    def translate(
        self,
        intent: dict,
        scope: dict | None = None,
        seed: int = 0,
        use_memory: bool = True,
    ) -> Translation:
        query = intent.get("name", "") + " " + " ".join(intent.get("requirements", []))
        context = self.kg.context_bundle(query, scope) if use_memory else dict(constraints=[], n_active=0, scope=scope or {})
        history = []
        last_audit = AuditResult(False, "semantic", "no attempt")
        weights = dict(w_rel=1 / 3, w_lat=1 / 3, w_pow=1 / 3)
        for attempt in range(self.budget):
            payload = dict(
                intent=intent,
                env_desc=self.env_desc,
                task_short_desc="LEO handover control with a 350-satellite digital twin",
                knowledge_context=context,
                prior_critique=history,
                clarification=(
                    last_audit.question if attempt and last_audit.question else ""
                ),
            )
            out = self.llm("forward_translate", payload, seed=seed + attempt)
            w = out.get("weights", {})
            weights = dict(
                w_rel=float(np.clip(w.get("w_rel", 1 / 3), 0.0, 1.0)),
                w_lat=float(np.clip(w.get("w_lat", 1 / 3), 0.0, 1.0)),
                w_pow=float(np.clip(w.get("w_pow", 1 / 3), 0.0, 1.0)),
            )
            tot = sum(weights.values()) or 1.0
            weights = {k: v / tot for k, v in weights.items()}
            audit = self.auditor.audit_weights(
                dict(
                    reliability=weights["w_rel"],
                    latency=weights["w_lat"],
                    power=weights["w_pow"],
                ),
                intent,
            )
            self.log.append(
                dict(attempt=attempt, weights=weights, ok=audit.ok, reason=audit.reason, question=audit.question)
            )
            last_audit = audit
            if audit.ok:
                return Translation(
                    weights=weights,
                    reward=audit,
                    attempts=attempt + 1,
                    escalated=False,
                    context=context,
                    raw=out,
                )
            history.append(dict(reason=audit.reason, question=audit.question, weights=weights))
        return Translation(
            weights=weights,
            reward=last_audit,
            attempts=self.budget,
            escalated=True,
            context=context,
            raw={},
        )
