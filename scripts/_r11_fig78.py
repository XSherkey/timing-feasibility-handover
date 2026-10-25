from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
for name, pre in (("paper_en.md", "Fig. "), ("paper_zh.md", "图 ")):
    p = D / name
    t = p.read_text(encoding="utf-8")
    n7, n8 = t.count(pre + "7"), t.count(pre + "8")
    t = t.replace(pre + "7", "@@SEVEN@@").replace(pre + "8", pre + "7").replace("@@SEVEN@@", pre + "8")
    p.write_text(t, encoding="utf-8")
    print(f"{name}: swapped {n7} sevens and {n8} eights")
