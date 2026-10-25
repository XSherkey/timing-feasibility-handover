"""Instrument the builder robustly and trace every table the parser sees."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
js = D / "build_paper_docx.js"
t = js.read_text(encoding="utf-8")
old = '  if (line.trim().startsWith("|")) {\n    const tbl = [];'
new = ('  if (line.trim().startsWith("|")) {\n'
       '    if (process.env.DSH_DOCX_DEBUG) console.error("[tbl@line " + i + "] " + line.trim().slice(0, 50));\n'
       '    const tbl = [];')
assert t.count(old) == 1, t.count(old)
t = t.replace(old, new, 1)
js.write_text(t, encoding="utf-8")
assert "DSH_DOCX_DEBUG" in js.read_text(encoding="utf-8"), "write did not persist"
print("instrumented OK")

node = r"D:\Program Files\Deepseek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe"
env = dict(os.environ, DSH_DOCX_DEBUG="1")
r = subprocess.run([node, "build_paper_docx.js", "paper_en.md", "_dbg2.docx", "en"], cwd=D,
                   capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
lines = [l for l in (r.stderr or "").splitlines() if l.startswith("[tbl@")]
print("table-branch hits:", len(lines))
for l in lines:
    print("  ", l)
