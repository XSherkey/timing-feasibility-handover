"""R8 part 3: merge the two factorial tables into one, renumber the drift table, and reshape D1A/D1B."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
fc = json.loads((ROOT / "results" / "routeA_r3" / "factorial_consistent" / "summary.json").read_text(encoding="utf-8"))
c3 = json.loads((ROOT / "results" / "routeA_r3" / "c3_deployed" / "summary.json").read_text(encoding="utf-8"))
dm = json.loads((ROOT / "results" / "routeA_r3" / "drift_margin" / "summary.json").read_text(encoding="utf-8"))
F = fc["arms"]

p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

# ---- merge C1 + C2 into a single Table C1 --------------------------------
i = t.find("**Table C1. Frozen-policy factorial")
j = t.find("\n\n", t.find("| late-handover share", t.find("**Table C2.")))
if i < 0 or j < 0:
    raise SystemExit("C1/C2 block not found")
rows = ["| seed | no shield | τ = 16 s | τ = 18 s (deployed) | τ = 20 s | oracle |",
        "|---|---|---|---|---|---|"]
for k in range(10):
    rows.append("| %d | %.1f | %.1f | %.1f | %.1f | %.1f |" % (
        k, F["none"]["polar"][k], F["rule16"]["polar"][k], F["rule18"]["polar"][k],
        F["rule20"]["polar"][k], F["oracle"]["polar"][k]))
rows.append("| mean ± sd | %.1f ± %.1f | %.2f ± %.2f | **%.2f ± %.2f** | %.2f ± %.2f | %.2f ± %.2f |" % (
    F["none"]["summary"]["mean"], F["none"]["summary"]["sd"],
    F["rule16"]["summary"]["mean"], F["rule16"]["summary"]["sd"],
    F["rule18"]["summary"]["mean"], F["rule18"]["summary"]["sd"],
    F["rule20"]["summary"]["mean"], F["rule20"]["summary"]["sd"],
    F["oracle"]["summary"]["mean"], F["oracle"]["summary"]["sd"]))
late16 = sum(F["rule16"]["late"]) / len(F["rule16"]["late"])
none_late = F["none"]["late"]
rows.append("| late-handover share | %.1f–%.1f%% (mean %.1f%%) | %.2f%% | 0.00%% | 0.00%% | 0.00%% |" % (
    min(none_late), max(none_late), sum(none_late) / len(none_late), late16))
C1 = ("**Table C1. Frozen-policy factorial, campaign checkpoints, polar HSR (%) per seed (|lat| ≥ 70°, "
      "traffic seed 0, common episodes, n = 10 policy seeds). The no-shield column is the same ten "
      "checkpoints before any constraint is applied; the τ = 18 s column is the deployed threshold and the "
      "oracle column coincides with it on every seed.**\n\n" + "\n".join(rows) + "\n")
t = t[:i] + C1 + t[j:]

# ---- the drift table becomes C2 -----------------------------------------
t = t.replace("**Table C3. Per-seed drift response", "**Table C2. Per-seed drift response", 1)
t = t.replace("| Drift response (Table V, Table C3) |", "| Drift response (Table V, Table C2) |", 1)

# ---- D1A / D1B: 4 columns, arithmetic visible in one cell ----------------
for tag in ("Table D1A.", "Table D1B."):
    a = t.find("**" + tag)
    b = t.find("\n\n", t.find("| total |", a))
    if a < 0 or b < 0:
        raise SystemExit(f"{tag} not found")
    block = t[a:b]
    lines = [ln for ln in block.splitlines() if ln.strip()]
    out, head_done = [], False
    for ln in lines:
        if not ln.startswith("|"):
            out.append(ln)
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("- "):
            out.append("| --- | --- | --- | --- |")
            continue
        if not head_done:
            out.append("| advance bucket (s) | attempts | exact + right-censored + competing = attempts | share of attempts |")
            head_done = True
            continue
        if len(cells) < 6:
            continue
        bucket = cells[0]
        try:
            att = int(cells[1].replace(",", ""))
        except ValueError:
            continue
        exc, cen, comp = (int(c.replace(",", "")) for c in cells[2:5])
        share = cells[5]
        if bucket.lower().startswith(("total", "合计")):
            out.append(f"| **total** | **{att:,}** | {exc:,} + {cen:,} + {comp:,} = {att:,} | **100%** |")
        else:
            out.append(f"| {bucket} | {att:,} | {exc:,} + {cen:,} + {comp:,} = {att:,} | {share} |")
    t = t[:a] + "\n".join(out) + t[b:]

p.write_text(t, encoding="utf-8")
print("C1 merged; C3->C2; D1 reshaped")
