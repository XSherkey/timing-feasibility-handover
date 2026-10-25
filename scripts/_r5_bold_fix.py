"""Fix the orphaned bold marker on the 'Probe cost and limits' paragraph."""
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = "Probe cost and limits.** One calibration costs"
new = "**Probe cost and limits.** One calibration costs"
if t.count(old) != 1:
    raise SystemExit(f"found {t.count(old)}")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("fixed")
