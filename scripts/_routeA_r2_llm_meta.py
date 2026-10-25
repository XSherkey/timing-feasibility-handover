"""R2 / C5: what the LLM-call artefacts can and cannot pin down about the model version.

The paper's Section III now makes a version-pinning claim.  This script checks the
actual logs: which model string was used, how many calls, whether a timestamp exists
(the logs may not carry one), and how many calls were served from cache.
"""
from __future__ import annotations

import glob
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def main() -> int:
    files = sorted(glob.glob("results/campaign_1023/*/llm_calls.jsonl"))
    models, backends, call_types = Counter(), Counter(), Counter()
    per_run = {}
    stamps = []
    n_calls = 0
    cached = 0
    schema_bad = 0
    fields_seen = set()
    for p in files:
        run = Path(p).parent.name
        c = 0
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            n_calls += 1
            c += 1
            fields_seen.update(r)
            models[str(r.get("model"))] += 1
            backends[str(r.get("backend"))] += 1
            call_types[str(r.get("call_type"))] += 1
            cached += bool(r.get("from_cache"))
            schema_bad += not bool(r.get("schema_ok", True))
            for key in ("timestamp", "time", "ts", "created_at", "created"):
                if key in r:
                    stamps.append(str(r[key]))
        per_run[run] = dict(calls=c, mtime=datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds"))

    payload = dict(
        n_files=len(files), n_calls=n_calls, from_cache=cached,
        schema_failures=schema_bad,
        models=dict(models), backends=dict(backends), call_types=dict(call_types),
        fields=sorted(fields_seen),
        timestamps_in_logs=len(stamps),
        earliest=min(stamps) if stamps else None,
        latest=max(stamps) if stamps else None,
        timestamp_note=("logs carry no timestamp field; file mtimes are used as a proxy"
                        if not stamps else "timestamps taken from the log records"),
        runs=dict(sorted(per_run.items())),
        runs_mtime_range=(min((v["mtime"] for v in per_run.values()), default=None),
                          max((v["mtime"] for v in per_run.values()), default=None)),
    )
    Path("results/routeA_r2").mkdir(parents=True, exist_ok=True)
    json.dump(payload, open("results/routeA_r2/llm_meta.json", "w", encoding="utf-8"), indent=2)
    print(json.dumps({k: payload[k] for k in ("n_files", "n_calls", "from_cache", "models",
                                              "backends", "timestamps_in_logs", "runs_mtime_range")},
                     indent=2))
    print("fields:", payload["fields"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
