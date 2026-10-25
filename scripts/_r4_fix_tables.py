"""R4 (v16) part 1: Tables IV and VI prose, duplicate lockbox table, arm count.

Fixes from review 9:
  * Table IV rebuilt at n = 10 (drift_margin), caption no longer claims 5 seeds.
  * Section VI-G prose now matches the rebuilt Table VI.
  * the old lockbox table in VI-A is removed (superseded by Table VIII).
  * "nine arms" -> eight, with A6 explained.
"""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


# ---------------------------------------------------------------- Table IV
start = t.find("**Table IV. Drift response")
end = t.find("\n\n", t.find("| probed", start))
if start < 0 or end < 0:
    raise SystemExit("Table IV block not found")
TABLE4 = """**Table IV. Drift response (polar HSR, mean ± sd, n = 10 policy seeds, traffic seed 0, polar band |lat| ≥ 70°; the two constant-controller rows are policy-independent and therefore have sd 0.00).**

| extra acquisition latency | 0 | +2.0 s | +3.2 s | +4.4 s |
|---|---|---|---|---|
| tuned constant, fixed 18 s | 93.33 | 92.39 | 85.98 | 83.56 |
| constant re-probed on validation + 2 s margin | 93.33 | 93.20 | 93.20 | 93.20 |
| shielded policies, fixed 18 s rule | 93.36 ± 0.05 | 92.42 ± 0.05 | 86.01 ± 0.06 | 83.47 ± 0.34 |
| shielded policies, threshold re-probed + 2 s margin | 93.36 ± 0.05 | 93.23 ± 0.05 | 93.23 ± 0.05 | 93.23 ± 0.05 |
| probed τ∗ (five policy seeds) | 16 (5/5) | 18 (5/5) | 20 (5/5) | 22 (4/5), 20 (1/5) |"""
t = t[:start] + TABLE4 + t[end:]
done.append("table4")

# ---------------------------------------------------------------- drift prose
rep("These are measured statements over five seeds and three regimes, not a probabilistic guarantee;",
    "These are measured statements over ten policy seeds and four regimes, not a probabilistic guarantee;",
    "drift-n")
rep("The last cell is the identifiability limit of Proposition 4, visible in a single grid entry: at +4.4 s one of five seeds probes 20 s instead of 22 s and lands at 91.1% against the 94.1% optimum.",
    "The last row is the identifiability limit of Proposition 4, visible in a single grid entry: in the five-seed probe study at +4.4 s one seed returns 20 s instead of 22 s. The drift ladder itself uses the regime median (22 s), which is why the re-probed arms hold 93.2% there; a deployment that trusted the single deviating probe would sit one grid step low.",
    "drift-probe-note")
rep("calibration at nominal physics buys nothing (94.0 vs 94.0)",
    "calibration at nominal physics buys nothing (93.33 vs 93.33 for the constant, 93.36 vs 93.36 for the shield)",
    "drift-nominal")
rep("The margin itself is insurance, not gain: m = 2 leaves every tested seed ≥ 93.2% across the three regimes, m = 4 is no better, and m = 0 leaves one seed at 92.4%.",
    "The margin itself is insurance, not gain: m = 2 holds 93.2–93.4% across the four regimes, m = 4 is no better, and m = 0 drops to 92.44% at nominal physics.",
    "drift-margin")

# ---------------------------------------------------------------- VI-G prose
old_g_start = t.find("**Alternative physics.**")
old_g_end = t.find("\n\n", t.find("absent from the test set.", old_g_start))
NEW_G = ("**Alternative physics.** Two perturbed twins test whether the conclusions are artefacts of one "
         "configuration (Table VI). With the polar seam penalty disabled, the shield lifts both families to "
         "95.5% (from 67.7% for the full-system policies and 78.1% for PPO-MLP); late handovers dominate "
         "before the shield (28.5% and 18.3% of attempts) and fall to 0.0% after it. With feeder capacity "
         "reduced to three slots per gateway the same shield lifts the arms only to 69.5–70.0% (from 39.1% "
         "and 46.4%), because `no_route` becomes the dominant failure class at 26–30% of attempts—timing "
         "feasibility is restored, routing capacity is binding. Both outcomes are what the theory predicts: "
         "the shield repairs the feasibility factor, and the ceiling afterwards is set by whatever failure "
         "class is next. We regard a method whose failure modes are predictable as more deployable than one "
         "whose are merely absent from the test set.")
if old_g_start < 0 or old_g_end < 0:
    raise SystemExit("VI-G paragraph not found")
t = t[:old_g_start] + NEW_G + t[old_g_end:]
done.append("vi-G")

# ---------------------------------------------------------------- duplicate lockbox table in VI-A
i = t.find("| Instance | full, no shield |")
if i > 0:
    j = t.find("\n\n", t.find("| −2 d", i))
    t = t[:i] + t[j + 2:]
    done.append("drop-dup-lockbox")
rep("Three lockbox instances are evaluated—epoch_doy 299.25 (+7 d), 306.25 (+14 d), and 290.25 (−2 d)—with the frozen full-system policies, the PPO-MLP baseline, and the reward-penalty arm, each under no shield, the mined 16 s rule, the validation-calibrated τ_used = 18 s shield, and, for the full-system policies, the tuned 18 s constant (mean ± sd over seeds; per-seed values in the sealed artefacts). In the table, *full* abbreviates \"full-system policies\"; the mined-rule campaign arm of Table II is a different arm and is not part of this table:",
    "Three lockbox instances are evaluated—epoch_doy 299.25 (+7 d), 306.25 (+14 d), and 290.25 (−2 d)—with the frozen full-system policies, the PPO-MLP baseline, and the reward-penalty arm, each under no shield, the mined 16 s rule, the validation-calibrated τ_used = 18 s shield, and, for the full-system policies, the tuned 18 s constant. The results are reported in Table VIII, which uses one policy set and one traffic seed for every arm so that the rows are comparable.",
    "viA-lead")

# ---------------------------------------------------------------- arms count
rep("Table VII reports the nine arms.", "Table VII reports the eight single-intent arms; the ninth, A6 (a fresh knowledge graph per intent), only differs from A0 in the multi-intent protocol and is therefore reported with the cross-intent experiment in Section VI-F.", "arms-count")

p.write_text(t, encoding="utf-8")
print("applied:", done)
