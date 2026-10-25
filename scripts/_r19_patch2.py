"""R19 part 2: tag tables/captions and split the body into IEEE sections."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

# ---- 1. tag the table with its width class -------------------------------
old = """  return new Table({
    width: { size: finalWidths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: finalWidths,
    alignment: AlignmentType.CENTER,
    rows: tableRows,
  });"""
new = """  const tbl = new Table({
    width: { size: finalWidths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: finalWidths,
    alignment: AlignmentType.CENTER,
    rows: tableRows,
  });
  tbl._wide = wide;
  return tbl;"""
if old not in s:
    raise SystemExit("table return block not found")
s = s.replace(old, new, 1)

# ---- 2. tag caption paragraphs so a wide table can take its caption ------
old = "const captionPara = (text) => {"
if old not in s:
    raise SystemExit("captionPara not found")
s = s.replace(old, "const captionPara = (text) => {\n  // tagged below so the IEEE section splitter can move a caption with its table", 1)

# find the return of captionPara and tag it
import re
m = re.search(r"(const captionPara = \(text\) => \{[\s\S]*?)\n\};", s)
if not m:
    raise SystemExit("captionPara body not found")
body = m.group(1)
if "return para(" in body or "return new Paragraph(" in body:
    print("captionPara returns a paragraph builder; tagging will be done at call sites")

# ---- 3. remember where the first Heading-1 starts ------------------------
old = "let paraBuf = [];"
new = "let paraBuf = [];\nlet firstH1 = -1;"
s = s.replace(old, new, 1)

old = """  if (/^##\\s+/.test(line)) {
    flushPara();
    children.push("""
new = """  if (/^##\\s+/.test(line)) {
    flushPara();
    if (firstH1 < 0) firstH1 = children.length;
    children.push("""
if old not in s:
    raise SystemExit("H1 branch not found")
s = s.replace(old, new, 1)

# ---- 4. IEEE sections ----------------------------------------------------
old = """  sections: [
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 },
        },
      },"""
new = """  sections: ieeeSections(),"""
if old not in s:
    raise SystemExit("section block not found")
# capture the full old section object to replace (it also holds headers/footers/children)
i = s.find(old)
j = s.find("  ],\n});", i)
if j < 0:
    raise SystemExit("section block end not found")
old_block = s[i:j + len("  ],\n")]
NEW_BLOCK = '''  sections: ieeeSections(),
'''
s = s[:i] + NEW_BLOCK + s[j + len("  ],\n"):]

# ---- 5. the ieeeSections() function, defined before the Document ----------
helper = '''
// ---- IEEE Transactions layout: one-column front matter, two-column body,
// ---- wide tables lifted into their own one-column section ----------------
const PAGE = IEEE
  ? { width: 12240, height: 15840, margin: { top: 1008, bottom: 1008, left: 936, right: 936 } }
  : { width: 11906, height: 16838, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } };

const headerFooter = {
  headers: {
    default: new Header({
      children: [
        para(run(headerText, { size: 16, color: "546E7A" }), {
          alignment: AlignmentType.CENTER,
          spacing: { after: 0, line: 220 },
        }),
      ],
    }),
  },
  footers: {
    default: new Footer({
      children: [
        para(new TextRun({ children: [PageNumber.CURRENT], font, size: 18 }), {
          alignment: AlignmentType.CENTER,
        }),
      ],
    }),
  },
};

const section = (kids, cols) => ({
  properties: {
    page: { size: { width: PAGE.width, height: PAGE.height }, margin: PAGE.margin },
    ...(cols > 1 ? { column: { count: cols, space: 360 } } : {}),
  },
  ...headerFooter,
  children: kids,
});

const ieeeSections = () => {
  if (!IEEE) return [section(children, 1)];
  const cut = firstH1 > 0 ? firstH1 : children.length;
  const front = children.slice(0, cut);
  const body = children.slice(cut);
  const out = [section(front, 1)];
  let buf = [];
  for (let i = 0; i < body.length; i++) {
    const c = body[i];
    const wide = c && c._wide;
    if (wide) {
      // a caption paragraph immediately before the table travels with it
      let cap = null;
      if (buf.length && buf[buf.length - 1] && buf[buf.length - 1]._caption) {
        cap = buf.pop();
      }
      if (buf.length) { out.push(section(buf, 2)); buf = []; }
      out.push(section(cap ? [cap, c] : [c], 1));
    } else {
      buf.push(c);
    }
  }
  if (buf.length) out.push(section(buf, 2));
  return out;
};
'''
anchor = "const doc = new Document({"
s = s.replace(anchor, helper + "\n" + anchor, 1)

p.write_text(s, encoding="utf-8")
print("sections wired")
