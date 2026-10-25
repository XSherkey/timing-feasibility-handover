"""T1-01 - rebuild Table VI (alternative physics) from fresh evaluations, with the full metric set.

Two altered twins (ISL seam disabled; feeder capacity reduced to three slots) x three constraint
states (no shield, mined 16 s rule, deployed tau_used = 18 s) x two policy families, each at n = 5
policy seeds, evaluated on common episodes.

Run:  python experiments/run_alternative_physics.py
Out:  results/routeA_r3/alternative_physics/summary.json
"""
from __future__ import annotations

import numpy as np

from r3lib import OUT, arctic, evaluate, late_share, summarise, write

SEEDS5 = [0, 1, 2, 3, 4]
TWINS = {
    "seam disabled": dict(no_seam=True),
    "feeder 3 slots": dict(feeder_slots=3),
}
ARMS = {
    "no shield": None,
    "mined 16 s": "min_advance:16@latitude_abs_deg>=68",
    "tau_used = 18 s": "min_advance:18@latitude_abs_deg>=68",
}
POLICIES = {"full-system": "almond", "PPO-MLP": "ppomlp"}


def main() -> int:
    # r3lib.evaluate does not forward twin kwargs; call eval_shield directly with the extra flags
    import json
    import subprocess
    import sys
    from pathlib import Path

    from r3lib import ROOT

    out = {}
    for tname, tkw in TWINS.items():
        for pname, pref in POLICIES.items():
            for aname, rule in ARMS.items():
                vals, lates, wins, routes = [], [], [], []
                for s in SEEDS5:
                    cmd = [sys.executable, str(ROOT / "scripts" / "eval_shield.py"),
                           "--run", f"results/campaign_1023/{pref}_seed{s}"]
                    for k, v in tkw.items():
                        cmd += [f"--{k.replace('_', '-')}"]
                        if not isinstance(v, bool):
                            cmd += [str(v)]
                    if rule:
                        cmd += ["--rule", rule]
                    cp = OUT / "_cache" / f"altphys_{tname.replace(' ', '')}_{pname.replace('-', '')}_{aname.replace(' ', '')}_{s}.json".replace("=", "")
                    cmd += ["--out", str(cp), "--label", f"{tname}/{pname}/{aname}/s{s}"]
                    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                                       errors="replace", cwd=str(ROOT))
                    if r.returncode != 0:
                        raise RuntimeError(r.stderr[-500:])
                    d = json.loads(Path(cp).read_text(encoding="utf-8"))[0]
                    vals.append(arctic(d))
                    pc = d.get("polar_causes") or {}
                    lates.append(100.0 * float(pc.get("late_handover", 0.0)))
                    wins.append(100.0 * float(pc.get("window_exceeded", 0.0)))
                    routes.append(100.0 * float(pc.get("no_route", 0.0)))
                out[f"{tname}|{pname}|{aname}"] = dict(
                    polar=summarise(vals), late=float(np.mean(lates)),
                    window=float(np.mean(wins)), no_route=float(np.mean(routes)), per_seed=vals)
                print(f"{tname:15s} {pname:12s} {aname:16s} HSR {np.mean(vals):6.2f} "
                      f"late {np.mean(lates):5.2f} win {np.mean(wins):5.2f} no_route {np.mean(routes):5.2f}")
    write(OUT / "alternative_physics" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
