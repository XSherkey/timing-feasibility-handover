"""Patch run_isolation.py: quick mode via R3_QUICK, and late-share from polar_causes."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "run_isolation.py"
t = p.read_text(encoding="utf-8")

old = '''ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
PPO = {s: f"results/campaign_1023/ppomlp_seed{s}" for s in SEEDS}
SEL_SEEDS = [0, 1, 2]          # seeds used ONLY to rank candidates on validation'''
new = '''import os

QUICK = bool(os.environ.get("R3_QUICK"))
SEL_SEEDS = [0] if QUICK else [0, 1, 2]     # seeds used ONLY to rank candidates on validation

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in (SEEDS[:2] if QUICK else SEEDS)}
PPO = {s: f"results/campaign_1023/ppomlp_seed{s}" for s in (SEEDS[:2] if QUICK else SEEDS)}
if QUICK:
    SEEDS = SEEDS[:2]'''
if t.count(old) != 1:
    raise SystemExit("anchor not found")
t = t.replace(old, new, 1)

old2 = '''    instances = {"eval": None}
    for e in LOCKBOX_EPOCHS:
        instances[f"lb{e:g}"] = e'''
new2 = '''    instances = {"eval": None}
    for e in (LOCKBOX_EPOCHS[:1] if QUICK else LOCKBOX_EPOCHS):
        instances[f"lb{e:g}"] = e'''
if t.count(old2) != 1:
    raise SystemExit("instances anchor not found")
t = t.replace(old2, new2, 1)

old3 = '''while len(RANDOM) < 20:'''
new3 = '''while len(RANDOM) < (6 if QUICK else 20):'''
if t.count(old3) != 1:
    raise SystemExit("random anchor not found")
t = t.replace(old3, new3, 1)

p.write_text(t, encoding="utf-8")
print("run_isolation patched for quick mode")
