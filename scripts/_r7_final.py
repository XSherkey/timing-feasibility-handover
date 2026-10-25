"""R8 part 10: ZH drift-table caption, EN appendix-A command block, and a final consistency sweep."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

# ---- ZH drift caption -----------------------------------------------------
z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
old_start = s.find("**表 V. 漂移响应")
if old_start < 0:
    raise SystemExit("ZH drift caption not found")
old_end = s.find("**", old_start + 6)
old_end = s.find("\n", old_end + 1) if s[old_end:old_end + 2] == "**" else old_end
# the caption paragraph is one line; take to end of line
line_end = s.find("\n", old_start)
cap = s[old_start:line_end]
print("old ZH caption:", cap[:160])
new_cap = ("**表 V. 漂移响应（极区 HSR，mean ± sd，traffic seed 0，极区取 |lat| ≥ 70°）。两个常数控制器行同样在 "
           "n = 10 个策略种子上评估，但不依赖策略，故 sd = 0.00；两个带盾行为 n = 10 个策略种子；最后一行为探测研究，"
           "使用五个策略种子并已注明。**")
s = s[:old_start] + new_cap + s[line_end:]
z.write_text(s, encoding="utf-8")
print("ZH drift caption fixed")

# ---- EN appendix A command block -----------------------------------------
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
i = t.find("python scripts/check_env.py")
j = t.find("```", i)
if i < 0 or j < 0:
    raise SystemExit("EN command block not found")
BLOCK = """python scripts/check_env.py
python scripts/run_campaign.py --methods almond --seeds 0-9 --episodes 9600 \\
    --eval-every 1200 --device cpu --spec-file results/nas/llm_spec.json \\
    --out results/campaign_1023
python scripts/eval_shield.py --run results/campaign_1023/almond_seed0 \\
    --rule "min_advance:16@latitude_abs_deg>=68"
python scripts/probe_feasibility.py --run results/campaign_1023/almond_seed0 \\
    --regime polar --episodes 8
python scripts/run_campaign.py --methods no_forensics --seeds 0-9 \\
    --late-risk-tau 16 --late-risk-weight 8.0 --out results/routeA_f3/lam8.0
python scripts/run_multi_intent.py --mode shared --seed 0
python experiments/run_drift_margin.py
python experiments/run_budget_curves.py
python scripts/km_setup_time.py --root results/campaign_1023
python scripts/probe_gate.py --run results/campaign_1023/almond_seed0
"""
t = t[:i] + BLOCK + t[j:]
p.write_text(t, encoding="utf-8")
print("EN command block rewritten")
