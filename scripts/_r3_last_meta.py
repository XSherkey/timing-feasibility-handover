from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = "The gate has two defects we discovered and report because a replicating reviewer will find them too."
new = "The gate has two defects that any replication will expose."
if t.count(old) != 1:
    raise SystemExit("anchor not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("removed last reviewer mention")
