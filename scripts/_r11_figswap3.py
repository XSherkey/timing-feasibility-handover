"""R12 part 10: put the dose caption in position 6 and the gate caption in position 7 (EN + ZH)."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"


def exchange(name: str, first_marker: str, second_marker: str) -> None:
    p = D / name
    t = p.read_text(encoding="utf-8")
    i = t.find(first_marker)
    j = t.find(second_marker)
    if i < 0 or j < 0:
        raise SystemExit(f"{name}: markers missing")
    if i > j:
        i, j = j, i
        first_marker, second_marker = second_marker, first_marker
    end_i = t.find("\n\n", i)
    end_j = t.find("\n\n", j)
    block1 = t[i:end_i]          # gate (labelled 7)
    block2 = t[j:end_j]          # dose (labelled 6)
    new = block2 + "\n\n" + block1
    t = t[:i] + new + t[end_j:]
    p.write_text(t, encoding="utf-8")
    print(name, "exchanged")


exchange("paper_en.md", "**Fig. 7.** The audit gate", "**Fig. 6.** Reward injection")
exchange("paper_zh.md", "**图 7.** 审计门的因果测量", "**图 6.** 奖励注入是剂量-反应")
