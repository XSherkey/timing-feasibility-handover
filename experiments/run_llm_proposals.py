"""T2-06 - LLM proposal quality, reproducibility and magnitude (in)stability.

Twenty failure narratives are drawn from the **training window only** (a passive no-shield run,
t_index < 60% of the twin horizon, worst attempts first).  Each narrative is sent to the final
prompt in two variants:

  P1  predicate only        -> {"effect", "magnitude", "atoms", "reading"}
  P2  predicate + magnitude -> same, plus an explicit "magnitude_s" justification field

Outputs are schema-validated exactly as the pipeline validates them, saved verbatim, and annotated
twice: (A) a mechanical rubric (field in the telemetry grammar, operator legal, effect executable,
scope non-empty, magnitude in the admissible range) and (B) an independent language-model judge
that is shown the rubric but not verdict (A).  Cohen's kappa between the two is reported.

Magnitude stability is probed by re-sending the same narrative with every acquisition time shifted
by +2 s (the drift the paper studies), and asking whether the proposed magnitude moves.

Run:  python experiments/run_llm_proposals.py        (needs ALMOND_LLM_BASE_URL / API key)
Out:  results/routeA_r3/llm_proposals/{summary.json,proposals.csv,prompt_examples.md}
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import numpy as np

from r3lib import OUT, ROOT, write

TRAIN_FRAC = 0.60
N_NARR = 20
MODEL = os.environ.get("ALMOND_LLM_MODEL", "deepseek-flash")

SYSTEM_P1 = (
    "You are a satellite-network operations analyst. You read temporal narratives of failed "
    "handover episodes and propose the single most plausible latent operational rule, expressed in "
    "a constrained predicate grammar. Rules must reference only declared telemetry fields, must be "
    "physically plausible under SGP4-propagated geometry, and must be falsifiable by counterfactual "
    "replay. You answer with JSON only."
)
SYSTEM_P2 = SYSTEM_P1[:-len("You answer with JSON only.")] + (
    "You also state the magnitude the rule should enforce, in seconds, with one sentence of "
    "justification. You answer with JSON only."
)

USER_TMPL = """OPERATOR INTENT: {intent}

DECLARED TELEMETRY FIELDS (rule predicates may use only these):
{fields}

EXECUTABLE EFFECTS:
{effects}

PAST FAILURE NARRATIVES (training window only):
{narratives}

Return JSON with exactly these keys:
  effect      : one of the effects above
  atoms       : list of {{"field": ..., "cmp": one of <,<=,>,>=,==,!=, "value": number}}
  magnitude   : number (seconds for lead-time effects){extra}
