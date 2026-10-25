from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "main.md"
t = p.read_text(encoding="utf-8")

block = (
    "**Table VI. Probe cost per calibration.**\n"
    "| configuration | episodes | env steps | share of a 9600-episode training run |\n"
    "|---|---|---|---|\n"
    "| probe, 2 episodes/advance | 22 | 5,280 | 0.23% |\n"
    "| probe, 8 episodes/advance | 88 | 21,120 | 0.92% |\n"
)
if block not in t:
    raise SystemExit("block not found")
t = t.replace(block, "", 1)

anchor = "**Probing accuracy.** As above: the threshold is identifiable to about +/-2 s"
i = t.find(anchor)
if i < 0:
    raise SystemExit("anchor not found")
end = t.find("\n\n**The constant.**", i)
if end < 0:
    raise SystemExit("end marker not found")
t = t[:end] + "\n\n" + block.strip() + "\n" + t[end:]
p.write_text(t, encoding="utf-8")
print("moved in main.md")
