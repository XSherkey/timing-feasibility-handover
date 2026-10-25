"""R6 part 2 (EN): the remaining numeric 'full system' attachments."""
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


rep("moves from 22.1% to 0.6% between the reward-only campaign arm and the full system",
    "moves from 22.1% to 0.6% between the reward-only campaign arm and the mined-rule campaign arm",
    "n1")
rep("does **not** favour the full system on the +7 d instance",
    "does **not** favour the full-system policies on the +7 d instance", "n2")
rep('matches the full system at nominal physics (94.0% ± 0.7% vs 93.6% ± 0.7%)',
    'matches the mined-rule campaign arm at nominal physics (94.0% ± 0.7% vs 93.6% ± 0.7%)', "n3")
rep("23.4 of the 24.0 pp between the reward-only policies and the full system's frozen τ = 16 s arm",
    "23.4 of the 24.0 pp between the reward-only policies and the mined-rule arm's frozen τ = 16 s arm",
    "n4")
rep("92.43 for the full system's frozen τ = 16 s arm)",
    "92.43 for the mined-rule arm's frozen τ = 16 s arm)", "n5")
rep("(iii) The full system with its validation-calibrated shield",
    "(iii) The full-system policies with their validation-calibrated shield", "n6")
rep("on the same architecture and data as the full system.",
    "on the same architecture and data as the full-system policies.", "n7")

P.write_text(t, encoding="utf-8")
print("applied:", done)
