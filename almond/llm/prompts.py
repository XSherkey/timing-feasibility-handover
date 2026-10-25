"""Prompt templates (Appendix A of the manuscript).

The templates are faithful to the appendix: few-shot, JSON-only output,
structure-only for topology calls, and a constrained predicate grammar for
forensic hypotheses.  ``render_prompt`` returns the ``system``/``user`` pair
that is sent to a real backend; the surrogate backend consumes only the
structured ``payload`` but the prompt is still rendered and logged so that the
call log is complete and auditable.
"""
from __future__ import annotations

import json


def _j(o) -> str:
    return json.dumps(o, default=str)

SYSTEM = {
    "forward_translate": (
        "You are an expert in LEO satellite network operations, reinforcement learning (RL), "
        "and reward function design. You translate operator intent into a weight profile over "
        "FIXED, normalized sub-rewards. You never invent new metrics, thresholds, or telemetry "
        "fields. You answer with JSON only."
    ),
    "forensic_hypothesis": (
        "You are a satellite-network operations analyst. You read temporal narratives of failed "
        "handover episodes and propose the single most plausible latent operational rule, expressed "
        "in a constrained predicate grammar. Rules must reference only declared telemetry fields, "
        "must be physically plausible under SGP4-propagated geometry, and must be falsifiable by "
        "counterfactual replay. You answer with JSON only."
    ),
    "topology_seed": (
        "You are a neural-architecture designer for resource-constrained satellite payloads. Given a "
        "regime description and the graph grammar, you propose one valid topology sketch. You output "
        "structure only, never weights. You answer with JSON only."
    ),
    "topology_mutation": (
        "You are a neural-architecture designer. Given a valid topology sketch and fitness feedback, "
        "you apply the minimal grammar-preserving edit that addresses the feedback. Structure only, "
        "never weights. JSON only."
    ),
    "topology_crossover": (
        "You are a neural-architecture designer. Given two valid parent sketches, you align their "
        "homologous subgraphs and propose a child by swapping the non-homologous parts. The child "
        "must satisfy the grammar. Structure only. JSON only."
    ),
    "population_critique": (
        "You are an evolutionary-search supervisor. Given summaries of the top-5 elite individuals "
        "(node types, depth, edge density, fitness only) you suggest operator-probability "
        "adjustments within the allowed bounds. JSON only."
    ),
}

FORWARD_USER = """The RL task is: <task_short_desc>.
The environment description (without objectives) is provided below.

<Env_desc_wo_obj>

## Objectives
The operator intent is given as a Python dict of named requirements:
<objectives>

## FIXED normalized sub-rewards (do not modify)
  R_rel = n_rel = (HSR - 50)/(100 - 50)
  R_lat = n_lat = (L_max - L)/(L_max - L_min), L_max = 150 ms, L_min = 20 ms
  R_pow = n_pow = 1 - (P - P_idle)/(P_max - P_idle)

## Output guide and format
For each requirement, in order: (a) analyze how to fulfill it; (b) identify the telemetry
variables that support it; (c) state which fixed sub-reward carries it. Then output
1. a weight profile {{w_rel, w_lat, w_pow}} with w_i in [0,1] and sum 1, matching the stated
   priorities ({priority_hint});
2. a mapping from each requirement to one of R_rel, R_lat, R_pow.
Do not invent new metrics, thresholds, or telemetry fields. Output JSON only:
{{"analysis": [...], "weights": {{"w_rel": 0.0, "w_lat": 0.0, "w_pow": 0.0}},
 "mapping": {{...}}, "open_questions": [...]}}

### Examples
{examples}
"""

EXAMPLE_FORWARD = [
    {
        "objectives": {"reliability": "critical", "latency": "low", "power": "low"},
        "answer": {
            "analysis": [
                "reliability is declared critical, so R_rel must dominate the profile",
                "latency is only 'low'; it should not trade away session continuity",
                "power is secondary in this regime",
            ],
            "weights": {"w_rel": 0.8, "w_lat": 0.12, "w_pow": 0.08},
            "mapping": {"reliability": "R_rel", "latency": "R_lat", "power": "R_pow"},
            "open_questions": [],
        },
    },
    {
        "objectives": {"reliability": "high", "latency": "critical", "power": "medium"},
        "answer": {
            "analysis": [
                "latency is critical, but reliability still bounds the tail",
                "a balanced reliability/latency profile is appropriate",
            ],
            "weights": {"w_rel": 0.45, "w_lat": 0.4, "w_pow": 0.15},
            "mapping": {"reliability": "R_rel", "latency": "R_lat", "power": "R_pow"},
            "open_questions": [],
        },
    },
    {
        "objectives": {"reliability": "medium", "latency": "medium", "power": "critical"},
        "answer": {
            "analysis": [
                "power is critical, e.g. an eclipse-season battery constraint",
                "reliability must remain above the service floor",
            ],
            "weights": {"w_rel": 0.4, "w_lat": 0.15, "w_pow": 0.45},
            "mapping": {"reliability": "R_rel", "latency": "R_lat", "power": "R_pow"},
            "open_questions": [],
        },
    },
]

