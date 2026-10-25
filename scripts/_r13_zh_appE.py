"""R14 part 4: make the Chinese Appendix E use the real prompt and the real three-call outputs."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"

# pull the real system prompt from the experiment script
src = (ROOT / "experiments" / "run_llm_proposals.py").read_text(encoding="utf-8")
m = re.search(r'SYSTEM_P1 = \(\s*(.*?)\n\)', src, re.S)
prompt = ""
if m:
    parts = re.findall(r'"([^"]*)"', m.group(1))
    prompt = "".join(parts)
print("prompt chars:", len(prompt))
print(prompt[:200])

NEW = (
    "## 附录 E. Prompt、schema 与原始输出\n\n"
    "**系统提示（原文，未改写）。**\n\n```\n" + prompt + "\n```\n\n"
    "`{narratives}` 由训练窗口的二十段失败叙述替换；`{intent}` 由算子意图替换。P1 变体要求只给谓词，"
    "P2 变体（同一系统提示，尾句改为要求同时给出幅值与理由）要求谓词 + 幅值。\n\n"
    "**原始输出，前三次调用（逐字 JSON）。**\n\n"
    "```\n"
    'call 1  P1  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":60},\n'
    '             {"field":"handover_advance_s","cmp":"lt","value":10}],"magnitude":10}\n'
    "        P2  {\"effect\":\"min_advance\",\"atoms\":[{\"field\":\"handover_advance_s\",\"cmp\":\"lt\",\"value\":12},\n"
    '             {"field":"latitude_abs_deg","cmp":"ge","value":60}],"magnitude":12,\n'
    '             "magnitude_justification":"Observed acquisitions took 8.0-9.8 s while a 6 s advance\n'
    '             failed, so 12 s provides margin above the worst-case acquisition time."}\n\n'
    'call 2  P1  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":64},\n'
    '             {"field":"handover_advance_s","cmp":"lt","value":10}],"magnitude":10}\n'
    '        P2  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":60}],\n'
    '             "magnitude":12,"magnitude_justification":"Polar failures show acquisition latencies\n'
    '             up to 9.9 s against a 6 s advance, so enforcing a 12 s lead provides margin."}\n\n'
    'call 3  P1  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":64},\n'
    '             {"field":"handover_advance_s","cmp":"le","value":6}],"magnitude":10}\n'
    '        P2  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":60}],\n'
    '             "magnitude":10,"magnitude_justification":"High-latitude handovers in the failure set\n'
    '             had acquisition times up to 8.9 s, so a 10 s minimum lead prevents the observed 6 s\n'
    '             advance from being exhausted before acquisition completes."}\n'
    "```\n\n"
    "**读法。** 谓词在三次调用间稳定（同一纬度字段、同一极区带）；幅值不稳定（10、12、10 s，而需求是 16 s），"
    "并且 P1 与 P2 的幅值并不一致；JSON 语法全部合法（20/20）。这正是正文所述「谓词可提、幅值不可信」的单例证据，"
    "二十条的统计见第六节 L。\n\n"
    "**Schema。** 允许字段与比较算子均以词形写出（`lt/le/gt/ge/eq/ne`），以保证跨 PDF 管线可复制；"
    "二十条提案的原始 JSON 与两种变体封存在 `results/routeA_r3/llm_proposals/proposals.csv`。\n\n"
)

z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
i = t.find("## 附录 E")
if i < 0:
    raise SystemExit("ZH appendix E not found")
j = t.find("## 参考文献", i)
t = t[:i] + NEW + t[j:]
z.write_text(t, encoding="utf-8")
print("ZH appendix E rebuilt with the real prompt and outputs")
