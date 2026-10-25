"""Replace the bare 'tau*' token with the asterisk operator so the docx builder's
inline-emphasis regex cannot mistake it for an italic delimiter (it left a stray '*'
in the rendered text)."""
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
for name in ("paper_en.md", "paper_zh.md"):
    p = D / name
    t = p.read_text(encoding="utf-8")
    n = t.count("τ*")
    t = t.replace("τ*", "τ\u2217")
    p.write_text(t, encoding="utf-8")
    print(name, "replaced", n)
