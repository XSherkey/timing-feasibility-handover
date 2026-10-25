"""T2-06 (final) — inter-annotator agreement between the manual annotation, the mechanical rubric
and a sharper language-model judge ("would an expert deploy this rule as-is?").

Run:  python experiments/analyse_annotation.py
Out:  results/routeA_r3/llm_proposals/agreement.json
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import numpy as np

from r3lib import OUT, ROOT, write

FIELDS = {"elevation_deg", "handover_advance_s", "isl_hop_count", "doppler_rate_hz_s",
          "latitude_abs_deg", "snr_db", "remaining_visibility_s", "plane_change",
          "path_available", "buffer_occupancy", "battery_state", "eclipse",
          "satellite_latitude_deg"}
EFFECTS = {"min_advance", "cap_advance", "power_cap", "prefer_same_plane",
           "prefer_long_visibility", "forbid_unrouted_target", "buffer_drain"}


def kappa(a, b) -> float:
    a = np.asarray(a, bool)
    b = np.asarray(b, bool)
    po = float(np.mean(a == b))
    pa, pb = float(np.mean(a)), float(np.mean(b))
    pe = pa * pb + (1 - pa) * (1 - pb)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def judge_deployable(narrative: str, rule: dict) -> bool:
    import urllib.request

    from almond.llm.backend import OpenAICompatBackend

    be = OpenAICompatBackend()
    sys = ("You are a LEO satellite operations engineer. Decide whether the proposed guard rule "
           "could be deployed AS IS to reduce failed handovers: the predicate must use declared "
           "telemetry fields, the scope must cover the failures shown, and the magnitude must be "
           "large enough for the acquisition times in the narrative without exceeding the remaining "
           "visibility. Answer JSON only: {\"deploy\": true|false, \"why\": \"...\"}")
    usr = f"NARRATIVE: {narrative}\nRULE: {json.dumps(rule)}"
    body = {"model": be.model,
            "messages": [{"role": "system", "content": sys}, {"role": "user", "content": usr}],
            "temperature": 0.0, "response_format": {"type": "json_object"}}
    req = urllib.request.Request(f"{be.base_url}/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {be.api_key}"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as resp:
        out = json.loads(resp.read().decode())
    try:
        return bool(json.loads(out["choices"][0]["message"]["content"]).get("deploy"))
    except Exception:
        return False


def main() -> int:
    d = OUT / "llm_proposals"
    props = {r["narrative_id"]: r for r in csv.DictReader(open(d / "proposals.csv", encoding="utf-8"))}
    ann = {r["narrative_id"]: r for r in csv.DictReader(open(d / "annotation_human.csv", encoding="utf-8"))}
    ids = sorted(props, key=int)

    human = [ann[i]["verdict"] == "accept" for i in ids]
    mech, judge = [], []
    for i in ids:
        rule = json.loads(props[i]["p1_rule"])
        atoms = rule.get("atoms") or []
        mech.append(bool(atoms) and all(a.get("field") in FIELDS for a in atoms)
                    and rule.get("effect") in EFFECTS)
        jp = d / f"judge_{i}.json"
        if jp.exists():
            judge.append(bool(json.loads(jp.read_text(encoding="utf-8"))["deploy"]))
        else:
            v = judge_deployable(props[i]["narrative"], rule)
            jp.write_text(json.dumps(dict(deploy=v)), encoding="utf-8")
            judge.append(v)

    out = dict(n=len(ids),
               human_accept_rate=float(np.mean(human)),
               mechanical_rate=float(np.mean(mech)),
               judge_rate=float(np.mean(judge)),
               kappa_human_judge=kappa(human, judge),
               kappa_human_mech=kappa(human, mech),
               kappa_judge_mech=kappa(judge, mech),
               agreement_human_judge=float(np.mean(np.asarray(human) == np.asarray(judge))),
               per_item=[dict(id=i, human=bool(h), judge=bool(j), mechanical=bool(m))
                         for i, h, j, m in zip(ids, human, judge, mech)])
    write(d / "agreement.json", out)
    print(json.dumps({k: out[k] for k in ("human_accept_rate", "judge_rate", "mechanical_rate",
                                          "kappa_human_judge", "kappa_human_mech",
                                          "agreement_human_judge")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
