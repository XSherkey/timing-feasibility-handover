import glob
import json
from pathlib import Path

dirs = sorted(set(str(Path(p).parent) for p in
                 glob.glob("results/**/no_forensics_seed0/run_summary.json", recursive=True)))
for d in dirs:
    j = json.loads((Path(d) / "run_summary.json").read_text(encoding="utf-8"))
    par = j.get("params") if isinstance(j.get("params"), dict) else {}
    cfg = j.get("config") if isinstance(j.get("config"), dict) else {}
    lam = par.get("late_risk_weight", cfg.get("late_risk_weight"))
    print(f"{d:55s} lam={lam}")
