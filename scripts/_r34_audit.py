"""FINAL pre-submission audit of v88."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from docx import Document

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
t = (D / "paper_en.md").read_text(encoding="utf-8")
s = (D / "supplementary/supp_en.md").read_text(encoding="utf-8")
fails = []


def check(label, ok):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        fails.append(label)


print("=== main structure ===")
caps = re.findall(r"\*\*Table ([IVX]+)\.", t)
check("tables I..VIII in order", caps == ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"])
check("figures 1..9 in order", re.findall(r"\*\*Fig\. (\d)\.\*\*", t) == [str(i) for i in range(1, 10)])
check("equations (1)..(5)", re.findall(r"\((\d)\)\s*$", t, flags=re.M) == ["1", "2", "3", "4", "5"])
inside = t[t.find("## VI."):t.find("## VII.")]
check("VI subsections A..O unique", re.findall(r"^### ([A-O])\.", inside, flags=re.M) == list("ABCDEFGHIJKLMNO"))
refs = [m.group(1) for m in re.finditer(r"Tables? ([IVX]+)(?![A-Za-z])", t)]
check("all table refs resolve", all(r in caps for r in refs))
check("no 'Table IX' / 'Table X'", t.count("Table IX") == 0 and t.count("Table X ") == 0)

print("\n=== review-27 items ===")
check("Prop 1 left inequality >= and right <=",
      "λ·[p(a*−Δ) − p(a*)] ≥ Δr(a*−Δ, a*)  and  λ·[p(a*) − p(a*+Δ)] ≤ Δr(a*, a*+Δ)" in t)
check("Prop 1 boundary caveat", "for a* at the edge of the grid only the interior neighbour exists" in t)
check("Prop 4 estimand is the observable curve", "π̂(a) = P(late at commanded advance a" in t)
check("Prop 4 simulator privilege stated", "simulator privilege" in t)
check("Prop 4 deployment without T_z", "A real deployment that cannot report T_z" in t)
check("probe budget 2->16 (no '8 episodes')", "2 to 16 episodes per advance" in t and "from 2 to 8 episodes" not in t)
check("Fig. 6 eight points incl. lambda=0", "eight points—the seven coefficients" in t)
check("abstract separation wording", "separate materially only at +3.2 s" in t)
check("abstract interval scoped", "in the settings we test its length" in t)
check("A7 caveat present", "pipeline-level ablation rather than a pure component ablation" in t)

print("\n=== supplement ===")
supp_caps = re.findall(r"\*\*Table ([A-Z]\d+[A-Z]?)\.", s)
check("supp tables include G2/G3", "G2" in supp_caps and "G3" in supp_caps)
check("supp proof conditioned on A_Π", "Condition on the protected scope A_Π" in s)
check("D2 has the rule column", "| id | executed rule | validation gain (pp) | admit? |" in s)
main_refs = set(re.findall(r"Table ([A-Z]\d+[A-Z]?)", t))
check("every main->supp table ref exists", main_refs.issubset(set(supp_caps)))

print("\n=== rendered files ===")
for f in ("Paper_EN_IEEE_v88.docx", "supplementary/supp_en.docx"):
    xml = zipfile.ZipFile(D / f).read("word/document.xml").decode("utf-8")
    txt = re.sub(r"<[^>]+>", "", xml)
    doc = Document(str(D / f))
    check(f"{f}: no literal '**'", txt.count("**") == 0)
    check(f"{f}: title metadata set", bool((doc.core_properties.title or "").strip()))
    check(f"{f}: 'Table IX' absent", "Table IX" not in txt)

print("\nFAILURES:", fails if fails else "none")
