from pathlib import Path
import re

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
t = (D / "paper_en.md").read_text(encoding="utf-8")
for k in ("already chose", "∘", "late_handover", "chose a"):
    print("==", k, t.count(k))
    for m in list(re.finditer(re.escape(k), t))[:6]:
        print("   ", repr(t[max(0, m.start() - 90):m.start() + 70]))