FORENSIC_USER = """The policy <policy_id> underperforms in region <region_tags>:
KPI <kpi> = <value> against threshold <theta>.

Below are the worst 5% failure episodes encoded as temporal narratives.

<episodes>

Telemetry field schema (only these may appear in a rule):
<field_schema>

Effect grammar (only these effects are executable):
<effect_grammar>

Each narrative may report a gateway error code. Choose the effect whose "remedy" matches that
code, and use the telemetry values in the narratives to pick the threshold: late_handover ->
min_advance, no_route -> forbid_unrouted_target, window_exceeded -> prefer_long_visibility, congestion ->
buffer_drain, cross-plane fragility -> prefer_same_plane.

Propose at most three rules. Rules must be a conjunction of at most two atoms of the form
<telemetry_field> <cmp> <value>, plus one effect from the grammar. Output JSON only:
{{"hypotheses": [{{"if": {{"all": [{{"field": "...", "cmp": ">=", "value": 0}}]}},
                  "then": {{"effect": "...", "magnitude": 0}}, "rationale": "..."}}],
 "alternative_explanations": ["..."]}}
"""

TOPOLOGY_SEED_USER = """Task: <task>

Regime tags: <regime_tags>
Regime hint: <regime_hint>
Measured regime statistics (computed from the digital twin, polar sites):
<regime_stats>

Graph grammar: node types IN, MLP_k (k in 64/128/256), GCN_k (32/64), ATT_<h,d> (h in 1/2/4/8,
d in 32/64/128), POOL, OUT; edges feed-forward/residual/skip; at most 24 nodes, depth at most 8,
width at most 256, parameter budget <= 50K. Two optional structural switches were recently added:
  "head_width": 0 or 32..256 - hidden width of the decision trunk/heads (0 = same as width), so the
      graph trunk and the decision head can differ in capacity;
  "edge_types": 0 or 1 - 1 uses separate weights for serving-anchor edges and candidate-candidate
      edges instead of one weight matrix for all edges.
Design brief for this proposal: <design_brief>

Already evaluated in this search (kind, width, layers, params, satisfaction, arctic HSR, diagnosis):
<history>

Propose one valid topology sketch that fits this brief and is NOT a duplicate of the table above.
Explain in "rationale" which measured statistic or diagnosis motivates it. JSON only:
{{"kind": "gcn|att|hybrid|mlp", "width": 64, "layers": 2, "heads": 2, "pool": "mean|max",
  "ctx_width": 64, "ctx_layers": 1, "head_width": 0, "edge_types": 0, "rationale": "..."}}
"""

TOPOLOGY_MUTATION_USER = """Current sketch: <sketch>
Measured outcome of this sketch: <feedback>
Recent evaluations in this search (so you do not repeat a failed direction):
<recent_results>
Allowed edits: change kind, double/halve width, add/remove one layer, add/remove attention heads,
switch pooling, deepen/shallow the context encoder, set head_width (0 or 32..256), set edge_types
(0 or 1). Apply exactly one minimal edit, chosen to address the diagnosis in "feedback" (for
example: never_hands_over -> widen the decision trunk via head_width; advance head stuck at the
minimum bucket -> add capacity rather than depth; high share of un-routed candidates -> edge_types=1
so the serving anchor can be weighted differently). JSON only:
{{"kind": "...", "width": 64, "layers": 2, "heads": 2, "pool": "...", "ctx_width": 64,
  "ctx_layers": 1, "head_width": 0, "edge_types": 0, "rationale": "..."}}
"""

TOPOLOGY_CROSSOVER_USER = """Parent A: <sketch_a>
Parent B: <sketch_b>
Align homologous subgraphs and swap the non-homologous parts; the child must satisfy the grammar
and must combine the strengths rather than copy one parent. JSON only:
{{"kind": "...", "width": 64, "layers": 2, "heads": 2, "pool": "...", "ctx_width": 64,
 "ctx_layers": 1, "head_width": 0, "edge_types": 0, "rationale": "..."}}
"""

