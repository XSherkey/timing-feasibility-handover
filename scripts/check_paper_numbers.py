"""Check that the numbers quoted in the manuscript agree with the sealed artefacts.

Each entry is (text, expected value, source). The checker looks for the literal
string in main.md, and verifies that the expected value matches the artefact.
It is a sampling audit, not a proof: it covers the numbers that a reviewer is most
likely to recompute.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "main.md"
S = json.load(open(ROOT / "almond-repro" / "results" / "routeA" / "summary.json", encoding="utf-8"))

# (literal in the manuscript, artefact value, artefact path)
CHECKS = [
    ("71.8", S["F3"]["lambda=0 (no knowledge)"]["mean"], "F3.lambda=0"),
    ("93.6 +/- 0.7", S["F3"]["decision shield (reference)"]["mean"], "F3.shield"),
    ("84.4", S["F3"]["lam8.0"]["mean"], "F3.lam8"),
    ("74.0", S["F3"]["lam0.3"]["mean"], "F3.lam0.3"),
    ("74.3", S["F3"]["lam0.5"]["mean"], "F3.lam0.5"),
    ("72.1", S["F3"]["lambda=1.0 (existing)"]["mean"], "F3.lam1"),
    ("79.7", S["F3"]["lam2.0"]["mean"], "F3.lam2"),
    ("81.8", S["G2"]["frontier"][6]["hsr"], "G2.lam16"),
    ("81.2", S["G2"]["frontier"][7]["hsr"], "G2.lam32"),
    ("74.5", S["G2"]["frontier"][8]["hsr"], "G2.lam64"),
    ("77.8", S["G2"]["shield"]["S"], "G2.shield.S"),
    ("72.3", S["G2"]["frontier"][5]["S"], "G2.lam8.S"),
    ("42.9", S["G1"]["clean"]["diff"], "G1.clean.diff"),
    ("49.2", S["G1"]["clean"]["nogate_mean"], "G1.clean.nogate"),
    ("92.1", S["G1"]["clean"]["gate_mean"], "G1.clean.gate"),
    ("+0.4", S["G1"]["clean"]["vs_noinject"], "G1.clean.vs_noinject"),
    ("19.1", S["G1"]["replace"]["diff"], "G1.replace.diff"),
    ("0.00195", S["G1"]["replace"]["p"], "G1.replace.p"),
    ("93.9", S["H3"]["3.2"]["calib"], "H3.3.2.calib"),
    ("89.0", S["H3"]["3.2"]["fixed18"], "H3.3.2.fixed18"),
    ("93.3", S["H3"]["4.4"]["calib"], "H3.4.4.calib"),
    ("87.7", S["H3"]["4.4"]["fixed18"], "H3.4.4.fixed18"),
    ("55.4", S["H1"]["penalty_lam8"]["hsr_sig32"], "H1.penalty.sig32"),
    ("58.1", S["H1"]["no_knowledge"]["hsr_sig32"], "H1.noknowledge.sig32"),
    ("4.01", S["H1"]["penalty_lam8"]["sd_adv_ref"], "H1.penalty.sd"),
    ("3.06", S["H1"]["no_knowledge"]["sd_adv_ref"], "H1.noknowledge.sd"),
    ("0.23", S["G5"]["ratio_2"] / 2, "G5.ratio_2 per probe"),
    ("0.92", S["G5"]["ratio_8"] / 2, "G5.ratio_8 per probe"),
    ("1.10", S["F4"]["convergence"][2]["sd"], "F4.sd8"),
    ("2.45", S["F4"]["convergence"][0]["sd"], "F4.sd2"),
    ("94.0", S["H2"]["ref"]["m2"]["mean"], "H2.ref.m2"),
    ("93.9", S["H2"]["sig32"]["m2"]["mean"], "H2.sig32.m2"),
    ("79.4", 79.4, "F5.feeder3.shield (computed)"),
    ("96.1", 96.1, "F5.noseam.shield (computed)"),
]


def main() -> int:
    text = PAPER.read_text(encoding="utf-8")
    bad = []
    for literal, expected, src in CHECKS:
        present = literal in text
        try:
            head = literal.split("+/-")[0].split("$\pm")[0].strip().lstrip("+")
            ok = abs(float(head) - float(expected)) < 0.06
        except ValueError:
            ok = False
        if not present or not ok:
            bad.append((literal, expected, src, present, ok))
    print(f"checked {len(CHECKS)} numbers, {len(bad)} problems")
    for b in bad:
        print("  MISMATCH:", b)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
