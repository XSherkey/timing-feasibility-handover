import re
from pathlib import Path

D = Path(r"../From Human Intent to In-Orbit Action/IEEE_Trans_新版本")
t = (D / "paper_en.md").read_text(encoding="utf-8")

def show(label, pat, before=120, after=320, limit=2):
    print(f"\n=== {label} ===")
    for m in list(re.finditer(pat, t))[:limit]:
        print(repr(t[max(0, m.start() - before):m.start() + after]))

show("abstract drift sentence", r"re-probed threshold holds 93\.2%")
show("A8 in contributions", r"probe-calibrated constant")
show("V-E gate split sentence", r"disjoint evaluation-window split")
show("V-E no-evaluation sentence", r"neither the evaluation window")
show("VI-A table list", r"Tables III")
show("VI-A stat section ref", r"Section VI-J")
show("limitations", r"Three limits")
show("Tz formula numbering", r"\(5\)", before=60, after=60, limit=3)
show("fig 9 caption", r"\*\*Fig\. 9\.\*\*")
show("duplicate acquisition paragraph", r"\*\*Acquisition requirement\.\*\*", limit=3)
