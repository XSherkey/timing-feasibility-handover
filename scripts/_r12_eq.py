"""R13: render displayed equations as centred equations with right-aligned numbers, not monospace code."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
b = D / "build_paper_docx.js"
s = b.read_text(encoding="utf-8")

if "eqBlock" in s:
    raise SystemExit("already patched")

OLD = """const flushCode = () => {
  // one paragraph per line: joining them produced a centred wall of text that was
  // unreadable (and reviewers read it as corrupted content)
  for (const line of codeBuf) {
    children.push(
      new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { before: 0, after: 0, line: 240 },
        indent: { left: 240 },
        children: [monoRun(line, { size: SMALL_SIZE })],
      }),
    );
  }
  codeBuf = [];
};"""

NEW = """const flushCode = () => {
  // A fenced block whose last line ends in "(n)" and whose body contains an "=" is a
  // displayed equation: render it centred with the number flush right (IEEE style),
  // in the body font. Everything else stays monospace (commands, JSON, prompts).
  const text = codeBuf.join(" ").replace(/\\s+/g, " ").trim();
  const m = text.match(/^(.*?)\\s*\\((\\d+)\\)\\s*$/);
  if (codeBuf.length && m && text.includes("=")) {
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
    codeBuf = [];
    return;
  }
  for (const line of codeBuf) {
    children.push(
      new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { before: 0, after: 0, line: 240 },
        indent: { left: 240 },
        children: [monoRun(line, { size: SMALL_SIZE })],
      }),
    );
  }
  codeBuf = [];
};"""

if OLD not in s:
    raise SystemExit("flushCode block not found")
s = s.replace(OLD, NEW, 1)

# make sure the tab-stop enum is imported
if "TabStopType" not in s.split("const flushCode")[0]:
    s = s.replace("const {", "const { TabStopType,", 1)
b.write_text(s, encoding="utf-8")
print("equation rendering patched; TabStopType imported:", "TabStopType," in s)
