"""R20 part 8: rebuild the supplement deterministically from the last archived full source (v59)."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
HIST = D / "_history"
src = sorted(HIST.glob("paper_en_v59_*.md"))[-1]
t = src.read_text(encoding="utf-8")
print("source:", src.name, len(t), "chars")


def grab(start: str, end: str) -> str:
    i = t.find(start)
    j = t.find(end, i)
    if i < 0 or j < 0:
        print("  MISS", start, i, j)
        return ""
    return t[i:j].strip()


nomen = grab("## Nomenclature", "## I. Introduction")
appendix_ad = grab("## Appendix A.", "## Appendix E.")
appendix_e = grab("## Appendix E.", "## References")

# tables that are now supplementary
i = t.find("**Table II. Threshold ledger")
j = t.find("\n\n", t.find("| Reward-", i)) if i > 0 else -1
if j < 0:
    j = t.find("\n\n", t.find("|", i) + 2)
ledger = t[i:j].strip() if i > 0 else ""

i = t.find("**Table VIII. Drift ladder")
j = t.find("\n\n", t.find("| δ = +4.4 s", i)) if i > 0 else -1
if j < 0:
    j = t.find("\n\n", t.find("|", i) + 2)
ladder = t[i:j].strip() if i > 0 else ""

proofs = re.findall(r"\*Proof\.\*[\s\S]*?□", t)
i = t.find("*Proof sketch.*")
sketch = ""
if i > 0:
    j = t.find("□", i)
    k = t.find("\n\n", j)
    sketch = t[i:k].strip()

TITLE = ("**Supplementary Material for “Probe-Calibrated Conservative Injection of Handover Constraints for "
         "Autonomous LEO Satellite Networks”**\n\nThis document carries the material the main text cites but does "
         "not reproduce: the reproduction commands, the latency note, the per-seed tables, the support audit and "
         "the 26-candidate gate bank, the prompt appendix, the consolidated nomenclature, the threshold ledger, the "
         "drift-ladder numbers behind Fig. 7, and the proofs. Table numbers keep their main-text names (C1, C2, "
         "D1A, D1B, D2, H1) so they cannot be confused with main-text tables.\n")

H1_HEAD = "## Appendix H. Drift ladder\n\n**Table H1. Drift ladder (polar HSR, |lat| ≥ 70°, campaign policies, traffic seed 0, identical episodes, n = 10; the numbers plotted in Fig. 7).**\n\n"
H1_BODY = ("| δ | oracle | τ = 18 s (fixed) | 16 s rule (as a shield) | tuned 18 s constant | reward λ = 8 | no knowledge |\n"
           "|---|---|---|---|---|---|---|\n"
           "| 0 | 93.36 | 93.36 | 91.60 | 93.33 | 82.93 | 76.31 |\n"
           "| +2.0 s | 93.36 | 92.42 | 84.79 | 92.39 | 52.00 | 54.64 |\n"
           "| +3.2 s | 93.36 | 86.01 | 81.25 | 85.98 | 42.67 | 45.85 |\n"
           "| +4.4 s | 93.36 | 83.47 | 77.49 | 83.56 | 21.02 | 24.16 |\n")

parts = [TITLE]
if appendix_ad:
    parts.append(appendix_ad)
if appendix_e:
    parts.append(appendix_e)
if nomen:
    parts.append("## Appendix F. Nomenclature\n\n" + nomen.replace("## Nomenclature", "").strip())
if ledger:
    parts.append("## Appendix G. Threshold ledger\n\n" + ledger)
if ladder:
    parts.append("## Appendix H. Drift ladder\n\n" + ladder.replace("**Table VIII. Drift ladder", "**Table H1. Drift ladder"))
else:
    parts.append(H1_HEAD + H1_BODY)
if proofs or sketch:
    parts.append("## Appendix I. Proofs\n\n" + "\n\n".join(proofs) + ("\n\n" + sketch if sketch else ""))

supp = "supplementary/supp_en.md"
out = "\n\n".join(p for p in parts if p.strip())
(D / supp).write_text(out + "\n", encoding="utf-8")
print("supplement rebuilt:", len(out), "chars")
print("headings:", re.findall(r"^## .*", out, flags=re.M))
print("tables:", len(re.findall(r"^\*\*Table ", out, flags=re.M)))
