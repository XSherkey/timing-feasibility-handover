from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "main.tex"
t = p.read_text(encoding="utf-8")

start = t.find("\\begin{table}[t]\n\\centering\n\\caption{Probe cost per calibration.}")
if start < 0:
    raise SystemExit("cost table not found")
end = t.find("\\end{table}", start) + len("\\end{table}")
block = t[start:end]
t = t[:start] + t[end:]

anchor = "\\textbf{Probing accuracy.}"
i = t.find(anchor)
if i < 0:
    raise SystemExit("anchor not found")
# insert after the paragraph containing the anchor (next blank line)
j = t.find("\n\n", i)
t = t[:j] + "\n\n" + block + t[j:]
p.write_text(t, encoding="utf-8")
print("moved the cost table in main.tex")
print("table order now:", [m for m in __import__("re").findall(r"\\label\{(tab:[a-z]+)\}", t)])
