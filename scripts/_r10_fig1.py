from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = "The contribution we do claim is an *audit and calibration protocol*"
new = ("The pipeline that makes this measurable is Fig. 1: censored failure logs feed a Kaplan–Meier recovery, the "
       "language model proposes only the predicate, a probe measures the magnitude on the deployed policy, and the "
       "resulting constraint is injected at decision time behind an admission gate. The contribution we do claim is "
       "an *audit and calibration protocol*")
print("count", t.count(old))
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("EN Fig.1 mention added")
