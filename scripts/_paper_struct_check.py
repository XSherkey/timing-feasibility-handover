import re
from pathlib import Path

d = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
md = (d / "main.md").read_text(encoding="utf-8")
tex = (d / "main.tex").read_text(encoding="utf-8")

m = re.search(r"## Abstract\n(.*?)\n---", md, re.S)
print("md abstract words:", len(m.group(1).split()) if m else "n/a")
m2 = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
print("tex abstract words:", len(m2.group(1).split()) if m2 else "n/a")

labels = ["pipeline", "gap", "policy", "lambda", "drift", "forms", "gate"]
for i, lab in enumerate(labels, 1):
    print("fig%d (%s) referenced:" % (i, lab), ("fig:" + lab) in tex)

for env in ("figure", "table", "tabular", "equation", "aligned", "enumerate",
            "thebibliography", "IEEEkeywords"):
    b = len(re.findall(r"\\begin\{" + env + r"\}", tex))
    e = len(re.findall(r"\\end\{" + env + r"\}", tex))
    if b or e:
        print("%s: begin %d end %d %s" % (env, b, e, "OK" if b == e else "MISMATCH"))
print("md words:", len(md.split()))
