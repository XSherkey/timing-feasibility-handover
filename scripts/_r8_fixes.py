"""R9 part 1: content fixes for review 12."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print(f"  MISS [{label}] {n}: {old[:60]}")
        return
    t = t.replace(old, new, 1)
    done.append(label)


# 1. drop the "Verification" paragraph that follows the D1B caption
i = t.find("*Verification.* Each row satisfies attempts")
if i > 0:
    j = t.find("\n\n", i)
    t = t[:i] + t[j + 2:]
    done.append("drop-verification")

# 2. Appendix E schema: word tokens instead of glyphs
rep('atoms       : list of {"field": ..., "cmp": one of <,<=,>,>=,==,!=, "value": number}',
    'atoms       : list of {"field": ..., "cmp": one of "lt","le","gt","ge","eq","ne",\n'
    '               "value": number}   # <, <=, >, >=, ==, != spelled out so the schema\n'
    '                                 # survives copy-paste through any PDF pipeline',
    "cmp-schema")

# 3. ordering ranges: derive from the printed table so reader and text agree
rep("the deployed arm is 0.39–0.92 pp above the mined 16 s rule and 0.86–1.58 pp above the same-rule PPO-MLP baseline",
    "the deployed arm is 0.38–0.92 pp above the mined 16 s rule and 0.86–1.59 pp above the same-rule PPO-MLP "
    "baseline (differences taken from the two-decimal values printed in Table X)", "ordering-round")

# 4. nomenclature: double backticks render literally
rep("is the share of attempts whose recorded cause is ``late_handover``.",
    "is the share of attempts whose recorded cause is `late_handover`.", "nomen-backtick")

# 5. Limitation 2: say which comparison the one-grid-step error costs
rep("at +4.4 s drift one of the five probe seeds returns 20 s instead of 22 s, i.e. one grid step low, "
    "which would cost it the difference between the fixed and the re-probed arm of Table V",
    "at +4.4 s drift one of the five probe seeds returns 20 s instead of 22 s, i.e. one grid step low; at that "
    "physics the fixed-18 s and re-probed arms differ by 9.7 pp (83.56 against 93.20 in Table V, the difference "
    "between a threshold that did not follow the physics and one that did), while the nominal cost of the same "
    "2 s step is only 0.13 pp (93.36 against 93.23)", "lim2")

p.write_text(t, encoding="utf-8")
print("applied:", done)
