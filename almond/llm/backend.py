"""Pluggable LLM access layer.

Three backends implement the same ``complete`` contract:

``OpenAICompatBackend``
    A real chat-completions client (any OpenAI-compatible endpoint: vLLM,
    llama.cpp server, SGLang, a hosted API).  Selected automatically when
    ``ALMOND_LLM_BASE_URL`` is set.

``SurrogateBackend``
    A deterministic *reasoning surrogate*.  It implements the same
    prompt/response contract as the real prompts of Appendix A but computes its
    answer symbolically (threshold search over the telemetry grammar, weight
    derivation from the stated priority order, grammar-constrained topology
    sampling).  This is what makes the reproduction runnable on a workstation
    without a hosted model, and every experiment that uses it is labelled
    ``llm_backend=surrogate`` in the result files.

``ReplayBackend``
    Replays a previously logged call sequence, for exact reproducibility of a
    run whose responses were captured with a real model.

Every call is logged with the rendered prompt, the raw response, the parsed
JSON, the sampling parameters, token counts and latency, so the reproducibility
and stability claims of the manuscript (Sec. 4.6) are auditable.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

import numpy as np

CALL_TYPES = (
    "forward_translate",
    "forensic_hypothesis",
    "topology_seed",
    "topology_mutation",
    "topology_crossover",
    "population_critique",
)

#: decoding settings per call type (manuscript Sec. 3.5.1)
DECODING = {
    "forward_translate": dict(temperature=0.2, top_p=0.9),
    "forensic_hypothesis": dict(temperature=0.2, top_p=0.9),
    "topology_seed": dict(temperature=0.7, top_p=0.9),
    "topology_mutation": dict(temperature=0.7, top_p=0.9),
    "topology_crossover": dict(temperature=0.7, top_p=0.9),
    "population_critique": dict(temperature=0.7, top_p=0.9),
}
#: Completion budget.  A reasoning-capable endpoint bills its reasoning tokens
#: against this same budget: with 2048 the long forensic prompts could consume
#: the whole budget on reasoning and return *empty* content with
#: ``finish_reason == "length"``.  The budget therefore covers reasoning + JSON.
MAX_TOKENS = int(os.environ.get("ALMOND_LLM_MAX_TOKENS", "8192"))
#: ceiling used when an empty (truncated) answer forces a larger retry
MAX_TOKENS_CEILING = int(os.environ.get("ALMOND_LLM_MAX_TOKENS_CEILING", "16384"))


class EmptyCompletion(RuntimeError):
    """The endpoint returned no content (budget exhausted on reasoning tokens)."""


@dataclass
class LLMResponse:
    text: str
    data: dict
    call_type: str
    seed: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    latency_s: float = 0.0
    attempts: int = 1
    backend: str = "surrogate"
    model: str = "surrogate"


class LLMBackend(Protocol):  # pragma: no cover - structural typing only
    name: str

    def complete(self, call_type: str, payload: dict, seed: int = 0) -> LLMResponse:
        ...


# --------------------------------------------------------------------------- #
# logging
# --------------------------------------------------------------------------- #
class LLMLog:
    """Append-only JSONL log of every call (prompts and responses)."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.records: list[dict] = []
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, rec: dict) -> None:
        self.records.append(rec)
        if self.path:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    def summary(self) -> dict:
        n = len(self.records)
        if not n:
            return dict(calls=0)
        toks_in = sum(r.get("tokens_in", 0) for r in self.records)
        toks_out = sum(r.get("tokens_out", 0) for r in self.records)
        lat = sum(r.get("latency_s", 0.0) for r in self.records)
        return dict(
            calls=n,
            tokens_in=toks_in,
            tokens_out=toks_out,
            latency_s=lat,
            schema_failures=sum(1 for r in self.records if not r.get("schema_ok", True)),
            by_type={t: sum(1 for r in self.records if r["call_type"] == t) for t in CALL_TYPES},
        )


