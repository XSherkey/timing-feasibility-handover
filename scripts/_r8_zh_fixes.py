from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
z = D / "paper_zh.md"
t = z.read_text(encoding="utf-8")
n = 0
if "``late_handover``" in t:
    t = t.replace("``late_handover``", "`late_handover`")
    n += 1
old2 = 'atoms       : list of {"field": ..., "cmp": one of <,<=,>,>=,==,!=, "value": number}'
if old2 in t:
    t = t.replace(old2,
                  'atoms       : list of {"field": ..., "cmp": one of "lt","le","gt","ge","eq","ne",\n'
                  '               "value": number}')
    n += 1
# the ZH verification paragraph after D1B
i = t.find("*核验。* 每一行满足")
if i > 0:
    j = t.find("\n\n", i)
    t = t[:i] + t[j + 2:]
    n += 1
z.write_text(t, encoding="utf-8")
print("ZH fixes:", n)
