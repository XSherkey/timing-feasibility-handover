"""R13 part 3: split equation blocks purely on numbered lines (the first equation may contain no '=')."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
b = D / "build_paper_docx.js"
s = b.read_text(encoding="utf-8")

old = '''  for (const line of codeBuf) {
    buf.push(line);
    const m = buf.join(" ").replace(/\\s+/g, " ").trim().match(/^(.*?)\\s*\\((\\d+)\\)\\s*$/);
    if (m && m[1].includes("=") && /\\(\\d+\\)\\s*$/.test(line)) {'''
new = '''  const isEqBlock = codeBuf.some((l) => /\\(\\d+\\)\\s*$/.test(l));
  if (!isEqBlock) {
    emitMono(codeBuf);
    codeBuf = [];
    return;
  }
  for (const line of codeBuf) {
    buf.push(line);
    const m = buf.join(" ").replace(/\\s+/g, " ").trim().match(/^(.*?)\\s*\\((\\d+)\\)\\s*$/);
    if (m && /\\(\\d+\\)\\s*$/.test(line)) {'''
if old not in s:
    raise SystemExit("grouping block not found")
s = s.replace(old, new, 1)
b.write_text(s, encoding="utf-8")
print("split condition relaxed")
