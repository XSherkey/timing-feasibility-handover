from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")
pairs = [
    ("A contribution-isolation experiment then asks which components are load-bearing, holding the shield, the probe and the margin fixed. Seven provenance variants—language model, hand-written predicates, latitude grid, random predicates, with and without the Kaplan–Meier stage and the audit gate—land within 0.11 pp of the full pipeline, and",
     "Holding the shield, the probe and the margin fixed, a contribution-isolation experiment then asks which components are load-bearing: seven provenance variants land within 0.11 pp of the full pipeline, and"),
    ("We therefore locate the contribution in the calibration-and-audit protocol rather than in the learner, and say so explicitly.",
     "The contribution is therefore the calibration-and-audit protocol, not the learner."),
    ("and the audit gate admits no harmful candidate and rejects no good one on a 26-candidate bank.",
     "and the audit gate admits no harmful candidate and rejects no good one in a 26-candidate bank."),
    ("The underlying principle is testable and does not depend on the field",
     "The underlying principle is a testable hypothesis across domains, not a domain-independent law"),
    ("What remains—and what this paper contributes—is the machinery around the constraint: mining its scope from narrative while refusing narrative magnitudes",
     "What remains—and what this paper contributes—is the machinery around the constraint: deriving its scope (by hand, by grid, or from a language model, all three equivalent in our isolation test) while refusing narrative magnitudes"),
]
for old, new in pairs:
    if t.count(old) != 1:
        print("MISS:", old[:60])
        continue
    t = t.replace(old, new, 1)
    print("ok:", old[:40])
p.write_text(t, encoding="utf-8")
a = t.find("## Abstract")
b = t.find("## Nomenclature")
print("abstract words:", len(t[a:b].split()))
