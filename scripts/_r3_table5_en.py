"""R3 (v11): replace the cross-intent table and text with the n = 8 results."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
t = (D / "paper_en.md").read_text(encoding="utf-8")
ci = json.loads((ROOT / "results" / "routeA_r3" / "cross_intent" / "summary.json").read_text(encoding="utf-8"))
pi = ci["per_intent"]
comm = ci["committed"]
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


def f(x, p=2):
    return f"{x:.{p}f}"


rows = ["| knowledge graph | intent 0 reliability | intent 1 latency | intent 2 power | intent 3 balanced | n |",
        "|---|---|---|---|---|---|"]
rows.append("| shared (inherited) | %s | **%s** | **%s** | **%s** | %d |" % (
    f(pi["reliability_first"]["shared"]["mean"]), f(pi["latency_first"]["shared"]["mean"]),
    f(pi["power_first"]["shared"]["mean"]), f(pi["balanced"]["shared"]["mean"]), len(ci["seeds"])))
rows.append("| fresh per intent | %s | %s | %s | %s | %d |" % (
    f(pi["reliability_first"]["fresh"]["mean"]), f(pi["latency_first"]["fresh"]["mean"]),
    f(pi["power_first"]["fresh"]["mean"]), f(pi["balanced"]["fresh"]["mean"]), len(ci["seeds"])))
rows.append("| transfer gain (pp) | +%s | +%s | +%s | +%s | |" % (
    f(pi["reliability_first"]["pair"]["mean_diff"]), f(pi["latency_first"]["pair"]["mean_diff"]),
    f(pi["power_first"]["pair"]["mean_diff"]), f(pi["balanced"]["pair"]["mean_diff"])))
rows.append("| exact Wilcoxon p | %s | %s | %s | %s | |" % tuple(
    ("%.4f" % pi[k]["pair"]["wilcoxon_p"]) if pi[k]["pair"]["wilcoxon_p"] is not None else "--"
    for k in ("reliability_first", "latency_first", "power_first", "balanced")))
TABLE5 = "\n".join(rows)

start = t.find("**Table V. Cross-intent transfer")
end = t.find("\n\n", t.find("| 转移增益", start) if "| 转移增益" in t[start:start + 2000] else t.rfind("|", start, t.find("\n\n", start)))
if start < 0:
    raise SystemExit("Table V not found")
# replace the caption + the markdown table that follows it
tbl_start = t.find("|", start)
tbl_end = t.find("\n\n", tbl_start)
new_table = ("**Table V. Cross-intent transfer (polar HSR at |lat| ≥ 70°, mean over policy seeds; the "
             "training seeds that committed a rule at intent 0 are %d of %d, and the table reports all "
             "seeds, so seeds without a committed rule contribute identically to both arms).**\n\n"
             % (comm["n"], len(ci["seeds"])) + TABLE5 + "\n")
t = t[:start] + new_table + t[tbl_end:]
done.append("table5")

(D / "paper_en.md").write_text(t, encoding="utf-8")
print("applied:", done)
print(TABLE5)
