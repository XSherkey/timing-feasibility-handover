"""R13 part 2: group code-block lines into one equation per numbered terminator."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
b = D / "build_paper_docx.js"
s = b.read_text(encoding="utf-8")

start = s.find("const flushCode = () => {")
end = s.find("\n};", start) + 3
if start < 0 or end < 3:
    raise SystemExit("flushCode not found")

NEW = '''const flushCode = () => {
  // Group the block into segments: a segment ends at a line whose trailing token is
  // "(n)" and whose text contains "=" — that is one displayed equation. Segments that
  // are not equations stay monospace (commands, JSON, prompts).
  let buf = [];
  const emitMono = (lines) => {
    for (const line of lines) {
      children.push(
        new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { before: 0, after: 0, line: 240 },
          indent: { left: 240 },
          children: [monoRun(line, { size: SMALL_SIZE })],
        }),
      );
    }
  };
  for (const line of codeBuf) {
    buf.push(line);
    const m = buf.join(" ").replace(/\\s+/g, " ").trim().match(/^(.*?)\\s*\\((\\d+)\\)\\s*$/);
    if (m && m[1].includes("=") && /\\(\\d+\\)\\s*$/.test(line)) {
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
    }
  }
  if (buf.length) emitMono(buf);
  codeBuf = [];
};'''

s = s[:start] + NEW + s[end:]
b.write_text(s, encoding="utf-8")
print("flushCode rewritten")
