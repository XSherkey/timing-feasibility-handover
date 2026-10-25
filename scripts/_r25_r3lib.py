"""Allow r3lib.evaluate to pass several --rule flags (needed for the two-sided feasibility case)."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parents[1] / "experiments" / "r3lib.py"
s = p.read_text(encoding="utf-8")

old_sig = "    rule: str | None = None,\n"
new_sig = "    rule: str | None = None,\n    rules: list[str] | None = None,\n"
print("sig:", s.count(old_sig))
s = s.replace(old_sig, new_sig, 1)

old_params = '    params = dict(label=label, run=run, policy=policy, rule=rule, oracle=oracle, window=window,'
new_params = ('    rules = list(rules or ([] if rule is None else [rule]))\n'
              '    params = dict(label=label, run=run, policy=policy, rule="|".join(rules), oracle=oracle, window=window,')
print("params:", s.count(old_params))
s = s.replace(old_params, new_params, 1)

old_cmd = '    if rule:\n        cmd += ["--rule", rule]\n'
new_cmd = '    for r in rules:\n        cmd += ["--rule", r]\n'
print("cmd:", s.count(old_cmd))
s = s.replace(old_cmd, new_cmd, 1)

p.write_text(s, encoding="utf-8")
print("patched r3lib")
