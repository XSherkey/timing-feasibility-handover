"""R23: equations must not use single-column tab stops — in IEEE mode emit one line per source line, centred."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

old = """    if (m && /\\(\\d+\\)\\s*$/.test(line)) {
      children.push(
        new Paragraph({
          spacing: { before: 80, after: 80, line: 260 },
          tabStops: [
            { type: TabStopType.CENTER, position: 4500 },
            { type: TabStopType.RIGHT, position: 9000 },
          ],
          children: [
            new TextRun({ text: "\\t" + m[1].trim(), size: BODY_SIZE, font }),
            new TextRun({ text: "\\t(" + m[2] + ")", size: BODY_SIZE, font }),
          ],
        }),
      );
      buf = [];
    }"""
new = """    if (m && /\\(\\d+\\)\\s*$/.test(line)) {
      if (IEEE) {
        // Two-column layout: a 4500/9000 tab pair runs off the column and the renderer
        // clips the formula. Emit every source line of the equation separately, centred,
        // with the number appended after an em space.
        for (const seg of buf) {
          const flat = seg.replace(/\\s+/g, " ").trim();
          if (!flat) continue;
          const mm = flat.match(/^(.*?)\\s*\\((\\d+)\\)\\s*$/);
          const body = mm ? mm[1].trim() : flat;
          const num = mm ? mm[2] : null;
          children.push(
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { before: 30, after: 30, line: 220 },
              children: [
                new TextRun({ text: num ? body + "\\u2003(" + num + ")" : body, size: 16, font }),
              ],
            }),
          );
        }
      } else {
        children.push(
          new Paragraph({
            spacing: { before: 80, after: 80, line: 260 },
            tabStops: [
              { type: TabStopType.CENTER, position: 4500 },
              { type: TabStopType.RIGHT, position: 9000 },
            ],
            children: [
              new TextRun({ text: "\\t" + m[1].trim(), size: BODY_SIZE, font }),
              new TextRun({ text: "\\t(" + m[2] + ")", size: BODY_SIZE, font }),
            ],
          }),
        );
      }
      buf = [];
    }"""
if old not in s:
    raise SystemExit("equation block not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("IEEE equation branch added")
