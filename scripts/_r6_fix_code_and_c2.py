"""R6 (v8): fix the docx builder's code-block rendering and reorder Table C2's caption."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

# ---- 1. builder: one monospace paragraph per code line -------------------
js = D / "build_paper_docx.js"
t = js.read_text(encoding="utf-8")
old = """const flushCode = () => {
  const text = codeBuf.join("  ");
  children.push(
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 120, line: 276 },
      children: [monoRun(text, { size: SMALL_SIZE })],
    }),
  );
  codeBuf = [];
};"""
new = """const flushCode = () => {
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
if old not in t:
    raise SystemExit("flushCode block not found")
t = t.replace(old, new, 1)
js.write_text(t, encoding="utf-8")
print("builder patched")

# ---- 2. Table C2: caption immediately above its body ---------------------
for name, explain_marker, cap_marker in (
    ("paper_en.md",
     "Measured on the architecture-fixed replicas whose τ = 16 s arm reproduces the archived one in the mean (92.43 vs 92.44); re-running the archived arms reproduces every per-seed value bit-identically (max |Δ| = 0.0).",
     "**Table C2. Deployed-threshold completion and oracle reference, polar HSR (%) per seed, common episodes.**"),
    ("paper_zh.md",
     "测量于架构固定副本集，其 τ = 16 s 臂在均值上复现归档臂（92.43 对 92.44）；重跑归档臂逐种子逐位一致（max |Δ| = 0.0）。",
     "**表 C2. 部署阈值补齐与 oracle 参照，极区 HSR（%）逐种子，共同回合。**"),
):
    p = D / name
    s = p.read_text(encoding="utf-8")
    cap_block = cap_marker + "\n\n" + explain_marker
    if cap_block in s:
        s = s.replace(cap_block, explain_marker + "\n\n" + cap_marker, 1)
        p.write_text(s, encoding="utf-8")
        print("reordered C2 caption in", name)
    else:
        # tolerate the variant where a blank line separates them differently
        alt = cap_marker + "\n\n" + explain_marker
        print("C2 block variant not found in", name, "| contains caption:", cap_marker in s)