# --------------------------------------------------------------------------- #
# real backend
# --------------------------------------------------------------------------- #
class OpenAICompatBackend:
    """Chat-completions client for any OpenAI-compatible endpoint.

    Works with a self-hosted server (vLLM / llama.cpp / SGLang) and with hosted
    APIs such as DeepSeek.  ``ALMOND_LLM_BASE_URL`` / ``ALMOND_LLM_API_KEY`` /
    ``ALMOND_LLM_MODEL`` configure it; ``ALMOND_LLM_JSON_MODE=0`` disables the
    ``response_format`` hint for servers that do not support it.
    """

    name = "openai_compat"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_s: float = 90.0,
        max_retries: int = 4,
        json_mode: bool | None = None,
    ):
        self.base_url = (base_url or os.environ.get("ALMOND_LLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("ALMOND_LLM_API_KEY", "none")
        self.model = model or os.environ.get("ALMOND_LLM_MODEL", "deepseek-flash")
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        if json_mode is None:
            json_mode = os.environ.get("ALMOND_LLM_JSON_MODE", "1") != "0"
        self.json_mode = json_mode
        self._sem = None
        if not self.base_url:
            raise ValueError("ALMOND_LLM_BASE_URL is not set")

    def _post(self, payload: dict) -> dict:
        from .semaphore import FileSemaphore

        if self._sem is None:
            self._sem = FileSemaphore(slots=int(os.environ.get("ALMOND_LLM_CONCURRENCY", "3")))
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with self._sem.acquire():
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                return json.loads(resp.read().decode())

    def complete(self, call_type: str, payload: dict, seed: int = 0, repair_note: str = "") -> LLMResponse:
        from .prompts import render_prompt

        prompt = render_prompt(call_type, payload)
        dec = DECODING[call_type]
        user = prompt["user"]
        if repair_note:
            user += (
                "\n\n## Repair required\nYour previous answer did not satisfy the required schema: "
                f"{repair_note}\nReturn the corrected JSON only."
            )
        body = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": user},
            ],
            temperature=dec["temperature"],
            top_p=dec["top_p"],
            max_tokens=MAX_TOKENS,
            seed=seed,
        )
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        last_err = None
        budget = MAX_TOKENS
        for attempt in range(1, self.max_retries + 1):
            t0 = time.time()
            body["max_tokens"] = budget
            try:
                out = self._post(body)
                text = out["choices"][0]["message"]["content"] or ""
                finish = out["choices"][0].get("finish_reason")
                usage = out.get("usage", {})
                if not text.strip():
                    # reasoning consumed the whole budget: retry with more room
                    # instead of burning the remaining attempts on the same limit
                    if finish == "length":
                        budget = min(budget * 2, MAX_TOKENS_CEILING)
                    raise EmptyCompletion(
                        f"empty content (finish_reason={finish}, completion_tokens="
                        f"{usage.get('completion_tokens')}); budget now {budget}"
                    )
                data = json.loads(text)
                return LLMResponse(
                    text=text,
                    data=data,
                    call_type=call_type,
                    seed=seed,
                    tokens_in=int(usage.get("prompt_tokens", 0)),
                    tokens_out=int(usage.get("completion_tokens", 0)),
                    latency_s=time.time() - t0,
                    attempts=attempt,
                    backend=self.name,
                    model=self.model,
                )
            except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError,
                    EmptyCompletion) as exc:
                last_err = exc
                time.sleep(min(2.0 * attempt, 8.0))
        raise RuntimeError(f"LLM call failed after {self.max_retries} retries: {last_err}")


