"""R2 driver utilities: run many eval_shield/probe commands in parallel, with logging."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = ROOT / "results" / "routeA_r2" / "commands.log"


def log(line: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(5):
        try:
            with LOG.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            return
        except OSError:
            time.sleep(0.2)


def run(cmd: list[str]) -> tuple[list[str], int]:
    log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] exit={r.returncode} :: {' '.join(cmd[:4])}")
    return cmd, r.returncode


def run_many(cmds: list[list[str]], workers: int = 6) -> list[int]:
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return [code for _cmd, code in ex.map(run, cmds)]


def read_one(path: Path) -> dict:
    d = json.load(open(path, encoding="utf-8"))
    return d[-1] if isinstance(d, list) else d


def polar(path: Path) -> float:
    return 100.0 * read_one(path)["arctic"][0]


def summary(path: Path) -> dict:
    rec = read_one(path)
    return dict(arctic=100.0 * rec["arctic"][0], midlat=100.0 * rec["midlat"][0],
                S=rec.get("satisfaction"), causes=rec.get("polar_causes", {}))


def mean_sd(vals: list[float]) -> tuple[float, float]:
    import statistics as st
    return (round(st.mean(vals), 2), round(st.stdev(vals), 2) if len(vals) > 1 else 0.0)
