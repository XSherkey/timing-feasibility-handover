"""Versioned operational knowledge graph (manuscript Sec. 3.2.4).

The graph is a typed document store plus a predicate index -- deliberately not a
free-form text log.  Records are append-only: a correction creates a new version
that links its predecessor, and retraction is recorded with a reason and a
timestamp rather than by deletion.  Retrieval is hybrid: a lexical/embedding
similarity over the natural-language reading, intersected with a hard scope
filter (latitude band, regime, traffic class, density) and a keyword check that
every predicate references an existing telemetry field.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np

#: telemetry fields a predicate may reference (must match the twin / env)
FIELD_NAMES = (
    "elevation_deg",
    "handover_advance_s",
    "isl_hop_count",
    "doppler_rate_hz_s",
    "latitude_abs_deg",
    "snr_db",
    "remaining_visibility_s",
    "plane_change",
    "path_available",
    "buffer_occupancy",
    "battery_state",
    "eclipse",
)

EXECUTABLE_EFFECTS = (
    "min_advance",
    "forbid_unrouted_target",
    "prefer_same_plane",
    "power_cap",
    "buffer_drain",
    # added after the recall experiment showed the grammar had no remedy for the
    # ``window_exceeded`` failure class (requested lead longer than the remaining
    # visibility), so those failures could never be mined into an accepted rule
    "cap_advance",
    "cap_advance_vis",
    "prefer_long_visibility",
)


@dataclass
class Constraint:
    id: str
    version: int
    atoms: list[dict]  # [{"field":..., "cmp":..., "value":...}, ...]
    effect: str
    magnitude: float
    nl_reading: str
    provenance: dict = field(default_factory=dict)
    confidence: float = 0.5
    scope_tags: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    predecessor: str | None = None
    retracted_at: float | None = None
    retraction_reason: str | None = None

    @property
    def active(self) -> bool:
        return self.retracted_at is None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["active"] = self.active
        return d

    @staticmethod
    def from_dict(d: dict) -> "Constraint":
        keys = {f for f in Constraint.__dataclass_fields__}
        return Constraint(**{k: v for k, v in d.items() if k in keys})

    def apply_mask(self, rows: Iterable[dict]) -> np.ndarray:
        rows = list(rows)
        m = np.ones(len(rows), dtype=bool)
        for a in self.atoms:
            vals = np.array([r.get(a["field"], np.nan) for r in rows], dtype=np.float64)
            with np.errstate(invalid="ignore"):
                op = a["cmp"]
                v = a["value"]
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


class KnowledgeGraph:
    """Append-only, versioned constraint store with hybrid retrieval."""

    def __init__(self, path: str | Path | None = None, embedding_dim: int = 256):
        self.path = Path(path) if path else None
        self.constraints: list[Constraint] = []
        self.history: list[dict] = []
        self.embedding_dim = embedding_dim
        self._version_counter: dict[str, int] = {}
        if self.path and self.path.exists():
            self.load()

    # -- persistence --------------------------------------------------- #
    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                dict(
                    constraints=[c.to_dict() for c in self.constraints],
                    history=self.history,
                    versions=self._version_counter,
                ),
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(self) -> None:
        blob = json.loads(self.path.read_text(encoding="utf-8"))
        self.constraints = [Constraint.from_dict(d) for d in blob.get("constraints", [])]
        self.history = blob.get("history", [])
        self._version_counter = blob.get("versions", {})

    # -- writing ------------------------------------------------------- #
    def commit(
        self,
        atoms: list[dict],
        effect: str,
        magnitude: float,
        nl_reading: str,
        *,
        provenance: dict | None = None,
        confidence: float = 0.5,
        scope_tags: dict | None = None,
        replaces: str | None = None,
        cid: str | None = None,
    ) -> Constraint:
        if effect not in EXECUTABLE_EFFECTS:
            raise ValueError(f"effect '{effect}' is not executable")
        for a in atoms:
            if a["field"] not in FIELD_NAMES:
                raise ValueError(f"unknown telemetry field '{a['field']}'")
        if replaces:
            base = self.get(replaces)
            cid = cid or base.id
            version = (base.version or 0) + 1
        else:
            cid = cid or f"k{len(self.constraints) + 1:04d}"
            version = 1
        self._version_counter[cid] = version
        c = Constraint(
            id=cid,
            version=version,
            atoms=list(atoms),
            effect=effect,
            magnitude=float(magnitude),
            nl_reading=nl_reading,
            provenance=provenance or {},
            confidence=float(confidence),
            scope_tags=scope_tags or {},
            predecessor=replaces,
        )
        self.constraints.append(c)
        self.history.append(dict(event="commit", id=cid, version=version, ts=c.created_at))
        return c

    def retract(self, cid: str, reason: str) -> None:
        c = self.get(cid)
        c.retracted_at = time.time()
        c.retraction_reason = reason
        self.history.append(dict(event="retract", id=cid, reason=reason, ts=c.retracted_at))

    def get(self, cid: str) -> Constraint:
        for c in reversed(self.constraints):
            if c.id == cid:
                return c
        raise KeyError(cid)

    # -- retrieval ----------------------------------------------------- #
    def active(self) -> list[Constraint]:
        return [c for c in self.constraints if c.active]

    def _embed(self, text: str) -> np.ndarray:
        """Hashing bag-of-words embedding (deterministic, dependency-free)."""
        v = np.zeros(self.embedding_dim, dtype=np.float64)
        for tok in text.lower().replace(",", " ").replace(".", " ").split():
            h = hash(tok) % self.embedding_dim
            v[h] += 1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def retrieve(
        self,
        query: str,
        scope: dict | None = None,
        top_k: int = 8,
        min_confidence: float = 0.0,
    ) -> list[tuple[Constraint, float]]:
        scope = scope or {}
        q = self._embed(query)
        out = []
        for c in self.active():
            if c.confidence < min_confidence:
                continue
            if not _scope_compatible(scope, c.scope_tags):
                continue
            if not all(a["field"] in FIELD_NAMES for a in c.atoms):
                continue
            sim = float(np.dot(q, self._embed(c.nl_reading)))
            out.append((c, sim))
        out.sort(key=lambda x: -x[1])
        return out[:top_k]

    def context_bundle(self, query: str, scope: dict | None = None) -> dict:
        hits = self.retrieve(query, scope)
        return dict(
            constraints=[
                dict(
                    id=c.id,
                    reading=c.nl_reading,
                    similarity=round(sim, 4),
                    confidence=c.confidence,
                    scope=c.scope_tags,
                )
                for c, sim in hits
            ],
            n_active=len(self.active()),
            scope=scope or {},
        )

    def stats(self) -> dict:
        return dict(
            n_records=len(self.constraints),
            n_active=len(self.active()),
            n_retracted=sum(1 for c in self.constraints if not c.active),
            effects={e: sum(1 for c in self.active() if c.effect == e) for e in EXECUTABLE_EFFECTS},
        )


def _scope_compatible(query: dict, scope: dict) -> bool:
    """Hard scope filter: a rule may not be retrieved outside its scope tags."""
    for key, allowed in scope.items():
        if key in query and query[key] is not None:
            if isinstance(allowed, (list, tuple, set)):
                if query[key] not in allowed:
                    return False
            elif isinstance(allowed, str):
                if str(query[key]) != allowed:
                    return False
    return True