# --------------------------------------------------------------------------- #
# deterministic surrogate (fallback when no real endpoint is configured)
# --------------------------------------------------------------------------- #
class SurrogateBackend:
    """Deterministic reasoning surrogate implementing the prompt contract.

    The surrogate is *not* a language model.  Each call type is answered by a
    symbolic routine that consumes exactly the structured payload a real prompt
    would receive and returns exactly the JSON schema Appendix A specifies:

    * ``forward_translate`` - maps the stated priority order onto a weight
      profile in the validated simplex, with sampling noise proportional to the
      configured decoding temperature;
    * ``forensic_hypothesis`` - runs a bounded threshold search over the
      telemetry grammar to find the predicate that best separates failing from
      successful handover attempts in the discovery set;
    * the topology call types - sample from the grammar with
      regime-conditioned priors.

    Sampling is seeded, so results are reproducible, while repeated calls with
    different seeds exhibit the stochasticity the stability experiment measures.
    """

    name = "surrogate"

    def __init__(self, record_decisions: bool = True):
        self.record_decisions = record_decisions

    def complete(self, call_type: str, payload: dict, seed: int = 0, repair_note: str = "") -> LLMResponse:
        from .prompts import render_prompt
        from . import surrogate as S

        t0 = time.time()
        prompt = render_prompt(call_type, payload)
        rng = np.random.default_rng(seed)
        fn = {
            "forward_translate": S.forward_translate,
            "forensic_hypothesis": S.forensic_hypothesis,
            "topology_seed": S.topology_seed,
            "topology_mutation": S.topology_mutation,
            "topology_crossover": S.topology_crossover,
            "population_critique": S.population_critique,
        }[call_type]
        data = fn(payload, rng)
        text = json.dumps(data, ensure_ascii=False)
        return LLMResponse(
            text=text,
            data=data,
            call_type=call_type,
            seed=seed,
            tokens_in=len(prompt["user"]) // 4,
            tokens_out=len(text) // 4,
            latency_s=time.time() - t0,
            attempts=1,
            backend=self.name,
            model="surrogate",
        )


class ReplayBackend:
    """Replays logged responses for bit-exact reproduction."""

    name = "replay"

    def __init__(self, path: str | Path):
        recs = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
        self.by_key: dict[str, list[dict]] = {}
        for r in recs:
            self.by_key.setdefault(r["cache_key"], []).append(r)
        self.cursor: dict[str, int] = {}

    def complete(self, call_type: str, payload: dict, seed: int = 0, repair_note: str = "") -> LLMResponse:
        key = cache_key(call_type, payload, seed)
        items = self.by_key.get(key) or next(iter(self.by_key.values()))
        i = self.cursor.get(key, 0) % len(items)
        self.cursor[key] = i + 1
        r = items[i]
        return LLMResponse(
            text=r["text"],
            data=r["data"],
            call_type=call_type,
            seed=seed,
            tokens_in=r.get("tokens_in", 0),
            tokens_out=r.get("tokens_out", 0),
            backend=self.name,
            model=r.get("model", "replay"),
        )


def cache_key(call_type: str, payload: dict, seed: int, model: str = "default") -> str:
    """Cache identity: call type, payload, seed **and** the serving model.

    The model must be part of the key, otherwise a run against a second endpoint
    would silently reuse the first model's audited artifacts and the cross-model
    comparison would be meaningless.
    """
    blob = json.dumps(
        dict(call_type=call_type, payload=payload, seed=seed, model=model),
        sort_keys=True, default=str,
    )
    return hashlib.sha1(blob.encode()).hexdigest()


# --------------------------------------------------------------------------- #
# facade
# --------------------------------------------------------------------------- #
class LLMSchemaError(RuntimeError):
    """Every attempt produced an artifact that violates the schema."""


