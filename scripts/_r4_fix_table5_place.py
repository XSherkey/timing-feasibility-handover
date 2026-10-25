"""Move the Table V block out of the trailing captions section and into Section VI-F."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

TABLE = """**Table V. Cross-intent transfer (polar HSR at |lat| ≥ 70°, mean over 10 policy seeds; 9 of them committed a rule at intent 0, and the table reports all seeds, so seeds without a committed rule contribute identically to both arms).**

| knowledge graph | intent 0 reliability | intent 1 latency | intent 2 power | intent 3 balanced | n |
|---|---|---|---|---|---|
| shared (inherited) | 90.37 | **90.21** | **89.99** | **90.75** | 10 |
| fresh per intent | 90.34 | 72.19 | 68.22 | 69.85 | 10 |
| transfer gain (pp) | +0.03 | +18.02 | +21.77 | +20.91 | |
"""

for name, anchor_tail, header in (
    ("paper_en.md",
     "identically to both arms, so they dilute the contrast rather than bias it.",
     "## Figure Captions"),
    ("paper_zh.md",
     "因此它稀释对比而不是使其有偏。",
     "## 图注"),
):
    p = D / name
    t = p.read_text(encoding="utf-8")
    lines = t.split("\n")

    # 1. drop the stray table rows that sit inside the captions section
    cap = t.find(header)
    if cap < 0:
        raise SystemExit(f"{name}: captions heading not found")
    head_part, cap_part = t[:cap], t[cap:]
    stray = []
    for row in cap_part.split("\n"):
        if row.strip().startswith("|"):
            stray.append(row)
    for row in stray:
        cap_part = cap_part.replace(row + "\n", "", 1)
    cap_part = cap_part.replace("\n\n\n", "\n\n")
    t = head_part + cap_part

    # 2. insert the block at the end of the qualification paragraph in VI-F
    if TABLE.strip()[:20] in t:
        raise SystemExit(f"{name}: Table V block already in the body")
    if anchor_tail not in t:
        raise SystemExit(f"{name}: VI-F anchor not found")
    t = t.replace(anchor_tail, anchor_tail + "\n\n" + TABLE, 1)
    p.write_text(t, encoding="utf-8")
    print(name, "| stray rows removed:", len(stray), "| Table V inserted in VI-F")
