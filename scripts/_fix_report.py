"""One-off fixer for the nested-quote f-string in make_report.py."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "scripts" / "make_report.py"
s = p.read_text(encoding="utf-8")
old = """        for cls, s in stress["summary"].items():
            put(f"audit.{cls}",
                f"semantic {s['semantic_detect'] * 100:.0f}%, physics {s['physics_detect'] * 100:.0f}%, "
                f"accept {('-' if s['false_acceptance'] is None else f'{s['false_acceptance'] * 100:.0f}%')}, "
                f"reject {('-' if s['false_rejection'] is None else f'{s['false_rejection'] * 100:.0f}%')}",
                "auditor_stress")"""
new = '''        for cls, sc in stress["summary"].items():
            acc = sc["false_acceptance"]
            rej = sc["false_rejection"]
            acc_s = "-" if acc is None else f"{acc * 100:.0f}%"
            rej_s = "-" if rej is None else f"{rej * 100:.0f}%"
            put(f"audit.{cls}",
                f"semantic {sc['semantic_detect'] * 100:.0f}%, physics {sc['physics_detect'] * 100:.0f}%, "
                f"accept {acc_s}, reject {rej_s}",
                "auditor_stress")'''
assert old in s, "stress block not found"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("patched")
