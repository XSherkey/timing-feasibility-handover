"""R20 part 1: create the supplementary folder, move Nomenclature / Table II / Table VIII / proofs into it."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
SUPP = D / "supplementary"
SUPP.mkdir(exist_ok=True)

main = D / "paper_en.md"
supp = D / "supplementary" / "supp_en.md"
t = main.read_text(encoding="utf-8")
s = supp.read_text(encoding="utf-8") if supp.exists() else ""
moved = []


def cut_block(start_marker: str, end_marker: str | None = None, include_end: bool = True):
    """Remove a block from the main text and return it."""
    global t
    i = t.find(start_marker)
    if i < 0:
        return None
    if end_marker is None:
        j = t.find("\n\n", i)
        j = len(t) if j < 0 else j
    else:
        k = t.find(end_marker, i)
        if k < 0:
            return None
        j = t.find("\n\n", k) if include_end else k
        j = len(t) if j < 0 else j
    block = t[i:j]
    t = t[:i] + t[j:]
    return block


# ---- 1. Nomenclature -----------------------------------------------------
block = cut_block("## Nomenclature", "## I. Introduction")
if block:
    moved.append("Nomenclature")
    s = s.rstrip() + "\n\n## Appendix F. Nomenclature\n\n" + block.replace("## Nomenclature", "").strip() + "\n"
    t = t.replace("## I. Introduction", "## I. Introduction", 1)
    # pointer right after the abstract / index terms
    k = t.find("## I. Introduction")
    ptr = ("*Nomenclature.* Every symbol used in the paper is defined at first use; the consolidated list, with "
           "the four arm names and the three bands, is Appendix F of the supplementary material.\n\n")
    t = t[:k] + ptr + t[k:]

# ---- 2. Table II (threshold ledger) --------------------------------------
i = t.find("**Table II. Threshold ledger")
if i > 0:
    j = t.find("\n\n", t.find("| Reward-", i))
    if j < 0:
        j = t.find("\n\n", t.find("|", i))
    block = t[i:j]
    t = t[:i] + ("*Threshold ledger.* Which rule each reported number executes is tabulated in Appendix G of the "
                 "supplementary material; no number in this paper depends on reading that table.\n") + t[j:]
    moved.append("Table II")
    s = s.rstrip() + "\n\n## Appendix G. Threshold ledger\n\n" + block + "\n"

# ---- 3. Table VIII (drift ladder) ----------------------------------------
i = t.find("**Table VIII. Drift ladder")
if i > 0:
    j = t.find("\n\n", t.find("| δ = +4.4 s", i))
    if j < 0:
        j = t.find("\n\n", t.find("|", t.find("|", i) + 2))
    block = t[i:j]
    t = t[:i] + ("*Drift ladder.* The per-regime ladder behind Fig. 7 is Table H1 of the supplementary material; "
                 "the figure carries the same numbers.\n") + t[j:]
    moved.append("Table VIII")
    s = s.rstrip() + "\n\n## Appendix H. Drift ladder\n\n" + block + "\n"

# ---- 4. proofs -----------------------------------------------------------
proofs = re.findall(r"\*Proof\.\*[\s\S]*?□", t)
for n, pr in enumerate(proofs, 1):
    t = t.replace(pr, "")
print("proofs moved:", len(proofs))
if proofs:
    s = s.rstrip() + "\n\n## Appendix I. Proofs\n\n" + "\n\n".join(proofs) + "\n"
    moved.append("proofs")

# tidy double blank lines left behind
t = re.sub(r"\n{3,}", "\n\n", t)

main.write_text(t, encoding="utf-8")
supp.write_text(s, encoding="utf-8")
print("moved:", moved)
print("main chars:", len(t), "supp chars:", len(s))
