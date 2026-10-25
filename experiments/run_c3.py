"""Per-seed drift response of the deployed arm (campaign policies + tau_used = 18 s) at four regimes."""
from __future__ import annotations

from r3lib import OUT, SEEDS, arctic, evaluate, summarise, write

ALMOND = {s: f"results/campaign_1023/almond_seed{s}" for s in SEEDS}
R18 = "min_advance:18@latitude_abs_deg>=68"


def main() -> int:
    out = {}
    for acq, tag in ((1.2, "0"), (3.2, "+2"), (4.4, "+3.2"), (5.6, "+4.4")):
        vals = [arctic(evaluate(f"c3_{tag}_deployed_s{s}", run=ALMOND[s], rule=R18, acq=acq))
                for s in SEEDS]
        out[tag] = dict(polar=vals, summary=summarise(vals))
        print(tag, round(summarise(vals)["mean"], 2), round(summarise(vals)["sd"], 2))
    write(OUT / "c3_deployed" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
