from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "run_factorial_consistent.py"
t = p.read_text(encoding="utf-8")
t = t.replace("            late.append(late_share(r))",
              "            lv = late_share(r)\n            late.append(0.0 if lv != lv else lv)")
old_print = (
    '        print(f"{arm:8s} polar {summarise(polar)[\'mean\']:6.2f} +- {summarise(polar)[\'sd\']:4.2f} | "\n'
    '              f"late {summarise(late)[\'mean\']:5.2f}% (min {min(late):.2f} max {max(late):.2f})")'
)
new_print = (
    '        print(arm, "polar", round(summarise(polar)["mean"], 2), "+-", round(summarise(polar)["sd"], 2),\n'
    '              "| late", round(summarise(late)["mean"], 2), "%")'
)
if old_print not in t:
    raise SystemExit("print block not found")
t = t.replace(old_print, new_print, 1)
p.write_text(t, encoding="utf-8")
print("patched")
