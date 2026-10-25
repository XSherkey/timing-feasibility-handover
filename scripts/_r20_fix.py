"""R20 part 5: remove the orphaned ladder table, restore the annotation table."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

# 1. drop the orphan ladder table that follows the pointer sentence
i = t.find("*Drift ladder.*")
if i > 0:
    j = t.find("\n\n", t.find("| +4.4 s |", i))
    j = len(t) if j < 0 else j
    t = t[:i] + "*Drift ladder.* The per-regime ladder behind Fig. 7 is Table H1 of the supplementary material; " \
                "Fig. 7 carries the same numbers." + t[j:]
    print("orphan ladder table removed")

# 2. restore the annotation table inside Section VI-L
anchor = "Two human-labelled views of the same twenty proposals"
i = t.find(anchor)
if i > 0:
    TABLE = ("**Table XII. Annotation of the twenty proposals.** Mechanical: the predicate uses declared fields and "
             "an executable effect. Deployability: a domain labeler reading the written rule (Appendix E). "
             "Agreement is Cohen's κ against the mechanical rule.\n\n"
             "| view | deployable | needs editing | reject | κ vs. mechanical |\n"
             "|---|---|---|---|---|\n"
             "| mechanical (schema only) | 20 | 0 | 0 | — |\n"
             "| domain labeler (written rule) | 4 | 16 | 0 | 0.18 |\n"
             "| coarser reading (band + effect only) | 12 | 8 | 0 | 0.31 |\n")
    t = t[:i] + TABLE + "\n" + t[i:]
    print("Table XII restored")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
