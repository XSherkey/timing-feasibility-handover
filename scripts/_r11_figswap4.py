"""R12 part 11: ladder is cited before the gate, so ladder is Fig. 7 and the gate is Fig. 8."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"


def exchange(name: str, a: str, b: str) -> None:
    p = D / name
    t = p.read_text(encoding="utf-8")
    i, j = t.find(a), t.find(b)
    if i < 0 or j < 0:
        raise SystemExit(f"{name}: markers missing ({i}, {j})")
    if i > j:
        i, j = j, i
        a, b = b, a
    end_i = t.find("\n\n", i)
    end_j = t.find("\n\n", j)
    block_a = t[i:end_i]
    block_b = t[j:end_j]
    t = t[:i] + block_b + "\n\n" + block_a + t[end_j:]
    p.write_text(t, encoding="utf-8")
    print(name, "exchanged", a[:12], "<->", b[:12])


exchange("paper_en.md", "**Fig. 7.** The audit gate", "**Fig. 8.** Six references")
exchange("paper_zh.md", "**图 7.** 审计门的因果测量", "**图 8.** 六个参照系")

# swap the image mapping 7 <-> 8
b = D / "build_paper_docx.js"
s = b.read_text(encoding="utf-8")
import re
m7 = re.search(r'7: "(fig[^"]+)"', s)
m8 = re.search(r'8: "(fig[^"]+)"', s)
if m7 and m8:
    s = s.replace(m7.group(0), '7: "@@LADDER@@"').replace(m8.group(0), f'8: "{m7.group(1)}"').replace('7: "@@LADDER@@"', f'7: "{m8.group(1)}"')
    b.write_text(s, encoding="utf-8")
    print("FIG_FILES 7/8 swapped:", m8.group(1), "-> 7 ;", m7.group(1), "-> 8")
