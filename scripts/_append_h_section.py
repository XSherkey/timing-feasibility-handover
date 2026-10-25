from pathlib import Path

p = Path(r"results/routeA/SUMMARY.md")
base = p.read_text(encoding="utf-8")
add = Path(r"results/routeA/_phase_h_section.md").read_text(encoding="utf-8")
if "Phase H（第三阶段" not in base:
    p.write_text(base.rstrip() + "\n" + add, encoding="utf-8")
    print("appended, len", len(base) + len(add))
else:
    print("already present")