CRITIQUE_USER = """Best satisfaction so far: <best_so_far> after <evaluated> evaluations.
Measured regime statistics: <regime_stats>
Elite summaries (spec, score, diagnosis): <elites>
Current operator probabilities: <probs>
Recent evaluations: <recent_results>
Diagnose why the search is stalling (e.g. all elites share one failure mode, or the population has
collapsed onto one family) and suggest operator adjustments within the allowed bounds. JSON only:
{{"mutation_rate": 0.3, "crossover_rate": 0.4, "width_bias": 0.0, "depth_bias": 0.0,
  "rationale": "..."}}
"""


def render_prompt(call_type: str, payload: dict) -> dict:
    """Render the prompt pair for a call type."""
    system = SYSTEM[call_type]
    if call_type == "forward_translate":
        intent = payload.get("intent", {})
        prio = intent.get("priorities", {})
        hint = ", ".join(f"{k}: {v}" for k, v in prio.items()) or "state the priorities explicitly"
        examples = "\n".join(
            f"### Example {i + 1}\nobjectives = {json.dumps(e['objectives'])}\nanswer = "
            f"{json.dumps(e['answer'])}"
            for i, e in enumerate(EXAMPLE_FORWARD)
        )
        user = (
            FORWARD_USER.replace("<task_short_desc>", payload.get("task_short_desc", "LEO handover control"))
            .replace("<Env_desc_wo_obj>", payload.get("env_desc", "")[:6000])
            .replace("<objectives>", _j(intent)[:3000])
            .replace("{priority_hint}", hint)
            .replace("{examples}", examples)
        )
    elif call_type == "forensic_hypothesis":
        episodes = payload.get("failure_narratives", [])
        user = (
            FORENSIC_USER.replace("<policy_id>", str(payload.get("policy_id", "pi_0")))
            .replace("<region_tags>", _j(payload.get("region_tags", {})))
            .replace("<kpi>", str(payload.get("kpi", "hsr")))
            .replace("<value>", f"{payload.get('kpi_value', float('nan')):.3f}")
            .replace("<theta>", f"{payload.get('threshold', 0.85):.3f}")
            .replace("<episodes>", "\n".join(episodes)[:8000])
            .replace("<field_schema>", _j(payload.get("field_schema", []))[:3000])
            .replace("<effect_grammar>", _j(payload.get("effect_grammar", []))[:2000])
        )
    elif call_type == "topology_seed":
        user = (
            TOPOLOGY_SEED_USER.replace("<task>", _j(payload.get("task", {}))[:1800])
            .replace("<regime_tags>", _j(payload.get("regime_tags", {})))
            .replace("<regime_hint>", str(payload.get("regime_hint", "balanced")))
            .replace("<regime_stats>", _j(payload.get("regime_stats", {}))[:1200])
            .replace("<design_brief>", str(payload.get("design_brief", "balanced design")))
            .replace("<history>", _j(payload.get("history", []))[:4000])
        )
    elif call_type == "topology_mutation":
        user = (
            TOPOLOGY_MUTATION_USER.replace("<sketch>", _j(payload.get("sketch", {})))
            .replace("<feedback>", _j(payload.get("fitness_feedback", {}))[:2500])
            .replace("<recent_results>", _j(payload.get("fitness_feedback", {}).get("recent_results", []))[:2500])
        )
    elif call_type == "topology_crossover":
        user = TOPOLOGY_CROSSOVER_USER.replace(
            "<sketch_a>", _j(payload.get("sketch_a", {}))
        ).replace("<sketch_b>", _j(payload.get("sketch_b", {})))
    elif call_type == "population_critique":
        user = (
            CRITIQUE_USER.replace("<elites>", _j(payload.get("elites", []))[:4000])
            .replace("<probs>", _j(payload.get("probs", {})))
            .replace("<best_so_far>", f"{payload.get('best_so_far', 0.0):.1f}")
            .replace("<evaluated>", str(payload.get("evaluated", 0)))
            .replace("<regime_stats>", _j(payload.get("regime_stats", {}))[:1000])
            .replace("<recent_results>", _j(payload.get("recent_results", []))[:3000])
        )
    else:  # pragma: no cover - defensive
        raise ValueError(f"unknown call type {call_type}")
    # the templates are plain strings (not f-strings), so the JSON examples carry
    # doubled braces; a real model should see ordinary JSON braces
    user = user.replace("{{", "{").replace("}}", "}")
    return dict(system=system, user=user)
