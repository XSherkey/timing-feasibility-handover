"""R4 part 2 (EN): define 'the full system' once, fix the numeric uses, note the p95 band."""
from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    print("ok", label)


rep(
    "Fig. 2 decomposes the gap between a literature-style baseline and the full system.",
    "Fig. 2 decomposes the gap between a literature-style baseline and the full system (throughout, \"the full system\" denotes the deployed pipeline; wherever a *number* is attributed to it, it is the **mined-rule campaign arm**, and the threshold ledger of Section V-D governs any ambiguity).",
    "define-full-system",
)
rep(
    "The end-to-end campaign figure of the full system, 93.6% ± 0.7%, is reproduced separately",
    "The end-to-end campaign figure of the mined-rule campaign arm, 93.6% ± 0.7%, is reproduced separately",
    "num-1",
)
rep(
    "Window and route failures barely move (≈2–4% throughout); the shield trades a fraction of window violations for the late handovers it removes, exactly as Eq. (3) predicts.",
    "Window and route failures barely move (≈2–4% throughout); the shield trades a fraction of window violations for the late handovers it removes, exactly as Eq. (3) predicts.",
    "noop",
)
rep(
    "14.8% for an identical-architecture ablation that never mines knowledge, 0.6% for the full system.",
    "14.8% for an identical-architecture ablation that never mines knowledge, 0.6% for the mined-rule campaign arm.",
    "num-2",
)
rep(
    "p50 = 7.08 s with 10,602 attempts at risk, p90 = 13.08 s with 2,069, p95 = 15.81 s with 1,040), and whether",
    "p50 = 7.08 s with 10,602 attempts at risk, p90 = 13.08 s with 2,069, p95 = 15.81 s with 1,040; the 15.80 s quoted in Section IV-C is the |lat| ≥ 70° band, and the 0.01 s difference is the band definition), and whether",
    "p95-band",
)
rep(
    "| advance bucket (s) | attempts | exact events | right-censored | competing risk | S_KM(bucket end) |",
    "| advance bucket (s) | attempts | exact events | right-censored | competing risk | S_KM(bucket end) |",
    "noop2",
)

P.write_text(t, encoding="utf-8")
print("done")
