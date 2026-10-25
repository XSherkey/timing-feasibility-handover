from pathlib import Path

p = Path(__file__).resolve().parent / "_r16_arch.py"
t = p.read_text(encoding="utf-8")

a = 'ax.add_patch(FancyArrowPatch((2.92, rects["llm"][1] - PAD), (2.92, rects["probe"][1] + 0.9 + PAD),'
b = 'ax.add_patch(FancyArrowPatch((2.25, rects["llm"][1] - PAD), (2.25, rects["probe"][1] + 0.9 + PAD),'
print("arrow found:", t.count(a))
t = t.replace(a, b, 1)

c = '    ax.text(0.15, 3.30, "calibration and admission — validation window only", fontsize=6.4,'
d = '    ax.text(2.45, 3.30, "calibration and admission — validation window only", fontsize=6.4,'
print("label found:", t.count(c))
t = t.replace(c, d, 1)

p.write_text(t, encoding="utf-8")
print("patched")
