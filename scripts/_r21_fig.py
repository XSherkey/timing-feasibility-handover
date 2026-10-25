from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

a = "const widthTwips = IEEE ? COL_WIDTH - 40 : 5800;"
b = "const widthTwips = IEEE ? COL_WIDTH - 400 : 5800;"
print("fig width found:", s.count(a))
s = s.replace(a, b, 1)

a2 = "spacing: { before: 160, after: 60 },"
b2 = "spacing: { before: 100, after: 40 },"
print("fig spacing found:", s.count(a2))
s = s.replace(a2, b2, 1)

p.write_text(s, encoding="utf-8")
print("patched ok")
