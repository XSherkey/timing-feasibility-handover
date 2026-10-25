"""Summarise the A / B experiments against the campaign arms.

Reads only JSON: the prior baselines, the two forensic-generator arms and the
campaign, and prints one comparison table with means, 95 % CIs, medians and the
rule-commit statistics, so the report can quote a single consistent set.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def ci(v: np.ndarray) -> tuple[float, float]:
    if len(v) < 2:
        return float(v[0]), float(v[0])
    h = 1.96 * v.std(ddof=1) / np.sqrt(len(v))
    return float(v.mean() - h), float(v.mean() + h)


def load_arm(d: Path, method: str = "almond") -> dict:
    arctic, sat, commits, effects = [], [], [], []
    for p in sorted(d.glob(f"{method}_seed*/run_summary.json")):
        with open(p, encoding="utf-8") as fh:
            r = json.load(fh)
        if not r.get("ok"):
            continue
        arctic.append(r["final"]["arctic"]["hsr"] * 100)
        sat.append(r["final"]["satisfaction"])
        acc = [f for f in (r.get("forensics") or []) if f.get("accepted")]
        commits.append(len(acc))
        effects.extend(f.get("effect") for f in acc)
    return dict(arctic=np.array(arctic), sat=np.array(sat),
                commits=np.array(commits), effects=Counter(e for e in effects if e))


def row(name: str, a: np.ndarray, s: np.ndarray | None = None, extra: str = "") -> str:
    lo, hi = ci(a)
    med = float(np.median(a))
    s_txt = f"{s.mean():5.1f}" if s is not None and len(s) else "  -  "
    return f"{name:<34}{a.mean():6.1f} {lo:6.1f} {hi:6.1f} {med:6.1f} {s_txt}  {extra}"


def main() -> int:
    prior = json.loads((ROOT / "results/baseline_prior.json").read_text(encoding="utf-8"))
    teacher = np.array([r["teacher"]["arctic"] for r in prior["rows"]])
    teacher_s = np.array([r["teacher"]["satisfaction"] for r in prior["rows"]])
    bc = np.array([r["bc_only"]["arctic"] for r in prior["rows"]])
    bc_s = np.array([r["bc_only"]["satisfaction"] for r in prior["rows"]])
    llm = load_arm(ROOT / "results/campaign", "almond")
    sur = load_arm(ROOT / "results/campaign_surrogate_forensics", "almond")

    print(f"{'arm':<34}{'arctic':>6} {'lo':>6} {'hi':>6} {'med':>6} {'S':>5}  notes")
    print(row("analytic controller only", teacher, teacher_s, "no network, no learning"))
    print(row("behaviour-cloned prior only", bc, bc_s, "deployed clone, no PPO"))
    print(row("PPO on the prior (surrogate hyp.)", sur["arctic"], sur["sat"],
              f"commits {sur['commits'].mean():.1f}/run, {dict(sur['effects'])}"))
    print(row("PPO on the prior (LLM hyp.)", llm["arctic"], llm["sat"],
              f"commits {llm['commits'].mean():.1f}/run, {dict(llm['effects'])}"))

    # the two ablation arms that never run forensics
    for name, d in (("PPO-MLP (no prior metric)", "ppomlp"), ("ALMOND w/o forensics", "no_forensics")):
        arm = load_arm(ROOT / "results/campaign")
        target = ROOT / "results/campaign"
        vals, sat = [], []
        for p in sorted(target.glob(f"{d}_seed*/run_summary.json")):
            with open(p, encoding="utf-8") as fh:
                r = json.load(fh)
            if r.get("ok"):
                vals.append(r["final"]["arctic"]["hsr"] * 100)
                sat.append(r["final"]["satisfaction"])
        if vals:
            print(row(name, np.array(vals), np.array(sat), "no forensic loop"))

    print("\npaired comparisons (same seeds):")
    n = min(len(teacher), len(llm["arctic"]))
    print(f"  LLM forensics - analytic controller : {(llm['arctic'][:n] - teacher[:n]).mean():+.1f} pp "
          f"(win {int((llm['arctic'][:n] > teacher[:n]).sum())}/{n})")
    print(f"  LLM forensics - surrogate forensics : {(llm['arctic'] - sur['arctic']).mean():+.1f} pp "
          f"(win {int((llm['arctic'] > sur['arctic']).sum())}/{min(len(llm['arctic']), len(sur['arctic']))})")
    print(f"  surrogate forensics - controller    : {(sur['arctic'][:n] - teacher[:n]).mean():+.1f} pp")

    out = dict(
        teacher=dict(arctic=teacher.tolist(), sat=teacher_s.tolist()),
        bc_only=dict(arctic=bc.tolist(), sat=bc_s.tolist()),
        llm_forensics=dict(arctic=llm["arctic"].tolist(), sat=llm["sat"].tolist(),
                           commits=llm["commits"].tolist(), effects=dict(llm["effects"])),
        surrogate_forensics=dict(arctic=sur["arctic"].tolist(), sat=sur["sat"].tolist(),
                                 commits=sur["commits"].tolist(), effects=dict(sur["effects"])),
    )
    p = ROOT / "results/ab_summary.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\nwrote", p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
