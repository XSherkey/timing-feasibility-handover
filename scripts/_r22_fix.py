"""R22: fix the four real defects reported in review 16 (the other claims are extraction artefacts)."""
from __future__ import annotations

import json
import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = p.read_text(encoding="utf-8")
supp = supp_path.read_text(encoding="utf-8")
edits = []


def sub(old, new, label, target="main"):
    global t, supp
    src = t if target == "main" else supp
    n = src.count(old)
    if n != 1:
        print("  MISS", label, n)
        return
    if target == "main":
        t = t.replace(old, new, 1)
    else:
        supp = supp.replace(old, new, 1)
    edits.append(label)


# ---- 1. Table XII: replace the invented kappa values with the measured ones ----
ag = json.loads((Path(__file__).resolve().parents[1] / "results" / "routeA_r3" / "llm_proposals" /
                 "agreement.json").read_text(encoding="utf-8"))
print("measured:", {k: ag[k] for k in ("human_accept_rate", "judge_rate", "mechanical_rate",
                                       "kappa_human_judge", "kappa_human_mech", "kappa_judge_mech",
                                       "agreement_human_judge")})

old_tab = t[t.find("**Table XII."):t.find("\n\n", t.find("| coarser reading", t.find("**Table XII.")))]
new_tab = ("**Table XII. Annotation of the twenty proposals.** Mechanical: the predicate uses declared fields and an "
           "executable effect. Human: a domain labeler reading the written rule (Appendix E). Judge: an independent "
           "second reading that saw only the band and the effect. κ is Cohen's κ against the mechanical rule; the "
           "two operational views agree with each other at κ = 0.23 on 80% raw agreement.\n\n"
           "| view | deployable | needs editing | reject | κ vs. mechanical |\n"
           "|---|---|---|---|---|\n"
           "| mechanical (schema only) | 20 | 0 | 0 | — |\n"
           "| human labeler (written rule) | 4 | 16 | 0 | 0.00 |\n"
           "| independent judge (band + effect) | 2 | 18 | 0 | 0.00 |\n")
t = t.replace(old_tab, new_tab, 1)
edits.append("Table XII kappa corrected")

# ---- 2. Table XI dangling reference -> Table K1 -------------------------
sub("The 26-candidate bank of Table XI is the full study",
    "The 26-candidate bank of Table K1 in the supplementary material is the full study",
    "Table XI -> K1")

# ---- 3. Table IX caption: state that A6 carries no measurements ----------
i = t.find("**Table IX.")
if i > 0:
    j = t.find("\n\n", i)
    cap = t[i:j]
    if "A6" not in cap:
        cap2 = cap.rstrip()
        if cap2.endswith("**"):
            cap2 = cap2[:-2] + " A6 carries no measurements and is not reported.**"
        else:
            cap2 = cap2 + " A6 carries no measurements and is not reported."
        t = t[:i] + cap2 + t[j:]
        edits.append("Table IX caption notes A6")

# ---- 4. Table H1 body is missing in the supplement -----------------------
if supp.count("| 0 | 93.36 |") == 0:
    i = supp.find("**Table H1.")
    if i > 0:
        j = supp.find("\n\n", i)
        BODY = ("\n\n| δ | oracle | τ = 18 s (fixed) | 16 s rule (as a shield) | tuned 18 s constant | reward λ = 8 | no knowledge |\n"
                "|---|---|---|---|---|---|---|\n"
                "| 0 | 93.36 | 93.36 | 91.60 | 93.33 | 82.93 | 76.31 |\n"
                "| +2.0 s | 93.36 | 92.42 | 84.79 | 92.39 | 52.00 | 54.64 |\n"
                "| +3.2 s | 93.36 | 86.01 | 81.25 | 85.98 | 42.67 | 45.85 |\n"
                "| +4.4 s | 93.36 | 83.47 | 77.49 | 83.56 | 21.02 | 24.16 |")
        supp = supp[:j] + BODY + supp[j:]
        edits.append("Table H1 body restored")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
supp_path.write_text(supp, encoding="utf-8")
print("edits:", edits)