class LLMClient:
    """Front door used by the framework; validates, repairs, logs and retries.

    A response that violates the call contract is *re-requested* with a repair
    note appended to the prompt rather than heuristically patched; the number of
    extra attempts is recorded, which is the metric the manuscript's stability
    experiment reports as "parse/grammar failures that trigger safe retries".
    """

    def __init__(
        self,
        backend: LLMBackend | None = None,
        log: LLMLog | None = None,
        max_retries: int = 4,
        validate: bool = True,
    ):
        if backend is None:
            backend = _default_backend()
        self.backend = backend
        self.log = log or LLMLog()
        self.max_retries = max_retries
        self.validate = validate
        self.calls = 0
        self.schema_retries = 0
        self.exhausted = 0
        self._cache = None

    def __call__(self, call_type: str, payload: dict, seed: int = 0) -> dict:
        from .cache import ResponseCache
        from .schema import normalise, validate_response

        key = cache_key(
            call_type, payload, seed,
            model=f"{getattr(self.backend, 'name', '?')}:{getattr(self.backend, 'model', '?')}",
        )
        if self._cache is None:
            self._cache = ResponseCache()
        cached = self._cache.get(key)
        if cached is not None:
            self.calls += 1
            if self.log is not None:
                self.log.add(
                    dict(
                        call_type=call_type, seed=seed, cache_key=key,
                        backend=getattr(self.backend, "name", "cache"),
                        model=getattr(self.backend, "model", "cache"),
                        schema_ok=True, schema_problem="", from_cache=True,
                        data=cached, text=json.dumps(cached), tokens_in=0, tokens_out=0,
                        latency_s=0.0, attempts=0,
                    )
                )
            return cached
        hint = ""
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                try:
                    resp = self.backend.complete(call_type, payload, seed, repair_note=hint)
                except TypeError:  # backend without the repair_note parameter
                    resp = self.backend.complete(call_type, payload, seed)
                ok, problem = (True, "")
                if self.validate:
                    ok, problem = validate_response(call_type, resp.data)
                if self.log is not None:
                    self.log.add(
                        dict(
                            call_type=call_type,
                            seed=seed,
                            cache_key=key,
                            backend=resp.backend,
                            model=resp.model,
                            temperature=DECODING[call_type]["temperature"],
                            top_p=DECODING[call_type]["top_p"],
                            schema_ok=bool(ok),
                            schema_problem=problem,
                            data=resp.data,
                            text=resp.text,
                            tokens_in=resp.tokens_in,
                            tokens_out=resp.tokens_out,
                            latency_s=resp.latency_s,
                            attempts=attempt,
                        )
                    )
                if ok:
                    self.calls += 1
                    if attempt > 1:
                        self.schema_retries += attempt - 1
                    out = normalise(call_type, resp.data) if self.validate else resp.data
                    self._cache.put(
                        key,
                        dict(
                            call_type=call_type, seed=seed, backend=resp.backend,
                            model=resp.model, tokens_in=resp.tokens_in,
                            tokens_out=resp.tokens_out, latency_s=resp.latency_s,
                            data=out,
                        ),
                    )
                    return out
                # violated the contract: re-request with the concrete problem
                hint = problem
                self.schema_retries += 1
                last_exc = LLMSchemaError(problem)
            except Exception as exc:  # network / transport failure
                last_exc = exc
                time.sleep(min(1.5 * attempt, 6.0))
        self.exhausted += 1
        raise LLMSchemaError(f"LLM call '{call_type}' failed after {self.max_retries} attempts: {last_exc}")

    def try_call(self, call_type: str, payload: dict, seed: int = 0, default=None):
        """Return ``default`` instead of raising when the contract cannot be met."""
        try:
            return self(call_type, payload, seed)
        except LLMSchemaError:
            return default

    def stable(self, call_type: str, payload: dict, repeats: int = 20, base_seed: int = 0) -> list[dict]:
        """Repeat a call with fresh seeds (used by the stability experiment)."""
        return [self(call_type, payload, seed=base_seed + i) for i in range(repeats)]


class RoutedBackend:
    """Send selected call types to a different backend.

    Used to isolate *which* LLM call matters: experiment B keeps the real model for
    the forward translation and routes the forensic-hypothesis call to the
    deterministic surrogate, so the only difference from the full system is who
    writes the hypotheses.
    """

    def __init__(self, primary: LLMBackend, fallback: LLMBackend, routed: set[str]):
        self.primary = primary
        self.fallback = fallback
        self.routed = set(routed)
        self.name = f"routed({primary.name}|{fallback.name})"
        self.model = f"{getattr(primary, 'model', '?')}|{getattr(fallback, 'model', '?')}"

    def complete(self, call_type: str, payload: dict, seed: int = 0, repair_note: str = "") -> LLMResponse:
        target = self.fallback if call_type in self.routed else self.primary
        try:
            return target.complete(call_type, payload, seed, repair_note=repair_note)
        except TypeError:  # backend without repair_note
            return target.complete(call_type, payload, seed)


def _default_backend() -> LLMBackend:
    url = os.environ.get("ALMOND_LLM_BASE_URL")
    routed = {
        c.strip()
        for c in os.environ.get("ALMOND_LLM_SURROGATE_CALLS", "").split(",")
        if c.strip()
    }
    if url:
        primary = OpenAICompatBackend()
        if routed:
            return RoutedBackend(primary, SurrogateBackend(), routed)
        return primary
    return SurrogateBackend()
