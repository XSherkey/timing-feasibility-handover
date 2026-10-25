"""Move the probe-cost table from Section V-C to Section VI-G so the table numbers
appear in reading order (I, II, ..., VI)."""
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

EN_BLOCK = """**Table VI. Probe cost per calibration.**
| configuration | episodes | env steps | share of a 9600-episode training run |
|---|---|---|---|
| probe, 2 episodes/advance | 22 | 5,280 | 0.23% |
| probe, 8 episodes/advance | 88 | 21,120 | 0.92% |
"""

ZH_BLOCK = """**表 VI. 每次标定的探测成本。**
| 配置 | episode 数 | 环境步数 | 占 9600 episode 训练的比例 |
|---|---|---|---|
| 每提前量 2 episode | 22 | 5,280 | 0.23% |
| 每提前量 8 episode | 88 | 21,120 | 0.92% |
"""

EN_ANCHOR = "**Probing accuracy.** The threshold is identifiable to about $\\pm2$"
EN_ANCHOR_PLAIN = "**Probing accuracy.** The threshold is identifiable to about +/-2 s at the plateau,"
ZH_ANCHOR = "**探测精度。** 阈值在平台处只能辨识到约 ±2 s"


def move(path: Path, block: str, anchor: str, after_para_marker: str) -> bool:
    t = path.read_text(encoding="utf-8")
    if block not in t:
        print("block not found in", path.name)
        return False
    t = t.replace(block, "", 1)
    idx = t.find(anchor)
    if idx < 0:
        print("anchor not found in", path.name)
        return False
    end = t.find(after_para_marker, idx)
    if end < 0:
        print("end marker not found in", path.name)
        return False
    insert_at = end
    t = t[:insert_at] + "\n\n" + block.strip() + "\n" + t[insert_at:]
    path.write_text(t, encoding="utf-8")
    print("moved in", path.name)
    return True


move(D / "main.md", EN_BLOCK, EN_ANCHOR_PLAIN, "\n\n**The constant.**")
move(D / "main_zh.md", ZH_BLOCK, ZH_ANCHOR, "\n\n**常数。**")
