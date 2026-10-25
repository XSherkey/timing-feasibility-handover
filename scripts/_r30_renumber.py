"""R30: continuous main-text table numbering (I-VIII) and the last text fixes."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

# ---- 1. the archival reference sentence (contains a range, fix before renumbering)
old = ("The *archival* numbers (Tables II–IV, Fig. 5) use the evaluation-window probe; the *three-way* numbers "
       "(Table X, lockbox rows) use the validation-only probe,")
new = ("The *archival* numbers (Table III and, in the supplementary material, Tables G1 and M1; Fig. 5) use the "
       "evaluation-window probe; the *three-way* numbers (Table X, lockbox rows) use the validation-only probe,")
print("archival sentence:", t.count(old))
t = t.replace(old, new, 1)

# ---- 2. renumber main tables I..VIII in document order
#     I -> I, III -> II, VI -> III, IX -> IV, IXb -> V, IXc -> VI, X -> VII, Xb -> VIII
MAP = [("Table IXb", "@@T5@@"), ("Table IXc", "@@T6@@"), ("Table Xb", "@@T8@@"),
       ("Table IX", "@@T4@@"), ("Table X", "@@T7@@"), ("Table VI", "@@T3@@"),
       ("Table III", "@@T2@@"), ("Table I", "@@T1@@")]
for old_tag, sentinel in MAP:
    n = len(re.findall(re.escape(old_tag) + r"(?![A-Za-z])", t))
    t = re.sub(re.escape(old_tag) + r"(?![A-Za-z])", sentinel, t)
    print(f"  {old_tag} -> {sentinel}: {n}")

for sentinel, new_tag in (("@@T1@@", "Table I"), ("@@T2@@", "Table II"), ("@@T3@@", "Table III"),
                          ("@@T4@@", "Table IV"), ("@@T5@@", "Table V"), ("@@T6@@", "Table VI"),
                          ("@@T7@@", "Table VII"), ("@@T8@@", "Table VIII")):
    t = t.replace(sentinel, new_tag)

# ---- 3. one-decimal fix: good lower bound is the evaluation-column value
print("+6.2 present:", t.count("+6.2 to +21.6"))
t = t.replace("sixteen are good (+6.2 to +21.6 pp)", "sixteen are good (+6.4 to +21.6 pp)")

p.write_text(t, encoding="utf-8")

# ---- 4. verify
caps = re.findall(r"\*\*Table ([IVX]+)\.", t)
print("captions in order:", caps)
refs = re.findall(r"Table ([IVX]+)(?![A-Za-z])", t)
print("all references:", sorted(set(refs), key=lambda r: ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"].index(r) if r in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"] else 99))
unknown = [r for r in set(refs) if r not in caps]
print("references to non-existent tables:", unknown)
print("leftover sentinels:", t.count("@@T"))
