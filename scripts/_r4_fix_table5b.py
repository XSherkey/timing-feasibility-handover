"""Repair the Table V placement and sort the caption list by figure number."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

TABLE_EN = """**Table V. Cross-intent transfer (polar HSR at |lat| ≥ 70°, mean over 10 policy seeds; 9 of them committed a rule at intent 0, and the table reports all seeds, so seeds without a committed rule contribute identically to both arms).**

| knowledge graph | intent 0 reliability | intent 1 latency | intent 2 power | intent 3 balanced | n |
|---|---|---|---|---|---|
| shared (inherited) | 90.37 | **90.21** | **89.99** | **90.75** | 10 |
| fresh per intent | 90.34 | 72.19 | 68.22 | 69.85 | 10 |
| transfer gain (pp) | +0.03 | +18.02 | +21.77 | +20.91 | |
"""
TABLE_ZH = """**表 V. 跨意图转移（极区 HSR，|lat| ≥ 70°，10 个策略种子取均值；其中 9 个在意图 0 提交了规则，表内包含全部种子，未提交的种子在两臂中贡献相同）。**

| 知识图谱 | 意图 0 可靠性 | 意图 1 时延 | 意图 2 功耗 | 意图 3 平衡 | n |
|---|---|---|---|---|---|
| 共享（继承） | 90.37 | **90.21** | **89.99** | **90.75** | 10 |
| 每意图新建 | 90.34 | 72.19 | 68.22 | 69.85 | 10 |
| 转移增益（pp） | +0.03 | +18.02 | +21.77 | +20.91 | |
"""

for name, table, anchor, cap_head, figre in (
    ("paper_en.md", TABLE_EN,
     "identically to both arms, so they dilute the contrast rather than bias it.",
     "## Figure Captions", re.compile(r"^\*\*Fig\.\s*(\d+)\.\*\*")),
    ("paper_zh.md", TABLE_ZH,
     "因此它稀释对比而不是使其有偏。",
     "## 图注", re.compile(r"^\*\*图\s*(\d+)\.\*\*")),
):
    p = D / name
    t = p.read_text(encoding="utf-8")
    i = t.find(cap_head)
    if i < 0:
        raise SystemExit(f"{name}: captions heading missing")
    body, caps = t[:i], t[i:]

    # 1. drop stray table rows from the captions section
    kept = [ln for ln in caps.split("\n") if not ln.strip().startswith("|")]
    caps = "\n".join(kept)
    caps = re.sub(r"\n{3,}", "\n\n", caps)

    # 2. sort the caption paragraphs by figure number
    head, rest = caps.split("\n", 1)
    blocks = [b.strip() for b in rest.split("\n\n") if b.strip()]
    numbered, others = [], []
    for b in blocks:
        m = figre.match(b)
        (numbered.append((int(m.group(1)), b)) if m else others.append(b))
    numbered.sort()
    caps = head + "\n\n" + "\n\n".join([b for _, b in numbered] + others) + "\n"

    # 3. put the Table V block back into Section VI-F
    if anchor not in body:
        raise SystemExit(f"{name}: VI-F anchor missing")
    if "| shared (inherited) |" in body or "| 共享（继承） |" in body:
        raise SystemExit(f"{name}: Table V already in the body")
    body = body.replace(anchor, anchor + "\n\n" + table, 1)

    p.write_text(body + caps, encoding="utf-8")
    print(name, "| captions sorted:", [n for n, _ in numbered])
