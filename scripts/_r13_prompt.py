"""R14 part 5: make both Appendix E blocks reproduce the actual system+user prompt verbatim."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

PROMPT = """SYSTEM (P1)
You are a satellite-network operations analyst. You read temporal narratives of failed handover
episodes and propose the single most plausible latent operational rule, expressed in a constrained
predicate grammar. Rules must reference only declared telemetry fields, must be physically plausible
under SGP4-propagated geometry, and must be falsifiable by counterfactual replay. You answer with
JSON only.

SYSTEM (P2) - identical, except the last sentence is replaced by
You also state the magnitude the rule should enforce, in seconds, with one sentence of
justification. You answer with JSON only.

USER
OPERATOR INTENT: {intent}

DECLARED TELEMETRY FIELDS (rule predicates may use only these):
elevation_deg, handover_advance_s, isl_hop_count, doppler_rate_hz_s, latitude_abs_deg,
snr_db, remaining_visibility_s, plane_change, path_available, buffer_occupancy, battery_state,
eclipse, satellite_latitude_deg

EXECUTABLE EFFECTS:
min_advance, cap_advance, power_cap, prefer_same_plane, prefer_long_visibility,
forbid_unrouted_target, buffer_drain

PAST FAILURE NARRATIVES (training window only):
{narratives}

Return JSON with exactly these keys:
  effect      : one of the effects above
  atoms       : list of {"field": ..., "cmp": one of "lt","le","gt","ge","eq","ne",
               "value": number}   # illustrative, not literal JSON: the operator names are
                                 # spelled out so the schema survives copy-paste.
  magnitude   : number (seconds for lead-time effects)"""

for name, head, tail_note in (
    ("paper_en.md", "## Appendix E. Prompt and raw outputs",
     "The block below is the prompt that actually ran, verbatim, with the two substitution points marked."),
    ("paper_zh.md", "## 附录 E. Prompt、schema 与原始输出",
     "下面这一块是实际运行所用的 prompt（原文），两个替换点已标出。"),
):
    p = D / name
    t = p.read_text(encoding="utf-8")
    i = t.find(head)
    if i < 0:
        raise SystemExit(f"{name}: appendix E head not found")
    # replace the first fenced block after the head with the true prompt
    j = t.find("```", i)
    k = t.find("```", j + 3)
    if j < 0 or k < 0:
        raise SystemExit(f"{name}: no fenced block")
    t = t[:j] + "```\n" + PROMPT + "\n```" + t[k + 3:]
    p.write_text(t, encoding="utf-8")
    print(name, "prompt block replaced")
