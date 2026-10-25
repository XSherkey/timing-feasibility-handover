"""Run one method of the campaign in its own process (shard launcher).

The full protocol is 8 methods x 10 seeds; the original study ran the shards in
parallel because each run is single-threaded (``OMP/MKL_NUM_THREADS=1``).  This
wrapper pins the same environment as the historical launch scripts and writes a
per-shard log:

    python scripts/run_campaign_shard.py --method almond --seeds 0-9 \
        --spec results/nas/llm_spec.json --out results/campaign

Pass ``--no-llm`` (or simply leave ``ALMOND_LLM_API_KEY`` unset) to force the
offline surrogate backend; with a key set, cache hits from ``results/llm_cache``
still mean the run makes no network call.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: methods that must reuse a pre-discovered architecture instead of searching
DEFAULT_SPEC = {
    "almond": "results/nas/llm_spec.json",
    "unseeded_evonas": "results/nas/random_spec.json",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True, help="or a comma separated list")
    ap.add_argument("--seeds", default="0-9")
    ap.add_argument("--spec", default=None, help="defaults per method (see DEFAULT_SPEC)")
    ap.add_argument("--out", default="results/campaign")
    ap.add_argument("--episodes", type=int, default=9600)
    ap.add_argument("--eval-every", type=int, default=1200)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    env = dict(os.environ)
    env.update(
        PYTHONIOENCODING="utf-8",
        OMP_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        ALMOND_HC_PENALTY="0.05",
        ALMOND_LLM_CACHE="1",
        ALMOND_LLM_CACHE_DIR="results/llm_cache",
    )
    if args.no_llm or not env.get("ALMOND_LLM_API_KEY"):
        env.pop("ALMOND_LLM_BASE_URL", None)
        env["ALMOND_LLM_BACKEND"] = "surrogate"
        if not args.no_llm:
            print("[shard] ALMOND_LLM_API_KEY not set -> offline surrogate backend")
    else:
        env.setdefault("ALMOND_LLM_BASE_URL", "https://api.deepseek.com")
        env.setdefault("ALMOND_LLM_MODEL", "deepseek-flash")
        env.setdefault("ALMOND_LLM_CONCURRENCY", "4")

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    log_dir = out / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / f"{args.method.replace(',', '_')}.log"

    spec = args.spec
    if spec is None and args.method in DEFAULT_SPEC:
        spec = DEFAULT_SPEC[args.method]

    cmd = [
        args.python, "-u", "scripts/run_campaign.py",
        "--methods", args.method,
        "--seeds", args.seeds,
        "--episodes", str(args.episodes),
        "--eval-every", str(args.eval_every),
        "--device", args.device,
        "--out", str(out),
    ]
    if spec:
        cmd += ["--spec-file", spec]

    print(f"[shard] {' '.join(cmd)}")
    print(f"[shard] log -> {log}")
    with log.open("w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.run(cmd, cwd=str(ROOT), env=env, stdout=fh, stderr=subprocess.STDOUT)
    print(f"[shard] {args.method} exit={proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
