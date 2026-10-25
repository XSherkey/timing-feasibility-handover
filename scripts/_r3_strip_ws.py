from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
for name in ("paper_en.md", "paper_zh.md"):
    p = D / name
    lines = p.read_text(encoding="utf-8").splitlines()
    fixed = 0
    for i, l in enumerate(lines):
        s = l.rstrip()
        if s != l:
            lines[i] = s
            fixed += 1
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(name, "stripped trailing whitespace on", fixed, "lines")
