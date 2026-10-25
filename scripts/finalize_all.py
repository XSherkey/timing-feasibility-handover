"""Run the whole finalisation chain in ONE interpreter.

The machine has to be treated gently: every fresh Python start costs minutes (the
scientific stack is re-imported and anti-virus re-scans it) and each process adds
disk churn.  This driver imports the three finalisers as modules and runs them in
order in a single process.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    print("=== 1/3 statistics + figures ===", flush=True)
    load("finalize").main()

    print("\n=== 2/3 BC-vs-final + TBD values ===", flush=True)
    load("finalize2").main()

    print("\n=== 3/3 manuscript refill + Chinese report ===", flush=True)
    load("finalize3").main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
