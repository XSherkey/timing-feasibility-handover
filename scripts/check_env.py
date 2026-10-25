"""Environment sanity check for the ALMOND reproduction.

Verifies that every third-party dependency imports, prints versions, reports the
CUDA status of torch and the digital-twin cache state.  Run it after creating the
conda environment (see ``requirements.txt`` and ``docs/ENVIRONMENT_SETUP.md``)::

    python scripts/check_env.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REQUIRED = {
    "numpy": "numpy",
    "scipy": "scipy",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "sklearn": "scikit-learn",
    "sgp4": "sgp4",
    "torch": "torch",
    "onnx": "onnx",
    "onnxruntime": "onnxruntime",
    "docx": "python-docx",
    "lxml": "lxml",
    "tqdm": "tqdm",
}

#: modules the package itself imports at runtime; catching a missing one here is
#: much cheaper than catching it 200 episodes into a campaign
LOCAL = [
    "almond.twin.twin",
    "almond.twin.constellation",
    "almond.twin.geometry",
    "almond.twin.topology",
    "almond.twin.handover_env",
    "almond.llm.backend",
    "almond.llm.surrogate",
    "almond.framework.system",
    "almond.framework.auditor",
    "almond.framework.forensics",
    "almond.framework.kg",
    "almond.framework.shield",
    "almond.policies.nets",
    "almond.policies.ppo",
    "almond.nas.evolution",
    "almond.analysis.metrics",
    "almond.analysis.stats",
]


def main() -> int:
    print(f"python      {sys.version.split()[0]}  ({sys.executable})")
    ok = True

    print("\n== third-party packages ==")
    for mod, dist in REQUIRED.items():
        try:
            m = __import__(mod)
            ver = getattr(m, "__version__", "?")
            print(f"  {dist:<14} {ver}")
        except Exception as exc:  # noqa: BLE001 - report and continue
            ok = False
            print(f"  {dist:<14} MISSING ({exc})")

    print("\n== project modules ==")
    for name in LOCAL:
        try:
            __import__(name)
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"  {name:<32} FAIL ({type(exc).__name__}: {exc})")
    print(f"  {len(LOCAL)} modules imported" if ok else "  import errors above")

    print("\n== torch / CUDA ==")
    try:
        import torch

        print(f"  torch {torch.__version__}  cuda_available={torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  device 0: {torch.cuda.get_device_name(0)}  cc={torch.cuda.get_device_capability(0)}")
            x = torch.randn(64, 64, device="cuda")
            print(f"  matmul on GPU ok: {(x @ x).sum().item():.3f}")
            del x
        else:
            print("  WARNING: CUDA not available - run the campaign with --device cpu")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"  FAIL {type(exc).__name__}: {exc}")

    print("\n== digital-twin cache ==")
    cache_root = ROOT / "data" / "cache"
    if not cache_root.exists():
        print(f"  no cache yet ({cache_root}); run scripts/build_twin.py")
    else:
        for d in sorted(cache_root.iterdir()):
            meta = d / "meta.json"
            if not meta.exists():
                print(f"  {d.name:<34} incomplete")
                continue
            m = json.loads(meta.read_text(encoding="utf-8"))
            size_mb = sum(f.stat().st_size for f in d.glob("*.npy")) / 1e6
            print(
                f"  {d.name:<34} {m['n_sat']} sats x {m['n_time']} epochs  "
                f"{m['horizon_s'] / 3600:.1f} h  {size_mb:.0f} MB"
            )

    print("\nRESULT:", "OK" if ok else "PROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
