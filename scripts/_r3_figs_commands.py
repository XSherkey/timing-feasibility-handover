"""R3 (v10): add Figs 8-9 captions, in-text references, and the new Appendix-A commands."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


FIG89 = """
**Fig. 8.** Deployment view. Discovery (training window), calibration and admission (validation window) and deployment are separate services over a versioned knowledge graph. The shield reads committed constraints at decision time and writes nothing; monitoring schedules a re-probe on drift and a rollback restores the previous committed version. Interfaces and failure paths are specified in Section VI-K.

**Fig. 9.** Passive support and sample budget. (a) Late-handover rate against the handover advance in the passive no-shield log (PPO-MLP, ten seeds, |lat| ≥ 68°, 8,682 attempts), with binomial 95% intervals and a PAVA monotone fit; the shaded band is the cluster-bootstrap 95% interval of the 5%-crossing (10 s to 18 s). (b) Width of that interval against the number of attempts drawn: resampling attempts independently (light) collapses to one grid step by 1,000 attempts, while resampling (seed, site) blocks (dark) stays at several seconds even at the full budget. The passivity of the log, not its size, is the binding constraint.
"""
i = t.find("## Figure Captions")
j = t.find("\n", t.rfind("**Fig. 7.**"))
t = t[:j + 1] + FIG89 + t[j + 1:]
done.append("fig-captions")

rep("Fig. 8 shows the deployment view.",
    "Fig. 8 shows the deployment view.", "noop-fig8")

# in-text pointers for Fig. 9 (Section IV-C, after the support numbers)
rep("The crossing is therefore *sampled but thin*:",
    "Fig. 9a shows this directly and Fig. 9b adds the sample-budget curve: resampling attempts independently makes the crossing interval collapse to one grid step, but resampling (seed, site) blocks keeps it at several seconds even at the full passive budget. The crossing is therefore *sampled but thin*:",
    "fig9-pointer")

# Appendix A: new commands
A_OLD = """python scripts/probe_gate.py --run results/campaign_1023/almond_seed0 --episodes 8   # six-candidate audit gate
```"""
A_NEW = """python scripts/probe_gate.py --run results/campaign_1023/almond_seed0 --episodes 8   # six-candidate audit gate
python experiments/run_passive_identifiability.py    # support bootstrap + budget curve   (~4 min)
python experiments/run_isolation_lean.py             # A0-A8 contribution isolation      (~25 min)
python experiments/run_lambda_validation.py          # lockbox calibration of lambda     (~6 min)
python experiments/run_gate_systematic.py            # 26-candidate gate confusion       (~25 min)
python experiments/run_drift_margin.py               # drift ladder + margin at n = 10   (~40 min)
python experiments/run_alternative_physics.py        # Table VI rebuild                  (~12 min)
```

The R3 scripts read `experiments/manifest_r3.json` and write their summaries to
`results/routeA_r3/`; the manifest pins the twin fingerprint, the three time windows, the traffic
multipliers, the ten policy seeds, the lockbox epochs and the physics-drift settings, so a rerun
does not depend on any number hard-coded inside a script. Every command above is CPU-only; the
timings in parentheses are measured on a 12-core desktop. `run_isolation_lean.py` evaluates A0 on
the full grid and checks by re-evaluation (two seeds, all four instances) that the arms which deploy
the same rule return bit-identical numbers."""
rep(A_OLD, A_NEW, "appendix-commands")

P.write_text(t, encoding="utf-8")
print("applied:", done)
