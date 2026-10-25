"""Multi-intent protocol: does knowledge mined for one intent transfer to the next?

Why this exists
---------------
In the single-intent campaign the ``no_memory`` and ``no_counterfactual`` arms come
out bit-identical to ALMOND: the translation happens once, while the knowledge
graph is still empty, and the rule is accepted anyway.  The components therefore
cannot show an effect no matter how many seeds are run.

This driver fixes the protocol instead of the number: a *sequence* of intents
shares one knowledge graph, and only the first intent is allowed to run reverse
forensics.  Intents 2..N have no forensic cycles at all, so the only way they can
get a shield is to inherit the rule.

    --mode shared : one knowledge graph across the sequence (intent 0 mines,
                    intents 1+ inherit)
    --mode fresh  : a fresh knowledge graph per intent (intent 0 mines and the
                    knowledge is thrown away; intents 1+ have nothing)

The difference between the two modes on intents 2..N is exactly the value of
persistent, cross-intent knowledge.

Usage
-----
    python scripts/run_multi_intent.py --mode shared --seed 0
    python scripts/run_multi_intent.py --mode fresh  --seed 0
    python scripts/run_multi_intent.py --mode shared --seed 0 --intents reliability_first,latency_first
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almond.framework.kg import KnowledgeGraph  # noqa: E402
from almond.framework.system import AlmondConfig, AlmondSystem  # noqa: E402
from almond.twin.twin import DigitalTwin, TwinConfig  # noqa: E402

DEFAULT_INTENTS = ("reliability_first", "latency_first", "power_first", "balanced")


def parse_rule(text: str) -> dict:
    """``effect:mag@field op value,...`` -> a hypothesis payload for the engine."""
    m = re.match(r"^\s*([a-z_]+)\s*:\s*(-?[\d.]+)\s*(?:@(.*))?$", text)
    if not m:
        raise SystemExit(f"cannot parse rule {text!r} (expected effect:mag@field op value)")
    effect, magnitude, atoms_txt = m.group(1), float(m.group(2)), m.group(3) or ""
    atoms = []
    for part in [a for a in atoms_txt.split(",") if a.strip()]:
        part = part.strip()
        for op in ("<=", ">=", "==", "!=", "<", ">"):
            if op in part:
                field, value = part.split(op, 1)
                atoms.append({"field": field.strip(), "cmp": op, "value": float(value)})
                break
        else:
            raise SystemExit(f"cannot parse atom {part!r}")
    return {"hypotheses": [{"if": {"all": atoms},
                            "then": {"effect": effect, "magnitude": magnitude},
                            "rationale": f"injected candidate: {text}"}],
            "alternative_explanations": []}


class InjectedLLM:
    """LLM proxy that answers the forensic call with a fixed candidate.

    Every other attribute (``backend``, ``log``, counters) is delegated to the real
    client, so the rest of the pipeline behaves exactly as before; only the
    hypothesis text changes, which lets the normal audit + gate decide its fate.
    """

    def __init__(self, orig, hypothesis: dict):
        object.__setattr__(self, "_orig", orig)
        object.__setattr__(self, "hypothesis", hypothesis)

    def __call__(self, call_type, payload, seed=0):
        if call_type == "forensic_hypothesis":
            return self.hypothesis
        return self._orig(call_type, payload, seed)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_orig"), name)


class AppendingLLM(InjectedLLM):
    """LLM proxy that *appends* a candidate to whatever the real model proposes.

    The replacement proxy above changes the pipeline in a second way: the good
    rule the model would have proposed never exists, so a rejection leaves the
    system with no knowledge at all.  This variant keeps the real proposal and
    adds the injected candidate next to it, which is the clean test of the gate:
    reject the bad one, keep the good one.
    """

    def __call__(self, call_type, payload, seed=0):
        if call_type == "forensic_hypothesis":
            base = self._orig(call_type, payload, seed)
            out = dict(base) if isinstance(base, dict) else {"hypotheses": []}
            out["hypotheses"] = list(base.get("hypotheses", [])) + list(self.hypothesis.get("hypotheses", []))
            return out
        return self._orig(call_type, payload, seed)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("shared", "fresh", "shared_nogate"), required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--intents", default=",".join(DEFAULT_INTENTS))
    ap.add_argument("--episodes", type=int, default=9600)
    ap.add_argument("--eval-every", type=int, default=1200)
    ap.add_argument("--twin-hours", type=float, default=12.0)
    ap.add_argument("--spec", default="results/nas/llm_spec.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--inject-bad-rule", default=None,
                    help="force the forensic engine to propose this rule at intent 0 "
                         "(replacement mode); the gate then decides whether it is committed")
    ap.add_argument("--inject-bad-rule-extra", default=None,
                    help="append this rule next to the model's own proposal (clean test: "
                         "reject the bad one, keep the good one)")
    args = ap.parse_args()

    if args.inject_bad_rule and args.inject_bad_rule_extra:
        raise SystemExit("--inject-bad-rule and --inject-bad-rule-extra are mutually exclusive")
    intents = [s.strip() for s in args.intents.split(",") if s.strip()]
    out_root = Path(args.out or (ROOT / "results" / f"multi_{args.mode}_seed{args.seed}"))
    out_root.mkdir(parents=True, exist_ok=True)
    spec = json.loads((ROOT / args.spec).read_text(encoding="utf-8")) if args.spec else None
    rule_txt = args.inject_bad_rule or args.inject_bad_rule_extra
    hyp = parse_rule(rule_txt) if rule_txt else None
    append_mode = bool(args.inject_bad_rule_extra)
    gate_on = args.mode != "shared_nogate"

    twin = DigitalTwin(TwinConfig(horizon_s=args.twin_hours * 3600)).build(verbose=False)
    shared_kg = KnowledgeGraph(out_root / "knowledge_graph.json")
    rows = []
    for i, intent in enumerate(intents):
        cfg = AlmondConfig(
            variant="full",
            seed=args.seed,
            intent=intent,
            episodes=args.episodes,
            eval_every=args.eval_every,
            device=args.device,
            twin_hours=args.twin_hours,
            nas_generations=0,
            fixed_spec=spec,
            counterfactual_gate=gate_on,
            # only the first intent may mine; the rest must inherit
            max_forensic_rounds=(1 if i == 0 else 0),
            forensics_after=25,
            out_dir=str(out_root / f"intent{i}_{intent}"),
        )
        system = AlmondSystem(cfg, twin=twin, out_dir=cfg.out_dir)
        system.kg = shared_kg if args.mode != "fresh" else KnowledgeGraph(out_root / f"kg_intent{i}.json")
        if hyp is not None and i == 0:
            # the normal audit and counterfactual replay still run, so the gate
            # decides the fate of the injected candidate; in append mode the model's
            # own proposal is kept, which is the clean "reject only the bad one" test
            system.llm = AppendingLLM(system.llm, hyp) if append_mode else InjectedLLM(system.llm, hyp)
            system.events.append(dict(event="injected_candidate", rule=rule_txt,
                                      mode="append" if append_mode else "replace"))
        res = system.run()
        fin = res.get("final", {})
        rows.append(dict(
            intent=intent,
            arctic=fin.get("arctic", {}).get("hsr"),
            midlat=fin.get("midlat", {}).get("hsr"),
            satisfaction=fin.get("satisfaction"),
            kg_active=len(system.kg.active()),
            kg_magnitudes=[c.magnitude for c in system.kg.active()],
            weight=tuple(round(res.get("weights", {}).get(k, 0.0), 2) for k in ("w_rel", "w_lat", "w_pow")),
        ))
        print(f"[{args.mode}] seed {args.seed} intent {i} {intent:<18} "
              f"arctic {100 * (rows[-1]['arctic'] or 0):5.1f}%  "
              f"kg_active={rows[-1]['kg_active']} mags={rows[-1]['kg_magnitudes']}  "
              f"w={rows[-1]['weight']}", flush=True)

    (out_root / "summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
