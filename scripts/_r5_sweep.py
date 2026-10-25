"""Final sweep: every remaining 94.0 / 88.6 style stale value in both files."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
for name in ("paper_en.md", "paper_zh.md"):
    t = (D / name).read_text(encoding="utf-8")
    print("=" * 20, name)
    for k in ("94.0%", "88.6", "93.4%", "93.9%", "5.0 pp", "0.7%"):
        for m in re.finditer(re.escape(k), t):
            print(f"  [{k}] {t[max(0, m.start()-90):m.start()+60]!r}")
