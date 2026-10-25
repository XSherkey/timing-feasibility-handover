"""R26 part 2: add the variance decomposition table and an honest overhead note."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

ts = json.loads((ROOT / "almond-repro" / "results" / "routeA_r3" / "traffic_seeds" / "summary.json")
                .read_text(encoding="utf-8"))
rows = []
for arm in ("no_shield", "reward_lam8", "mined_16", "deployed_18", "tuned_constant"):
    a = ts[arm]
    rows.append(f"| {arm.replace('_', ' ')} | {a['summary']['mean']:.2f} | {a['sd_policy']:.2f} | {a['sd_traffic']:.2f} | "
                f"{a['share_policy']:.2f} / {a['share_traffic']:.2f} |")
TABLE = ("**Table Vd. Where the variance lives (polar HSR, five policy seeds × five traffic seeds, n = 25 cells "
         "per arm).** The two columns are the standard deviations of the per-policy and per-traffic means; the "
         "last column is the share of total sum of squares.\n\n"
         "| arm | mean (%) | policy sd | traffic sd | share policy / traffic |\n"
         "|---|---|---|---|---|\n" + "\n".join(rows) + "\n")

anchor = "### J. Statistical protocol"
i = t.find(anchor)
if i < 0:
    raise SystemExit("VI-J not found")
j = t.find("\n\n", i)
t = t[:j] + "\n\n" + TABLE + t[j:]

# honest overhead sentence in the limitations section
old = "None of the three affects the ordering claims"
new = ("A fourth limit is on the metric side: we report success, the three failure classes, mean latency through "
       "the satisfaction score, and the probe budget (52 polar attempts, 1.7% of a stream, or 0.46% of a training "
       "budget for one calibration), but not p95/p99 latency or signalling counts, so the claim that a longer lead "
       "is \"nearly free\" is bounded to the metrics we do report. None of the four affects the ordering claims")
if t.count(old) == 1:
    t = t.replace(old, new, 1)
    print("limitations extended")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("rows:", len(rows))
