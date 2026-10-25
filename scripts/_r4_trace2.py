import os
import subprocess
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
js = D / "build_paper_docx.js"
print("instrumented already:", "DSH_DOCX_DEBUG" in js.read_text(encoding="utf-8"))
node = r"D:\Program Files\Deepseek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe"
env = dict(os.environ, DSH_DOCX_DEBUG="1")
r = subprocess.run([node, "build_paper_docx.js", "paper_en.md", "_dbg3.docx", "en"], cwd=D,
                   capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
lines = [l for l in (r.stderr or "").splitlines() if l.startswith("[tbl@")]
print("hits:", len(lines))
for l in lines:
    print("  ", l)
print("stdout tail:", (r.stdout or "").strip()[-200:])
