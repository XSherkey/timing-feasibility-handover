"""R24: fix the checkable inconsistencies raised in review 18."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = p.read_text(encoding="utf-8")
supp = supp_path.read_text(encoding="utf-8")
done = []


def rep(old, new, label, target="main"):
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
    done.append(label)


# 1. prose said the second reading judged 12/20; the sealed data says 2/20
rep("a domain labeler judged 4 of 20 deployable as written, while a coarser reading judged 12.",
    "a domain labeler judged 4 of 20 deployable as written, while an independent second reading—which saw only the "
    "band and the effect—judged 2; the two agree on 16 of 20 (κ = 0.23).",
    "XII prose 12 -> 2")

# 2. the 8 s natural candidate: align with the sealed bank (G02, +0.8 held out, neutral)
rep("an 8 s polar minimum lead (−1.5 pp, rejected as harmful)",
    "an 8 s polar minimum lead (+0.8 pp held out, neutral, therefore rejected)",
    "8 s candidate numbers")

# 3. Figure number for the lambda grid
rep("*Grid.* The full λ grid behind Fig. 4 is Table M1 of the supplementary material.",
    "*Grid.* The full λ grid behind Fig. 6 is Table M1 of the supplementary material.",
    "Fig. 4 -> Fig. 6")

# 4. Fig. 5 caption: five bars plus a quoted reference value
rep("All five bars come from one protocol, so the differences between them are protocol-free",
    "The five bars come from one protocol (the deployed 93.36 is quoted above for reference, not drawn as a sixth "
    "bar), so the differences between them are protocol-free",
    "five bars clarified")

# 5. lambda = 64 variance: text said 17.0, the sealed table says 17.3
rep("with its variance exploding to 17.0 and the per-attempt mean lead",
    "with its variance exploding to a standard deviation of 17.3 and the per-attempt mean lead",
    "lambda64 sd")

# 6. dangling table references after the supplementary move
rep("(Table IV, Fig. 6)", "(Table M1 of the supplementary material, Fig. 6)", "Table IV -> M1")
rep("arises of one configuration (Table VII).", "arises of one configuration (Table L1 of the supplementary material).",
    "Table VII -> L1")

# 7. scope the "0.7 pp" claim
rep("the learned component is worth about 0.7 pp;",
    "the learned component is worth about 0.7 pp in this pipeline;", "0.7 pp scoped")

t = re.sub(r"\n{3,}", "\n\n", t)

# 8. D2 caption: explain magnitudes beyond the executable grid
i = supp.find("**Table D2.")
if i > 0:
    j = supp.find("\n\n", i)
    cap = supp[i:j].rstrip()
    if "executable grid" not in cap:
        cap = cap[:-2] + (" Two proposals (G04 at 28 s, G19 at 30 s) exceed the 26 s action grid: their magnitude is "
                          "executed at the grid maximum, which is why the two rows carry identical gains, and they are "
                          "kept to show that the gate does not distinguish proposals that differ only above the "
                          "executable range.**") if cap.endswith("**") else cap
        supp = supp[:i] + cap + supp[j:]
        done.append("D2 clamping note")

p.write_text(t, encoding="utf-8")
supp_path.write_text(supp, encoding="utf-8")
print("applied:", done)
