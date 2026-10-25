"""Split the two caption lines whose closing '**' sat mid-line (it leaked into the docx)."""
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

en = D / "paper_en.md"
t = en.read_text(encoding="utf-8")
old = "**Table C1′. Deployed-threshold completion and oracle reference, polar HSR (%) per seed, common episodes.** Measured on"
new = "**Table C1′. Deployed-threshold completion and oracle reference, polar HSR (%) per seed, common episodes.**\n\nMeasured on"
print("EN:", t.count(old))
t = t.replace(old, new, 1)
en.write_text(t, encoding="utf-8")

zh = D / "paper_zh.md"
t = zh.read_text(encoding="utf-8")
old = "**表 C1′. 部署阈值补齐与 oracle 参照，极区 HSR（%）逐种子，共同回合。** 测量于"
new = "**表 C1′. 部署阈值补齐与 oracle 参照，极区 HSR（%）逐种子，共同回合。**\n\n测量于"
print("ZH:", t.count(old))
t = t.replace(old, new, 1)
zh.write_text(t, encoding="utf-8")
print("done")
