from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "build_paper_docx.js"
s = p.read_text(encoding="utf-8")
old = ': "Censoring-Aware Mining and Conservative Injection of Handover Constraints";'
new = ': "Timing-Feasibility Constraints for LEO Handover: Attribution, Calibration and Audit";'
print("header found:", s.count(old))
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("header updated")
