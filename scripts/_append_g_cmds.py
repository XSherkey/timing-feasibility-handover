from pathlib import Path

p = Path(r"docs/EVIDENCE_PACKAGE.md")
t = p.read_text(encoding="utf-8")
marker = "python scripts/_routeA_f5.py --configs noseam,feeder3"
add = marker + """

# Phase G 追加（A17–A21）
python scripts/run_multi_intent.py --mode shared        --seed 0 --inject-bad-rule-extra "cap_advance:6@latitude_abs_deg>=68" --out results/routeA_g1/i_clean_gate_s0
python scripts/run_multi_intent.py --mode shared_nogate --seed 0 --inject-bad-rule-extra "cap_advance:6@latitude_abs_deg>=68" --out results/routeA_g1/i2_clean_nogate_s0
python scripts/run_campaign.py --methods no_forensics --seeds 0-9 --late-risk-tau 16 --late-risk-weight 64 --out results/routeA_g2/lam64
python scripts/_routeA_g3.py
python scripts/run_campaign.py --methods almond --seeds 0-4 --acq-signaling 3.2 --probe-calibrated --probe-episodes 8 --out results/routeA_g4/pcs8_sig32
python scripts/_routeA_g2b_g4b.py
python scripts/_routeA_g1_analysis.py
python scripts/_routeA_g_summarise.py"""
if "Phase G 追加" not in t:
    p.write_text(t.replace(marker, add, 1), encoding="utf-8")
    print("appended")
else:
    print("already present")
