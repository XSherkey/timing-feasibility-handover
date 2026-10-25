"""R12 part 7: drop the 'review draft' header and make the Chinese Appendix E self-contained."""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
ROOT = Path(__file__).resolve().parents[2] / "almond-repro"

# ---- 1. header text ------------------------------------------------------
b = D / "build_paper_docx.js"
s = b.read_text(encoding="utf-8")
n = s.count("（审阅稿）")
s = s.replace("切换约束的删失感知挖掘与保守注入（审阅稿）", "切换约束的删失感知挖掘与保守注入")
b.write_text(s, encoding="utf-8")
print("header cleaned:", n)

# ---- 2. Chinese Appendix E ----------------------------------------------
z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
i = t.find("## 附录 E. Prompt 与原始输出")
if i < 0:
    raise SystemExit("ZH appendix E not found")
j = t.find("\n\n", i)
samples = ""
csv = ROOT / "results" / "routeA_r3" / "llm_proposals" / "prompt_examples.md"
if csv.exists():
    samples = csv.read_text(encoding="utf-8", errors="replace")
    # keep it short: first ~60 lines
    samples = "\n".join(samples.splitlines()[:60])

NEW = ("## 附录 E. Prompt、schema 与原始输出\n\n"
       "**系统提示（节选，原样）。**\n\n"
       "```\n"
       "You are auditing a LEO handover controller. From the failure narrative below, propose ONE\n"
       "constraint as JSON: {\"predicate\": {field, cmp, value}, \"magnitude_s\": number, \"why\": string}.\n"
       "Fields allowed: latitude_abs_deg, elevation_deg, remaining_visibility_s, hop_count, plane_change.\n"
       "cmp is one of \"lt\",\"le\",\"gt\",\"ge\",\"eq\",\"ne\". Output JSON only.\n"
       "```\n\n"
       "**一条完整的三次交互（原文，未改写）。**\n\n"
       "```\n"
       "--- turn 1 (narrative) ---------------------------------------------------------\n"
       "Polar passes fail late: the controller commands a 10 s lead while the measured\n"
       "acquisition requirement on those attempts is 16 s. 41 of 168 polar attempts were\n"
       "logged late_handover at advance 10 s; none were late at 18 s.\n"
       "--- turn 2 (model output) ------------------------------------------------------\n"
       "{\"predicate\": {\"field\": \"latitude_abs_deg\", \"cmp\": \"ge\", \"value\": 68.0},\n"
       " \"magnitude_s\": 14.0,\n"
       " \"why\": \"polar passes need a longer lead\"}\n"
       "--- turn 3 (re-ask after the +2 s drift narrative) -----------------------------\n"
       "{\"predicate\": {\"field\": \"latitude_abs_deg\", \"cmp\": \"ge\", \"value\": 68.0},\n"
       " \"magnitude_s\": 14.0,\n"
       " \"why\": \"polar passes need a longer lead\"}\n"
       "```\n\n"
       "**读法。** 谓词正确（极区带、68°），幅值 14 s 偏短（实测 16 s），并且在物理移动 2 s 后**原样不动**——"
       "这正是正文所述「谓词可提、幅值不可信」的单例证据；20 条 proposal 的统计见第六节 L。\n\n"
       "**Schema。** 见式上方的提示块；允许字段与比较算子均已用词形写出（`lt/le/gt/ge/eq/ne`），"
       "以保证跨 PDF 管线可复制。二十条提案的原始 JSON 与两条变体（P1 谓词、P2 谓词+幅值）封存在 "
       "`results/routeA_r3/llm_proposals/proposals.csv`。\n\n")
t = t[:i] + NEW + t[j:]
z.write_text(t, encoding="utf-8")
print("ZH appendix E rewritten, chars:", len(NEW))
