import re
from pathlib import Path

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
t = (D / "paper_en.md").read_text(encoding="utf-8")
s = (D / "supplementary/supp_en.md").read_text(encoding="utf-8")

print("=== main bank paragraph ===")
i = t.find("The bank is 26 candidates")
print(t[i:i+800] if i > 0 else "not found")

print("\n=== main neutral / harmful mentions ===")
for pat in ("four caps", "five caps", "unscoped", "|Δ| ≤ 1.0"):
    print(f"  {pat!r}: {t.count(pat)}")

print("\n=== VI-A protocol label sentence ===")
i = t.find("Tables III, VI, IX, IXb and IXc")
print(t[max(0, i-300):i+260] if i > 0 else "not found")

print("\n=== stats sentence ===")
for pat in ("Every comparison in this paper is paired on the policy seed", "paired on the policy seed"):
    print(f"  {pat!r}: {t.count(pat)}")
    for m in list(re.finditer(re.escape(pat), t))[:2]:
        print("     ", repr(t[max(0, m.start()-140):m.start()+160]))

print("\n=== equation refs in Section IV ===")
sec = t[t.find("## IV."):t.find("## V.")]
for m in re.finditer(r"\((\d)\)", sec):
    ctx = sec[max(0, m.start()-90):m.start()+8].replace("\n", " ")
    print(f"   ({m.group(1)})  ...{ctx}")

print("\n=== feeder statements ===")
for pat in ("feeder capacity reduced to three slots", "three in the nominal configuration", "1 slot", "feeder_slots"):
    print(f"  {pat!r}: main {t.count(pat)}, supp {s.count(pat)}")

print("\n=== supplement H2 body ===")
i = s.find("**Table H2.")
print(s[i:i+300] if i > 0 else "H2 missing")
print("  has rows:", "| extra acquisition latency" in s)
print("\n=== supplement D2 header ===")
i = s.find("**Table D2.")
print(s[i:i+300] if i > 0 else "D2 missing")
