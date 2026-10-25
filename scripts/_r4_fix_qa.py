from pathlib import Path

p = Path(__file__).resolve().parent / "_r4_qa.py"
t = p.read_text(encoding="utf-8")
t = t.replace('"lim7-bounded": ["is *bounded*", "**收窄**"],',
              '"lim7-bounded": ["is bounded", "收窄"],')
t = t.replace('print("   Table D1 16-18 row:", [c.text.strip() for c in tb.rows[5].cells])',
              'print("   D1 rows 14-16 / 16-18:", [[c.text.strip() for c in tb.rows[k].cells] for k in (5, 6)])')
p.write_text(t, encoding="utf-8")
print("patched QA")
