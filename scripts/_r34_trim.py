"""R34 part 2: three compressions to hold 16 pages (numbers preserved)."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def sub_para(start: str, new: str, label: str):
    global t
    i = t.find(start)
    if i < 0:
        print("  MISS", label)
        return
    j = t.find("\n\n", i)
    old = len(re.findall(r"[A-Za-z0-9']+", t[i:j]))
    t = t[:i] + new + t[j:]
    done.append(f"{label}: {old}->{len(re.findall(chr(39), new)) if False else len(re.findall(r'[A-Za-z0-9]+', new))}w")


sub_para("All four orderings survive the change of window.",
         "All four orderings survive the change of window. Shielded beats unshielded in every instance: the deployed arm "
         "is 0.38–0.92 pp above the mined 16 s rule and 0.86–1.59 pp above the same-rule PPO-MLP baseline (differences "
         "taken from the two-decimal values printed in Table VII), and the deployed arm and the tuned constant are "
         "within 0.03 pp of each other in all four instances (93.36 vs 93.33, 91.67 vs 91.67, 93.03 vs 93.06, 92.91 vs "
         "92.91)—the competition the paper reports as a tie rather than a win. The decision-layer shield beats the best "
         "reward penalty by 9.4–11.0 pp. What a reader should look at when judging optimism is the difference between "
         "the evaluation-window column and the lockbox columns: it is small relative to the effect of the constraint "
         "itself (21–23 pp).",
         "orderings paragraph")

sub_para("Table IXc gives the four reference points.",
         "Table IXc gives the four reference points. The fixed threshold loses 5.2 pp across the drift (95.8% to 90.6%). "
         "The loop detects the drift in **one chunk** (15 decision epochs, ~150 s of twin time) and spends 52 polar probe "
         "attempts, 1.7% of the stream. The gate then *rejects* its own candidate: at +2 s the replay predicts no net "
         "gain, because the extra lead buys late successes at the price of window failures—the trade-off of Table V—so "
         "the loop rolls back to 18 s and ends at 89.7%, below the fixed threshold and below the EWMA quantile (93.6%). "
         "We report this as a failure of replay-based admission under drift, not as a demonstrated recovery.",
         "closed loop paragraph")

sub_para("Remark (scope). A universal claim that",
         "Remark (scope). A universal claim that no objective computed from such outcomes can identify the bound would be "
         "false, and we do not make it: binary outcomes do carry information wherever the advances reach, and the reward "
         "penalty of Proposition 1 likewise carries information through L(a). The correct and narrower statement is "
         "Claim 2: in passive operation the informative region is *thinly* exercised (705 attempts out of 8,682), so "
         "within any affordable sample budget the bound is effectively invisible to a learner fed by the passive "
         "stream—until an experiment changes the support and pays for the coverage it needs.",
         "remark scope")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", done)
