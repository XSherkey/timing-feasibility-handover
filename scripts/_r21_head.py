from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

# headings must not be justified: set alignment LEFT explicitly on both levels
a = """      para(run(line.slice(4).trim(), { bold: true, size: 22 }), {
        heading: HeadingLevel.HEADING_3,"""
b = """      para(run(line.slice(4).trim(), { bold: true, size: 22 }), {
        heading: HeadingLevel.HEADING_3,
        alignment: AlignmentType.LEFT,"""
print("h3:", s.count(a))
s = s.replace(a, b, 1)

c = """      para(run(line.slice(3).trim(), { bold: true, size: 26, color: "000000", smallCaps: true }), {
        heading: HeadingLevel.HEADING_2,"""
d = """      para(run(line.slice(3).trim(), { bold: true, size: 26, color: "000000", smallCaps: true }), {
        heading: HeadingLevel.HEADING_2,
        alignment: AlignmentType.LEFT,"""
print("h2:", s.count(c))
s = s.replace(c, d, 1)

p.write_text(s, encoding="utf-8")
print("done")
