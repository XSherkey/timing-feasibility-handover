from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
t = (D / "paper_en.md").read_text(encoding="utf-8")
i = t.find("The tuned constant is the strongest objection")
j = t.find("\n\n", t.find("start high and stay there.", i))
print(t[i:j])
