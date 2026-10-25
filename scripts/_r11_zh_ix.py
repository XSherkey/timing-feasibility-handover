"""R12 part 6: rebuild the Chinese isolation table from the JSON with CI/p/TOST columns."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
iso = json.loads((ROOT / "results" / "routeA_r3" / "isolation" / "summary.json").read_text(encoding="utf-8"))
rng = np.random.default_rng(5)


def tost_p(d, margin=1.0):
    d = np.asarray(d, float)
    n = d.size
    se = d.std(ddof=1) / np.sqrt(n) if n > 1 else 0.0
    if se == 0:
        return 0.0 if abs(d.mean()) < margin else 1.0
    return float(max(1 - stats.norm.cdf((d.mean() + margin) / se),
                     1 - stats.norm.cdf((margin - d.mean()) / se)))


a0 = np.array(iso["arms"]["A0_full"]["per_seed"]["eval"])
ARMS = [("A0_full", "A0", "完整流水线（LLM 谓词、KM、探测、门、共享图谱）", "`min_advance:18@latitude_abs_deg>=68`"),
        ("A1_human", "A1", "人工谓词（验证窗口上选定）", "`min_advance:18@latitude_abs_deg>=68,elevation_deg>=15`"),
        ("A2_grid", "A2", "纬度阈值由网格搜索选定", "`min_advance:18@latitude_abs_deg>=60`"),
        ("A3_randomBest", "A3", "被门准入的随机谓词", "`min_advance:22@remaining_visibility_s>=60`"),
        ("A4_noKM", "A4", "去掉 Kaplan–Meier 阶段的完整流水线", "`min_advance:18@latitude_abs_deg>=68`"),
        ("A5_noGate", "A5", "去掉审计门的完整流水线", "`min_advance:18@latitude_abs_deg>=68`"),
        ("A7_probeOnly", "A7", "仅探测 + 余量 + 盾", "`min_advance:18@latitude_abs_deg>=68,elevation_deg>=15`"),
        ("A8_constantProbe", "A8", "最高仰角控制器，提前量在验证窗口重选", "无约束规则：最高仰角 + 固定 18 s")]

rows = ["| 臂 | 组件来源 | 部署规则 | 测试窗口 HSR（%） | 相对 A0（pp） | lockbox +7 d（%） | Δ vs A0 [95% CI] | p（精确 Wilcoxon） | TOST p（margin 1.0 pp） |",
        "|---|---|---|---|---|---|---|---|---|"]
for key, lab, src, rule in ARMS:
    polar = np.array(iso["arms"][key]["per_seed"]["eval"])
    lb = iso["arms"][key]["per_seed"].get("lb299.25")
    lbm = np.mean(lb) if lb is not None else float("nan")
    if key == "A0_full":
        rows.append(f"| A0 | {src} | {rule} | 93.36 | -- | 91.67 | — | — | — |")
        continue
    d = polar - a0
    boot = np.array([rng.choice(d, size=d.size, replace=True).mean() for _ in range(10000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    pw = stats.wilcoxon(d, zero_method="wilcox").pvalue if np.any(d != 0) else 1.0
    tp = tost_p(d)
    rows.append(f"| {lab} | {src} | {rule} | {polar.mean():.2f} | {d.mean():+.2f} | {lbm:.2f} | "
                f"{d.mean():+.2f} [{lo:+.2f}, {hi:+.2f}] | {pw:.3f} | {'< 0.001' if tp < 0.001 else f'{tp:.3f}'} |")

TABLE = ("**表 IX. 贡献隔离（极区 HSR，|lat| ≥ 70°，n = 10 个策略种子，共同回合；所有选择在验证窗口完成）。"
         "协议：仅验证窗口。**\n\n" + "\n".join(rows) + "\n")

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
i = t.find("**表 IX.")
if i < 0:
    raise SystemExit("ZH Table IX not found")
j = t.find("\n\n", t.find("| A8", i))
t = t[:i] + TABLE + t[j:]
z.write_text(t, encoding="utf-8")
print("ZH Table IX rebuilt")
