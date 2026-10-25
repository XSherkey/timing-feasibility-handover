"""R31: the four residuals of review 24."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
main = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = main.read_text(encoding="utf-8")
s = supp_path.read_text(encoding="utf-8")
done = []

# ---- 1. VI-A protocol paragraph rewritten per table ------------------------
i = t.find("Tables III and VI report archival numbers")
if i < 0:
    raise SystemExit("VI-A protocol sentence not found")
j = t.find("Nothing else differs", i)
NEW = ("Tables II and III report archival results, as does the evaluation-window column of Table VII. Table IV uses "
       "validation-only selection and adds a single lockbox column scored without further selection; Table V selects "
       "its guard on the validation window and scores the test window once. Table VI is a protocol of its own—one "
       "continuous stream with an unannounced drift—and belongs to neither of the two calibration protocols. The last "
       "three columns of Table VII are the three-way lockbox instances, and the archival drift and gate tables (H2, "
       "K1) plus the annotation table (J1) live in the supplementary material. ")
t = t[:i] + NEW + t[j:]
done.append("VI-A protocol paragraph")

# ---- 2. Appendix J: Table V reference is stale ----------------------------
old = "Their value is only visible in the protocols designed to expose it (Tables V and Fig. 8)."
new = ("Their value is visible only in the cross-intent and gate-stress protocols (Table III, Fig. 8, and Table K1 of "
       "the supplementary material).")
if s.count(old) == 1:
    s = s.replace(old, new, 1)
    done.append("Appendix J reference")
else:
    print("  MISS appendix J", s.count(old))

# ---- 3. Table M1 caption: Table X no longer exists ------------------------
old = "the shield column is the deployed probe-calibrated algorithm of Table X)"
new = "the shield column is the deployed probe-calibrated algorithm, arm A0 in Table IV of the main text)"
if s.count(old) == 1:
    s = s.replace(old, new, 1)
    done.append("Table M1 caption")
else:
    print("  MISS M1", s.count(old))

# ---- 4. stray markdown in four captions: make each a single bold span -----
CAPS = [
    (t, "**Table V. The second constraint family", "n = 10).** Protocol: probe and guard selection on validation; arms scored on the test window.",
     "**Table V. The second constraint family (polar HSR, |lat| ≥ 70°, campaign checkpoints, traffic seed 0, n = 10). "
     "Protocol: probe and guard selection on validation, arms scored on the test window.**"),
    (t, "**Table VIII. Where the variance lives", "n = 25 cells per arm).** The two columns are the standard deviations of the per-policy and per-traffic means; the last column is the share of total sum of squares.",
     "**Table VIII. Where the variance lives (polar HSR, five policy seeds × five traffic seeds, n = 25 cells per arm). "
     "The two columns are the standard deviations of the per-policy and per-traffic means; the last column is the share "
     "of total sum of squares.**"),
]
for text, start, old_tail, new_cap in CAPS:
    i = text.find(start)
    if i < 0:
        print("  MISS caption", start[:30])
        continue
    j = text.find("\n\n", i)
    if old_tail in text[i:j]:
        if text is t:
            t = t[:i] + new_cap + text[j:]
        done.append(f"caption {start[9:20]}")

# J1 caption in the supplement
start = "**Table J1. Annotation of the twenty proposals"
i = s.find(start)
if i > 0:
    j = s.find("\n\n", i)
    cap = s[i:j]
    if cap.count("**") > 2:
        new_cap = ("**Table J1. Annotation of the twenty proposals. Mechanical: the predicate uses declared fields and an "
                   "executable effect. Human: a domain labeler reading the written rule (Appendix E). Judge: an independent "
                   "second reading that saw only the band and the effect. κ is Cohen's κ against the mechanical rule; the "
                   "two operational views agree with each other at κ = 0.23 on 80% raw agreement.**")
        s = s[:i] + new_cap + s[j:]
        done.append("Table J1 caption")

# H2 caption
start = "**Table H2. Drift response"
i = s.find(start)
if i > 0:
    j = s.find("\n\n", i)
    cap = s[i:j]
    if cap.count("**") > 2:
        cap_new = cap.rstrip()
        # collapse the interior close/open pair: remove the '**' that ends the first sentence-span
        inner = cap_new[2:-2] if cap_new.endswith("**") else cap_new[2:]
        inner = inner.replace("Protocol: archival.**", "Protocol: archival.")
        s = s[:i] + "**" + inner + "**" + s[j:]
        done.append("Table H2 caption")

main.write_text(re.sub(r"\n{3,}", "\n\n", t), encoding="utf-8")
supp_path.write_text(re.sub(r"\n{3,}", "\n\n", s), encoding="utf-8")
print("edits:", done)
