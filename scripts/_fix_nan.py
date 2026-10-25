from pathlib import Path
p = Path(r"D:\almond-repro\scripts\make_report.py")
s = p.read_text(encoding="utf-8")
old = '''        for th, v in sensitivity["theta_rho"].items():
            put(f"sens.theta.{th}",
                f"fires {v['fires']}, precision {v['precision'] * 100:.0f}%, recall {v['recall'] * 100:.0f}%",
                "sensitivity")
        for dm, v in sensitivity["delta_min"].items():
            put(f"sens.delta.{dm}",
                f"accepted {v['accepted']}/{v['n']}, precision {v['precision'] * 100:.0f}%, "
                f"recall {v['recall'] * 100:.0f}%", "sensitivity")'''
new = '''        def _pct(x):
            x = float(x)
            return "n/a" if not np.isfinite(x) else f"{x * 100:.0f}%"

        for th, v in sensitivity["theta_rho"].items():
            put(f"sens.theta.{th}",
                f"fires {v['fires']}, precision {_pct(v['precision'])}, recall {_pct(v['recall'])}",
                "sensitivity")
        for dm, v in sensitivity["delta_min"].items():
            put(f"sens.delta.{dm}",
                f"accepted {v['accepted']}/{v['n']}, precision {_pct(v['precision'])}, "
                f"recall {_pct(v['recall'])}", "sensitivity")'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("patched nan formatting")
