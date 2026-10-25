"""R10 part 1: unify the protocol narrative and fix the stale corollary numbers."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:60]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# ---- 1. Section V-E: the gate admits on validation replay only -----------
i = t.find("be precise rather than comforting, and the precise version is given in Section VI-A")
if i < 0:
    raise SystemExit("V-E protocol sentence not found")
j = t.find("\n\n", i)
VE = ("be precise rather than comforting. Discovery uses training-time logs only (0–60%). Every subsequent "
      "selection—the gate's admission, the probe that fixes τ∗, the penalty coefficient λ and the margin m—is "
      "made on the validation window (65–75%), and the gate admits a candidate only if its validation replay "
      "gain exceeds 5 pp with a positive lower bound. Neither the evaluation window (82–95%) nor any lockbox "
      "instance participates in admission: they are scored after the fact, and the two-protocol statement in "
      "Section VI-A says which reported number belongs to which protocol. An earlier draft of this paper "
      "described the gate as replaying on the evaluation window as well; that is the archival protocol of "
      "Section VI-A, it applied to the first round of results only, and no number reported here depends on it.")
t = t[:i] + VE + t[j:]
done.append("VE-protocol")

# ---- 2. Section VI-A data-flow paragraph ---------------------------------
i = t.find("Three calibration steps, however, touch the evaluation window")
if i < 0:
    raise SystemExit("VI-A data-flow paragraph not found")
j = t.find("\n\n", i)
VI_A = ("All three calibration steps—the audit gate's replay, the probe that fixes τ∗, and the λ and margin "
        "selection—are made on the validation window. The gate admits a candidate only if its validation replay "
        "gain exceeds 5 pp with a positive lower bound; the evaluation window never enters that decision. The "
        "archival numbers of Tables III–IX, XI and XII were produced in an earlier round in which those same "
        "three selections happened to be evaluated on the evaluation window; that round is reported here only "
        "because it reproduces the original pipeline, and Section VI-I shows that the three-way protocol returns "
        "the same selections (τ∗ = 16 s, λ = 8, m = 2) and therefore the same numbers to 0.05 pp. No claim in "
        "this paper rests on the archival structure.")
t = t[:i] + VI_A + t[j:]
done.append("VIA-dataflow")

# ---- 3. Limitation 7: describe the three-way residual limitation ----------
i = t.find("7. **Lockbox scope.**")
if i < 0:
    raise SystemExit("Limitation 7 not found")
j = t.find("\n\n", i)
L7 = ("7. **Lockbox scope.** The three-way protocol moves every selection onto the validation window and scores "
      "the lockbox only afterwards, on three epoch-shifted instances (±2/7/14 days of orbital phase). What it "
      "does not do is re-run *discovery*: the narrative, the predicate proposals and the checkpoints themselves "
      "were produced once, on the 0–60% training window, and are held fixed. The lockbox therefore bounds the "
      "optimism of calibration, not the optimism of discovery. Two further caveats: the deployed arm and the "
      "tuned constant are within 0.03 pp of each other on every lockbox instance, so the calibration buys "
      "automation and auditability rather than accuracy; and the lockbox twins share the constellation, traffic "
      "model and horizon structure with calibration, so generalization beyond this twin family is untested.")
t = t[:i] + L7 + t[j:]
done.append("L7")

# ---- 4. Proposition 3 corollary: current factorial numbers ----------------
rep("without the shield they span 49.8–90.0% (sd 13.2); with the deployed τ = 18 s shield they span 92.7–93.7% (sd 0.26).",
    "without the shield they span 49.8–90.0% (sd 13.2); with the deployed τ = 18 s shield they span 93.3–93.5% "
    "(sd 0.05, Table C1).", "prop3-corollary")

# ---- 5. the late-share sentence: say which threshold ----------------------
rep("the realized post-shield late-handover share is 0.9% against ε = 5%",
    "the realized post-shield late-handover share is 0.93% at τ = 16 s and 0.00% at τ = 18 s, against ε = 5%",
    "late-share")

# ---- 6. the "six candidates" vs 26-bank mapping --------------------------
rep("The gate is not decorative. In a controlled study we handed it six candidates an LLM could plausibly "
    "propose, with the following held-out deltas and verdicts (the full bank of 26 candidates is summarized in "
    "Table XI):",
    "The gate is not decorative. The 26-candidate bank of Table XI is the full study: seven candidates measured "
    "harmful, three neutral, sixteen good. It contains the six natural candidates an LLM plausibly proposes "
    "(reported individually below) plus twenty variants that change one element of the predicate—scope, "
    "magnitude, field—so that the bank is not built around the rule the gate already knows. The six natural "
    "candidates, with their held-out deltas and verdicts:", "gate-mapping")

p.write_text(t, encoding="utf-8")
print("applied:", done)
