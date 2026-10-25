"""Does enriching the discovery set raise forensic recall?  (controlled test)

Loads *frozen* campaign policies (no retraining), and for each one runs the
forensic loop twice on identical splits, with identical LLM seeds:

* ``legacy``   - the original discovery selection (route availability, then
                 acquisition time), which over-sampled the ``no_route`` class;
* ``enriched`` - stratified by the gateway error code recorded by the twin
                 (``late_handover`` / ``no_route`` / ``window_exceeded`` /
                 ``below_elevation``) with the code written into the narrative.

Because the actor is frozen and the split is the same, every difference is
attributable to the discovery set.  Reported per mode:

* candidates proposed, candidates surviving the auditor, candidates clearing the
  validation gate, and rules committed after the held-out test;
* **recall** - which of the three rule classes the twin can express
  (timing / routing / plane discipline) the committed rules cover;
* mean and per-multiplier test gain of the committed rules.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.auditor import Auditor
from almond.framework.forensics import ForensicEngine, SplitConfig
from almond.framework.kg import KnowledgeGraph
from almond.llm.backend import LLMClient, LLMLog, SurrogateBackend, _default_backend
from almond.policies.nets import GraphSpec, build_policy
from almond.policies.ppo import RunningNorm
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

#: failure classes the twin can produce and the executable effect that remedies
#: each one.  Recall is measured only over the classes *present* in that run's
#: discovery set, because a failure mode that never occurs cannot be mined.
CAUSE_EFFECT = {
    "late_handover": "min_advance",
    "no_route": "forbid_unrouted_target",
    "window_exceeded": "cap_advance",
}
#: the three rule classes used for the headline recall figure
CLASSES = {
    "timing": "min_advance",
    "routing": "forbid_unrouted_target",
    "window": "cap_advance",
}


def load_policy(run: Path):
    blob = torch.load(run / "policy.pt", map_location="cpu", weights_only=False)
    return blob


def make_policy_fn(pol, obs_norm, env):
    def policy_fn(obs, x, adj, deterministic=True):
        o = obs_norm(obs) if obs_norm is not None else obs
        cand = env.cand_idx[env.site, env.t_idx]
        mask = np.concatenate([np.ones((env.batch, 1), bool), cand >= 0], axis=1)
        with torch.no_grad():
            lt, la, _v = pol(
                torch.as_tensor(o, dtype=torch.float32),
                torch.as_tensor(x, dtype=torch.float32),
                torch.as_tensor(adj, dtype=torch.float32),
            )
        lt = np.where(mask, lt.numpy(), -1e9)
        return lt.argmax(-1), la.numpy().argmax(-1)

    return policy_fn


def run_mode(mode: str, twin, blob, llm, kg, auditor, splits, seed: int, episodes: int) -> dict:
    weights = blob.get("weights") or dict(w_rel=0.57, w_lat=0.14, w_pow=0.29)
    env = HandoverEnv(
        twin,
        EnvConfig(episode_steps=240, w_rel=weights["w_rel"], w_lat=weights["w_lat"],
                  w_pow=weights["w_pow"]),
        batch=24,
        seed=seed * 7919 + 13,
    )
    x, adj = env.candidate_graph()
    spec = GraphSpec.from_dict(blob["spec"])
    pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                       n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
    pol.load_state_dict(blob["policy"])
    pol.eval()
    _on = blob.get("obs_norm")
    obs_norm = None
    if _on:
        obs_norm = RunningNorm(len(_on["mean"]))
        obs_norm.load_state_dict(_on)

    log: list[dict] = []
    fe = ForensicEngine(
        twin=twin, env=env, policy_fn=make_policy_fn(pol, obs_norm, env), llm=llm,
        kg=kg, auditor=auditor, splits=splits, delta_min=0.05, log=log,
    )
    res = fe.run(max_attempts=1, validate_episodes=3, test_episodes=3,
                 discovery_mode=mode)
    disc = next((e for e in log if e.get("event") == "discovery"), {})
    audits = [e for e in log if e.get("event") == "audit"]
    val = [e for e in log if e.get("event") == "validation"]
    tests = [e for e in log if e.get("event") == "test"]
    covered = set()
    if res.accepted and res.constraint is not None:
        for cls, eff in CLASSES.items():
            if res.constraint.effect == eff:
                covered.add(cls)
    causes = disc.get("causes", {}) or {}
    # which rule classes *could* have been mined from this discovery set
    present = {cls for cls, eff in CLASSES.items()
               if any(CAUSE_EFFECT.get(c) == eff for c in causes)}
    # does the model propose the remedy for a failure mode that is actually present?
    proposed = [a.get("effect") for a in audits if a.get("effect")]
    expected = {CAUSE_EFFECT[c] for c in causes if c in CAUSE_EFFECT}
    aligned = [e for e in proposed if e in expected]
    return dict(
        mode=mode,
        discovery_rows=disc.get("rows", 0),
        discovery_causes=causes,
        present_classes=sorted(present),
        expected_effects=sorted(expected),
        n_proposed=len(proposed),
        n_aligned=len(aligned),
        alignment=(len(aligned) / len(proposed)) if proposed else 0.0,
        recall_denominator=len(present),
        recall_numerator=len(covered & present),
        candidates=res.n_candidates,
        audit_pass=sum(1 for a in audits if a.get("ok")),
        validation_pass=sum(1 for v in val if v.get("delta", 0) >= 0.05),
        committed=int(bool(res.accepted)),
        effect=res.constraint.effect if res.constraint else None,
        atoms=res.constraint.atoms if res.constraint else None,
        delta_val=res.delta_val,
        delta_test=res.delta_test,
        per_multiplier=[t.get("per_multiplier") for t in tests][-1] if tests else None,
        covered_classes=sorted(covered),
        proposed_effects=sorted({a.get("effect") for a in audits if a.get("effect")}),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/campaign/almond_seed*,results/campaign/eureka_seed*")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--tag", default="ref")
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--out", default="results/forensics_recall.json")
    ap.add_argument("--backend", default="auto", choices=["auto", "surrogate"])
    args = ap.parse_args()

    runs: list[Path] = []
    for pat in args.runs.split(","):
        runs.extend(sorted(Path().glob(pat.strip())))
    runs = [r for r in runs if (r / "policy.pt").exists()][: args.limit]
    if not runs:
        print("no runs with policy.pt found")
        return 1
    print(f"{len(runs)} frozen policies: {[r.name for r in runs]}")

    twin = DigitalTwin(TwinConfig(tag=args.tag, horizon_s=args.hours * 3600)).build(verbose=False)
    backend = SurrogateBackend() if args.backend == "surrogate" else _default_backend()
    log_path = Path(args.out).with_suffix(".calls.jsonl")
    if log_path.exists():
        log_path.unlink()
    llm = LLMClient(backend, LLMLog(log_path), max_retries=4)
    print(f"backend={llm.backend.name} model={getattr(llm.backend, 'model', 'n/a')}")

    results = {"runs": [], "legacy": {}, "enriched": {}}
    for i, run in enumerate(runs):
        blob = load_policy(run)
        # a fresh graph per mode so commits from one mode cannot leak into the other
        rec = {"run": run.name}
        for mode in ("legacy", "enriched"):
            kg_path = Path("results/_recall_kg") / f"{run.name}_{mode}.json"
            kg_path.parent.mkdir(parents=True, exist_ok=True)
            if kg_path.exists():
                kg_path.unlink()  # fresh graph: commits must not leak between modes
            kg = KnowledgeGraph(kg_path)
            # same composition the ALMOND system uses (no fitted impact model ->
            # the impact stage is skipped rather than silently rejecting rules)
            auditor = Auditor(impact=None, require_impact=False)
            r = run_mode(mode, twin, blob, llm, kg, auditor, SplitConfig(), seed=i, episodes=3)
            rec[mode] = r
            print(f"  [{run.name}] {mode:<8} disc={r['discovery_rows']:3d} "
                  f"cand={r['candidates']} audit={r['audit_pass']} val={r['validation_pass']} "
                  f"commit={r['committed']} effect={r['effect']} dtest={r['delta_test']:+.3f}")
        results["runs"].append(rec)

    for mode in ("legacy", "enriched"):
        rows = [r[mode] for r in results["runs"]]
        covered: Counter = Counter()
        for r in rows:
            covered.update(r["covered_classes"])
        have = [r for r in rows if r["recall_denominator"] > 0]
        results[mode] = dict(
            n=len(rows),
            n_with_failures=len(have),
            discovery_rows=float(np.mean([r["discovery_rows"] for r in rows])),
            causes={k: int(sum(r["discovery_causes"].get(k, 0) for r in rows))
                    for k in CAUSE_EFFECT},
            candidates=float(np.mean([r["candidates"] for r in rows])),
            commit_rate=float(np.mean([r["committed"] for r in rows])),
            recall_by_class={c: covered.get(c, 0) / len(rows) for c in CLASSES},
            # recall over the classes that were actually present
            recall=float(np.mean([r["recall_numerator"] / r["recall_denominator"] for r in have]))
            if have else 0.0,
            recall_committed=float(sum(r["recall_numerator"] for r in have) /
                                   max(1, sum(r["recall_denominator"] for r in have))),
            mean_delta_test=float(np.mean([r["delta_test"] for r in rows if r["committed"]]))
            if any(r["committed"] for r in rows) else 0.0,
            # the metric enrichment is expected to move: does the model propose the
            # remedy for a failure mode that is actually in the discovery set?
            alignment=float(np.mean([r["alignment"] for r in rows])),
            aligned_fraction_pooled=float(sum(r["n_aligned"] for r in rows) /
                                          max(1, sum(r["n_proposed"] for r in rows))),
            class_coverage=float(np.mean([len(r["covered_classes"]) / max(1, r["recall_denominator"])
                                          for r in have])) if have else 0.0,
            effects_proposed=dict(Counter(e for r in rows for e in r["proposed_effects"])),
        )

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=2, default=float), encoding="utf-8")
    print("\nmode       disc-rows  candidates  commit-rate  recall(pooled)  alignment  coverage")
    for mode in ("legacy", "enriched"):
        d = results[mode]
        print(f"{mode:<10} {d['discovery_rows']:9.1f} {d['candidates']:11.2f} "
              f"{d['commit_rate']:11.2f}  {d['recall_committed']:13.2f}  "
              f"{d['aligned_fraction_pooled']:8.2f}  {d['class_coverage']:8.2f}")
    print("\nfailure causes in the discovery sets (rows across runs):")
    for mode in ("legacy", "enriched"):
        print(f"  {mode:<9} {results[mode]['causes']}")
    print("\neffects proposed to the auditor:")
    for mode in ("legacy", "enriched"):
        print(f"  {mode:<9} {results[mode]['effects_proposed']}")
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
