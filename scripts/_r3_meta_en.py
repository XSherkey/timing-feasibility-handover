"""T1-05 — remove review-response meta-commentary from the manuscript body (EN)."""
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


rep("Two grid points must be kept apart here, because an earlier draft conflated them.",
    "Two grid points must be kept apart here.", "prop1-corollary")
rep("An earlier draft wrote \"three harmful ones\"; the count is four. Without the replay stage",
    "Without the replay stage", "gate-count")
rep("Four orderings are tested, each with an explicit pairing, because an earlier draft left them ambiguous.",
    "Four orderings are tested, each with an explicit pairing.", "lockbox-orderings")
rep("An earlier draft called the second pairing \"shielded full vs shielded PPO-MLP\", which was ambiguous because the two arms carry different thresholds. Note",
    "The second pairing compares arms that carry different thresholds, so it answers a different question. Note",
    "pairing-note")
rep("so the tolerance is **≤ 1.20 pp** (an earlier draft said \"within 1 pp\", which the numbers do not support).",
    "so the tolerance is **≤ 1.20 pp**.", "tolerance")
rep("We state this as a table because a prose explanation of this point in an earlier version tried to reconcile an equality that does not hold, and a reviewer correctly called it out.",
    "We state this as a table because prose invites an equality that does not hold.", "ledger-intro")
rep("so we report the counts—and we now report them **separately for the two log regimes**, because an earlier version pooled them and a reviewer correctly objected that 91% of the pooled mass sat at 16 s.",
    "so we report the counts, **separately for the two log regimes**, because pooling them would confound the executed rule's own signature with passive coverage.",
    "appendixD-pooling")
rep("(An earlier version reported only the pooled table, which is where the 91% mass came from; the correction changes the percentages in Section IV-C from \"67 of 22,807 ≈ 0.3%\" to \"705 of 8,682 ≈ 8.1%\", and removes the \"two orders of magnitude\" phrasing, which the passive data do not support.)",
    "The percentages in Section IV-C are computed on the passive panel (705 of 8,682 ≈ 8.1%), not on this one.",
    "appendixD-parenthetical")
rep("*Probe the deployed policy.* An earlier version ran the probe inside the training loop, right after the first chunk, estimating the threshold for a policy that was not the one eventually deployed",
    "*Probe the deployed policy.* A probe run inside the training loop estimates the threshold of a policy that is not the one eventually deployed",
    "probe-history")
rep("Boundaries are stated plainly:", "Limits are explicit:", "abstract-plainly")
rep("*Scope—stated plainly, because it is easy to overclaim.*", "*Scope.*", "prop1-scope")
rep("Two consequences, stated plainly.", "Two consequences follow.", "ledger-consequences")
rep("One selection caveat, stated plainly:", "One selection caveat:", "lambda-caveat")
rep("Two further honesty notes about what the KM curve is and is not.",
    "Two further remarks on what the KM curve is and is not.", "km-notes")
rep("One number needs the right reading, and we state it rather than let a reader misread it:",
    "One number needs care:", "lockbox-reading")
rep("an estimator-bias phenomenon we report as measured, not as a law",
    "an estimator-bias phenomenon we report empirically", "probe-law")

P.write_text(t, encoding="utf-8")
print("applied:", done)
