import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
for name in ("paper_en.md", "paper_zh.md"):
    t = (D / name).read_text(encoding="utf-8")
    refs = t.find("## References" if name.endswith("en.md") else "## 参考文献")
    caps = t.find("## Figure Captions" if name.endswith("en.md") else "## 图注")
    body = t[:refs]
    print("==", name, "| refs at", refs, "| captions at", caps)
    for n in range(1, 10):
        pat = re.compile(r"Fig(?:ure)?\.?\s*%d\b" % n) if name.endswith("en.md") else re.compile(r"图\s*%d\b" % n)
        hits = [m.start() for m in pat.finditer(body)]
        cap_hits = [m.start() for m in pat.finditer(t) if m.start() >= caps] if caps > 0 else []
        print("   Fig %d: body mentions %d %s | caption-section mentions %d"
              % (n, len(hits), ("(first at %d)" % hits[0]) if hits else "(NONE -> appended at end)", len(cap_hits)))
