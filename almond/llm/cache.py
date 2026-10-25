"""Persistent, cross-process cache for validated LLM responses.

Two reasons:

1. **Cost and throttling.** Eight campaign processes re-asking the same
   translation question is what triggers provider throttling; a warm cache makes
   the repeated calls free.
2. **Reproducibility.** The forward-translation artifact is a *ground-side,
   per-intent* product: all seeds of a method should share the same audited
   weight profile, so that seed variance measures the learning component only.
   Caching by ``(call_type, payload, seed)`` makes exactly that happen, and the
   forensic hypotheses (whose payload embeds the seed's own failure trajectories)
   stay per-seed because their keys differ.

Only schema-validated responses are written, so the cache can never launder an
invalid artifact into the pipeline.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


class ResponseCache:
    def __init__(self, root: str | Path | None = None, enabled: bool = True):
        env = os.environ.get("ALMOND_LLM_CACHE", "1") != "0"
        self.enabled = enabled and env
        base = root or os.environ.get("ALMOND_LLM_CACHE_DIR") or "results/llm_cache"
        self.dir = Path(base)
        if self.enabled:
            self.dir.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def _path(self, key: str) -> Path:
        return self.dir / key[:2] / f"{key}.json"

    def get(self, key: str) -> dict | None:
        if not self.enabled:
            return None
        p = self._path(key)
        if not p.exists():
            self.misses += 1
            return None
        try:
            blob = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self.misses += 1
            return None
        self.hits += 1
        return blob.get("data")

    def put(self, key: str, record: dict) -> None:
        if not self.enabled:
            return
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, ensure_ascii=False, default=str), encoding="utf-8")
        os.replace(tmp, p)

    def stats(self) -> dict:
        return dict(enabled=self.enabled, hits=self.hits, misses=self.misses)