"""

FIELDS_TXT = """elevation_deg, handover_advance_s, isl_hop_count, doppler_rate_hz_s, latitude_abs_deg,
snr_db, remaining_visibility_s, plane_change, path_available, buffer_occupancy, battery_state,
eclipse, satellite_latitude_deg"""
EFFECTS_TXT = """min_advance, cap_advance, power_cap, prefer_same_plane, prefer_long_visibility,
forbid_unrouted_target, buffer_drain"""


def training_failures() -> list[dict]:
    """Failures from the TRAINING window only, produced by a passive no-shield rollout."""
    p = OUT / "llm_proposals" / "train_attempts.json"
    rows = json.loads(p.read_text(encoding="utf-8"))
    n_time = 4320
    rows = [a for a in rows
            if a["t_index"] < TRAIN_FRAC * n_time
            and a.get("cause") in ("late_handover", "window_exceeded", "no_route")]
    rows.sort(key=lambda a: float(a.get("handover_advance_s", 0.0)))
    return rows[: N_NARR * 4]


def narrate(rows: list[dict], shift: float = 0.0) -> str:
    from almond.framework.forensics import episodes_to_narratives

    shifted = []
    for r in rows:
        q = dict(r)
        q["t_setup_s"] = float(r.get("t_setup_s", 0.0)) + shift
        shifted.append(q)
    lines = episodes_to_narratives(shifted, per_line=4)
    return lines[0] if lines else ""


def call(system: str, user: str, seed: int = 0) -> tuple[dict | None, str, str]:
    from almond.llm.backend import OpenAICompatBackend

    be = OpenAICompatBackend()
    payload = {"system": system, "user": user}
    import urllib.request

    body = {
        "model": be.model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": seed,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        f"{be.base_url}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {be.api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        out = json.loads(resp.read().decode())
    text = out["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = None
    return parsed, text, be.model


def rubric(prop: dict | None) -> dict:
    """Mechanical annotation (A)."""
    if not isinstance(prop, dict):
        return dict(valid=False, reason="unparseable")
    fields = {f.strip() for f in FIELDS_TXT.replace("\n", " ").split(",")}
    effects = {e.strip() for e in EFFECTS_TXT.replace("\n", " ").split(",")}
    atoms = prop.get("atoms") or []
    ok_field = bool(atoms) and all(a.get("field") in fields for a in atoms)
    ok_cmp = all(a.get("cmp") in ("<", "<=", ">", ">=", "==", "!=") for a in atoms)
    ok_eff = prop.get("effect") in effects
    try:
        mag = float(prop.get("magnitude"))
        ok_mag = 0.0 <= mag <= 60.0
    except Exception:
        mag, ok_mag = None, False
    return dict(valid=bool(ok_field and ok_cmp and ok_eff and ok_mag),
                field=ok_field, cmp=ok_cmp, effect=ok_eff, magnitude=ok_mag, magnitude_s=mag)


def judge(narrative: str, prop: dict | None) -> bool:
    """Independent annotation (B): a language-model judge with the same rubric, blind to (A)."""
    if not isinstance(prop, dict):
        return False
    sys = ("You audit proposed operational rules for a LEO satellite handover simulator. "
           "A rule is VALID if its predicate uses only the declared telemetry fields, its operator "
           "is one of <,<=,>,>=,==,!=, its effect is executable, and it would plausibly reduce "
           "failed handovers in the narratives. Answer with JSON only: {\"valid\": true|false}.")
    usr = f"DECLARED FIELDS: {FIELDS_TXT}\nEFFECTS: {EFFECTS_TXT}\nNARRATIVES: {narrative}\nRULE: {json.dumps(prop)}"
    try:
        parsed, _txt, _m = call(sys, usr)
        return bool(parsed and parsed.get("valid"))
    except Exception:
        return False


def kappa(a: list[bool], b: list[bool]) -> float:
    a = np.asarray(a, bool)
    b = np.asarray(b, bool)
    if a.size == 0:
        return float("nan")
    po = float(np.mean(a == b))
    pa1, pb1 = float(np.mean(a)), float(np.mean(b))
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def main() -> int:
    if not os.environ.get("ALMOND_LLM_BASE_URL"):
        raise SystemExit("ALMOND_LLM_BASE_URL is not set")
    if not os.environ.get("ALMOND_LLM_API_KEY"):
        raise SystemExit(
            "ALMOND_LLM_API_KEY is not set. It is required to re-run the mining stage against a hosted "
            "model; the shipped artefacts (results/routeA_r3/llm_proposals/) let you inspect and replay the "
            "recorded calls without a key."
        )
    rows = training_failures()
    chunks = [rows[i: i + 4] for i in range(0, min(len(rows), N_NARR * 4), 4)][:N_NARR]
    recs = []
    for k, ch in enumerate(chunks, 1):
        narr = narrate(ch)
        narr_drift = narrate(ch, shift=2.0)
        base_payload = dict(intent="reliability first; polar handovers must not fail",
                            fields=FIELDS_TXT, effects=EFFECTS_TXT, narratives=narr)
        user1 = USER_TMPL.format(extra="", **base_payload)
        user2 = USER_TMPL.format(extra="\n  magnitude_justification : one sentence", **base_payload)
        p1, raw1, model = call(SYSTEM_P1, user1)
        p2, raw2, _ = call(SYSTEM_P2, user2)
        p2d, raw2d, _ = call(SYSTEM_P2, USER_TMPL.format(extra="\n  magnitude_justification : one sentence",
                                                         **dict(base_payload, narratives=narr_drift)))
        r1 = rubric(p1)
        v1 = judge(narr, p1)
        recs.append(dict(narrative_id=k, model=model, narrative=narr,
                         p1_raw=raw1, p1_rule=json.dumps(p1), p1_valid=bool(r1["valid"]),
                         p1_judge=bool(v1),
                         p2_raw=raw2, p2_rule=json.dumps(p2),
                         p2_magnitude=(p2 or {}).get("magnitude"),
                         p2_magnitude_drift=(p2d or {}).get("magnitude")))
        print(f"[{k:02d}] P1 valid={r1['valid']} judge={v1} | P2 mag={recs[-1]['p2_magnitude']} "
              f"drift mag={recs[-1]['p2_magnitude_drift']}")

    a = [r["p1_valid"] for r in recs]
    b = [r["p1_judge"] for r in recs]
    mags = [(r["p2_magnitude"], r["p2_magnitude_drift"]) for r in recs]
    both = [(float(x), float(y)) for x, y in mags if isinstance(x, (int, float)) and isinstance(y, (int, float))]
    same = sum(1 for x, y in both if abs(x - y) < 1e-9)
    summary = dict(
        model=MODEL, n_narratives=len(recs),
        valid_rate=float(np.mean(a)), judge_rate=float(np.mean(b)),
        kappa=kappa(a, b), agreement=float(np.mean(np.asarray(a) == np.asarray(b))),
        schema_fail_rate=1.0 - float(np.mean(a)),
        magnitude=dict(n_pairs=len(both),
                       unchanged_under_2s_drift=int(same),
                       share_unchanged=float(same / len(both)) if both else None,
                       mean=(float(np.mean([x for x, _ in both])) if both else None)),
        prompts=dict(P1=SYSTEM_P1 + "\n\n" + USER_TMPL.format(intent="{intent}", fields=FIELDS_TXT,
                                                              effects=EFFECTS_TXT,
                                                              narratives="{narratives}", extra=""),
                     P2=SYSTEM_P2 + "\n\n" + USER_TMPL.format(intent="{intent}", fields=FIELDS_TXT,
                                                              effects=EFFECTS_TXT,
                                                              narratives="{narratives}",
                                                              extra="\n  magnitude_justification : one sentence")),
        note=("The second annotator is a language-model judge, not a human; a human re-annotation of "
              "the same twenty items is required before submission."),
    )
    write(OUT / "llm_proposals" / "summary.json", summary)

    d = OUT / "llm_proposals"
    d.mkdir(parents=True, exist_ok=True)
    with (d / "proposals.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
        w.writeheader()
        for r in recs:
            w.writerow(r)
    (d / "prompt_examples.md").write_text(
        "# Prompt appendix (verbatim, first three calls)\n\n"
        + "\n\n".join(f"## Call {r['narrative_id']}\n\n**P1 raw output**\n```json\n{r['p1_raw']}\n```\n\n"
                      f"**P2 raw output**\n```json\n{r['p2_raw']}\n```" for r in recs[:3]),
        encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("valid_rate", "judge_rate", "kappa", "schema_fail_rate")}, indent=1))
    print("magnitude:", summary["magnitude"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
