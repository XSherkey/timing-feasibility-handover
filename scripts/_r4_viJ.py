from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = "Results at n = 5 (cross-intent transfer, the alternative-physics twin) are reported as"
new = ("Results at n = 5 (the alternative-physics twin; the cross-intent transfer now uses ten seeds) "
       "are reported as")
assert t.count(old) == 1, t.count(old)
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("EN VI-J updated")

z = D / "paper_zh.md"
s = z.read_text(encoding="utf-8")
old2 = "n = 5 的结果（跨意图转移、替代物理孪生）作描述性报告"
new2 = "n = 5 的结果（替代物理孪生；跨意图转移现用十个种子）作描述性报告"
if s.count(old2) == 1:
    s = s.replace(old2, new2, 1)
    z.write_text(s, encoding="utf-8")
    print("ZH VI-J updated")
else:
    print("ZH anchor count:", s.count(old2))
