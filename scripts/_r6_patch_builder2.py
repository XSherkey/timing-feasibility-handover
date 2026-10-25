"""Patch step 2: wire the paragraph buffer into the main loop of build_paper_docx.js."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")

# ---- the flushParagraph helper (placed after flushCode) -------------------
marker = "  codeBuf = [];\n};"
if marker not in s:
    raise SystemExit("flushCode end not found")
helper = '''  codeBuf = [];
};

// flush one accumulated body paragraph, then place any figures it references
const flushPara = () => {
  if (!paraBuf.length) return;
  const text = paraBuf.join(" ").replace(/\\s+/g, " ").trim();
  paraBuf = [];
  if (!text) return;
  children.push(bodyPara(text));
  let m;
  const re = new RegExp(figRefRe.source, "g");
  const toInsert = [];
  while ((m = re.exec(text)) !== null) {
    const num = Number(m[1]);
    if (!figCaptionText[num] || insertedFigs.has(num) || toInsert.includes(num)) continue;
    toInsert.push(num);
  }
  for (const num of toInsert.sort((a, b) => a - b)) {
    if (!insertedFigs.has(num)) {
      for (const b of figureBlock(num)) children.push(b);
      insertedFigs.add(num);
      const k = pendingQueue.indexOf(num);
      if (k >= 0) pendingQueue.splice(k, 1);
    }
  }
};'''
s = s.replace(marker, helper, 1)

# ---- structural elements must flush the buffer first ---------------------
s = s.replace('  if (line.trim().startsWith("```")) {\n    if (inCode) flushCode();',
              '  if (line.trim().startsWith("```")) {\n    flushPara();\n    if (inCode) flushCode();', 1)
s = s.replace('  // table block\n  if (line.trim().startsWith("|")) {',
              '  // table block\n  if (line.trim().startsWith("|")) {\n    flushPara();', 1)
s = s.replace('  if (/^#\\s+/.test(line)) {\n    // title',
              '  if (/^#\\s+/.test(line)) {\n    flushPara();\n    // title', 1)

# ---- the regular-paragraph branch now buffers instead of emitting --------
old_body = '''  // regular paragraph
  const p = bodyPara(bodyLine);
  children.push(p);
'''
new_body = '''  // regular paragraph: accumulate until a structural line or blank line
  if (!isStructural(line) && !/^\\*\\*(Fig\\.|图|Table|表)/.test(trimmed)) {
    paraBuf.push(trimmed);
    i++;
    continue;
  }
  flushPara();
  const p0 = bodyPara(bodyLine);
  children.push(p0);
'''
if old_body not in s:
    raise SystemExit("body branch not found")
s = s.replace(old_body, new_body, 1)

# ---- drop the now-duplicated figure placement block for the fallback -----
start = s.find("  // figure insertion: only when referenced in THIS paragraph")
end = s.find("  i++;\n}", start)
if start < 0 or end < 0:
    raise SystemExit("figure block not found")
s = s[:start] + s[end:]

# ---- flush before the loop ends and before the safety pass ---------------
s = s.replace("// safety: place any figures never referenced in the body, in order",
              "flushPara();\n\n// safety: place any figures never referenced in the body, in order", 1)

p.write_text(s, encoding="utf-8")
print("builder patched")
