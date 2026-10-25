"""Evaluate a frozen policy under an arbitrary set of injected constraints.

This is the factorial instrument for the theory: it separates **what the policy
learned** from **what the shield enforces**, on exactly the same weights and the
same held-out test episodes.

    python scripts/eval_shield.py --run results/campaign_1023/almond_seed0
    python scripts/eval_shield.py --run results/campaign_1023/almond_seed0 \
        --rule "min_advance:16@latitude_abs_deg>=68"
    python scripts/eval_shield.py --policy teacher --rule "min_advance:16@latitude_abs_deg>=68"
    python scripts/eval_shield.py --run .../ppomlp_seed0 --rule "min_advance:8@latitude_abs_deg>=68"

Rule syntax
-----------
``effect:magnitude@field op value[,field op value]...``
e.g. ``min_advance:16@latitude_abs_deg>=68`` or
``prefer_same_plane:0@latitude_abs_deg>=70``.

The evaluation protocol is copied from ``AlmondSystem._final_eval`` (same test
split, same batch, same traffic multipliers) so numbers are comparable with the
campaign tables; the only difference is which shield is installed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almond.framework.kg import Constraint  # noqa: E402
from almond.framework.shield import compile_constraints  # noqa: E402
from almond.policies.nets import GraphSpec, build_policy  # noqa: E402
from almond.policies.ppo import PPOConfig, PPOTrainer  # noqa: E402
from almond.twin.env import EnvConfig, HandoverEnv  # noqa: E402
from almond.twin.twin import DigitalTwin, TwinConfig  # noqa: E402

OPS = ("<=", ">=", "==", "!=", "<", ">")


def parse_rule(text: str) -> list[dict]:
    """``effect:mag@field op value,...`` -> list of atom dicts."""
    m = re.match(r"^\s*([a-z_]+)\s*:\s*(-?[\d.]+)\s*(?:@(.*))?$", text)
    if not m:
        raise SystemExit(f"cannot parse rule {text!r} (expected effect:magnitude@field op value)")
    effect, magnitude, atoms_txt = m.group(1), float(m.group(2)), m.group(3) or ""
    atoms = []
    for part in [a for a in atoms_txt.split(",") if a.strip()]:
        part = part.strip()
        for op in OPS:
            if op in part:
                field, value = part.split(op, 1)
                atoms.append({"field": field.strip(), "cmp": op, "value": float(value)})
                break
        else:
            raise SystemExit(f"cannot parse atom {part!r}")
    return [dict(effect=effect, magnitude=magnitude, atoms=atoms)]


def build_shield(rules: list[str]):
    if not rules:
        return None
    cons = []
    for i, r in enumerate(rules):
        for atom_spec in parse_rule(r):
            cons.append(
                Constraint(
                    id=f"inj{i}",
                    version=1,
                    atoms=atom_spec["atoms"],
                    effect=atom_spec["effect"],
                    magnitude=atom_spec["magnitude"],
                    nl_reading=f"injected: {r}",
                    provenance={},
                    confidence=1.0,
                    scope_tags={},
                )
            )
    return cons


def load_checkpoint(run_dir: Path):
    ck = __import__("torch").load(run_dir / "policy.pt", map_location="cpu", weights_only=False)
    return ck


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="campaign run directory holding policy.pt")
    ap.add_argument("--policy", default="ckpt", choices=("ckpt", "teacher", "random", "maxel", "maxvis", "staged"))
    ap.add_argument("--lead", type=float, default=6.0,
                    help="fixed preparation lead (s) for the maxel/maxvis operational baselines")
    # intent profile used for the satisfaction metric; defaults to the checkpoint's
    ap.add_argument("--w-rel", type=float, default=None)
    ap.add_argument("--w-lat", type=float, default=None)
    ap.add_argument("--w-pow", type=float, default=None)
    ap.add_argument("--dh-latency-ms-per-s", type=float, default=0.0,
                    help="dual-homing latency cost per second of lead (0 = legacy twin)")
    ap.add_argument("--dh-power-per-s", type=float, default=0.0)
    # twin-level physics (must match the campaign when evaluating its checkpoints)
    ap.add_argument("--no-seam", action="store_true")
    ap.add_argument("--feeder-slots", type=int, default=None)
    ap.add_argument("--isl-dropout", type=float, default=None)
    ap.add_argument("--constellation", default=None)
    ap.add_argument("--epoch-doy", type=float, default=None,
                    help="day-of-year of the twin epoch; shifts the orbital phase to build an "
                         "independent lockbox instance (default: the campaign epoch, 292.25)")
    ap.add_argument("--oracle-shield", action="store_true",
                    help="per-attempt oracle: clamp the polar lead to the realised acquisition "
                         "requirement (upper reference for any fixed threshold)")
    ap.add_argument("--rule", action="append", default=[], help="repeatable")
    ap.add_argument("--twin", default="ref")
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--traffic", type=float, default=None,
                    help="evaluate a single traffic multiplier (default: the 0.5/1/2 mix)")
    ap.add_argument("--acq-signaling", type=float, default=None,
                    help="override the acquisition signalling time, to evaluate under perturbed physics")
    ap.add_argument("--window", default="test",
                    choices=("train", "validation", "test"),
                    help="time window of the twin to evaluate on (test by default; "
                         "validation is the only window that any selection step may touch)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default=None)
    ap.add_argument("--dump-advance-dist", default=None,
                    help="write the polar handover-advance distribution to this JSON")
    ap.add_argument("--dump-attempts", default=None,
                    help="write the full attempt log (JSON) to this path, for narrative studies")
    args = ap.parse_args()

    # ---------------- twin + env (same config as the campaign) ----------------
    twin_kwargs = {}
    if args.no_seam:
        twin_kwargs["isl_seam_enabled"] = False
    if args.feeder_slots is not None:
        twin_kwargs["feeder_slots"] = args.feeder_slots
    if args.isl_dropout is not None:
        twin_kwargs["isl_dropout"] = args.isl_dropout
    if args.constellation is not None:
        twin_kwargs["constellation"] = args.constellation
    if args.epoch_doy is not None:
        twin_kwargs["epoch_doy"] = args.epoch_doy
    if args.oracle_shield and args.rule:
        raise SystemExit("--oracle-shield and --rule are mutually exclusive")
    twin = DigitalTwin(TwinConfig(tag=args.twin, horizon_s=args.hours * 3600, **twin_kwargs)).build(verbose=False)

    ck = load_checkpoint(Path(args.run)) if args.policy == "ckpt" else None
    weights = dict((ck or {}).get("weights") or dict(w_rel=1 / 3, w_lat=1 / 3, w_pow=1 / 3))
    # an explicit intent profile lets a heuristic be scored against ALMOND's weights
    if args.w_rel is not None:
        weights["w_rel"] = args.w_rel
    if args.w_lat is not None:
        weights["w_lat"] = args.w_lat
    if args.w_pow is not None:
        weights["w_pow"] = args.w_pow
    variant = (ck or {}).get("variant", "full")
    env_cfg = EnvConfig(
        episode_steps=args.steps,
        w_rel=weights["w_rel"], w_lat=weights["w_lat"], w_pow=weights["w_pow"],
        use_snr_proxy=(variant == "handcrafted"),
        drop_penalty=0.0 if variant == "handcrafted" else 0.30,
        switch_penalty=0.10,
        **({"acq_signaling_s": args.acq_signaling} if args.acq_signaling is not None else {}),
        **({"oracle_min_advance": True} if args.oracle_shield else {}),
        **({"dual_homing_latency_ms_per_s": args.dh_latency_ms_per_s} if args.dh_latency_ms_per_s else {}),
        **({"dual_homing_power_per_s": args.dh_power_per_s} if args.dh_power_per_s else {}),
    )
    env = HandoverEnv(twin, env_cfg, batch=args.batch, seed=args.seed + 4242)
    x0, adj0 = env.candidate_graph()

    trainer = None
    if args.policy == "ckpt":
        spec = GraphSpec.from_dict(ck["spec"])
        policy = build_policy("graph", obs_dim=env.obs_dim, node_dim=x0.shape[-1],
                              n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
        policy.load_state_dict(ck["policy"])
        pcfg = PPOConfig(device="cpu", seed=args.seed, deterministic=True)
        trainer = PPOTrainer(env, policy, pcfg)
        if trainer.obs_norm is not None and ck.get("obs_norm"):
            trainer.obs_norm.load_state_dict(ck["obs_norm"])

    shield = compile_constraints(build_shield(args.rule) or [], env.cfg) if args.rule else None
    fixed_bucket = int(np.clip(round((args.lead - env.cfg.a_min_s) / env.cfg.a_step_s), 0, env.cfg.a_max_bucket))

    def heuristic(key: str, staged: bool = False) -> tuple[np.ndarray, np.ndarray]:
        """Operational handover rules used as external baselines.

        ``maxel``  - hand over to the highest-elevation routed candidate
        ``maxvis`` - hand over to the candidate that stays visible longest
        ``staged`` - max elevation with a *regime-dependent* lead: 18 s above 68°,
        12 s in the mid-latitudes, 8 s near the equator.  This is what a
        per-regime calibration (or a context-dependent policy) can do and a single
        global constant cannot.
        """
        si, t = env.site, env.t_idx
        cand = env.cand_idx[si, t]
        valid = cand >= 0
        cc = np.maximum(cand, 0)
        el = env.el[si[:, None], cc, t[:, None]]
        trem = env.trem[si[:, None], cc, t[:, None]]
        hop = env.hop[cc, t[:, None]]
        score = el if key != "maxvis" else trem
        score = np.where(valid & (hop >= 0), score, -1e9)
        j = score.argmax(axis=1)
        ta = np.where(score.max(axis=1) > -1e8, j + 1, 0)
        if staged:
            lat = np.abs(env.site_lat[si])
            lead = np.where(lat >= 68.0, 18.0, np.where(lat >= 15.0, 12.0, 8.0))
            aa = np.clip(np.round((lead - env.cfg.a_min_s) / env.cfg.a_step_s), 0, env.cfg.a_max_bucket)
            return ta.astype(np.int64), aa.astype(np.int64)
        return ta.astype(np.int64), np.full(env.batch, fixed_bucket, dtype=np.int64)

    def act(obs, x, adj):
        if args.policy == "teacher":
            return env.teacher_action()
        if args.policy == "random":
            ta = np.random.randint(0, env.K + 1, size=env.batch)
            aa = np.random.randint(0, env.n_advance, size=env.batch)
            return ta, aa
        if args.policy in ("maxel", "maxvis"):
            return heuristic(args.policy)
        if args.policy == "staged":
            return heuristic("maxel", staged=True)
        at, aa, _lp, _v = trainer._act(obs, x, adj, deterministic=True)
        return at, aa

    # ---------------- evaluation: identical splits to _final_eval ----------------
    from almond.framework.forensics import SplitConfig

    splits = SplitConfig()
    test_idx = splits.indices(twin.n_time, args.window, args.steps)
    rows, attempts = [], []
    mults = (1.0, 0.5, 2.0) if args.traffic is None else (args.traffic,)
    for mult in mults:
        env.cfg.traffic_scale = mult
        env.reset(t_range=test_idx)
        for _ in range(env.cfg.episode_steps):
            x, adj = env.candidate_graph()
            at, aa = act(env.obs(), x, adj)
            env.step(at, aa, shield=shield, record=True)
        st = env.episode_stats()
        lat = env.site_lat[env.site]
        for i in range(env.batch):
            rows.append(dict(lat=float(lat[i]), attempts=int(st["attempts"][i]),
                             successes=int(st["successes"][i]),
                             hsr=float(st["hsr"][i]),
                             lat_p95=float(st["lat_p95"][i]) if not np.isnan(st["lat_p95"][i]) else float("nan"),
                             lat_mean=float(st["lat_mean"][i]) if not np.isnan(st["lat_mean"][i]) else float("nan"),
                             power_mean=float(np.nanmean([p[i] for p in env.pow_hist])) if env.pow_hist else 0.5))
        attempts.extend(env.attempt_log)
    env.cfg.traffic_scale = 1.0

    if args.dump_attempts:
        Path(args.dump_attempts).parent.mkdir(parents=True, exist_ok=True)
        Path(args.dump_attempts).write_text(
            json.dumps(attempts, default=float), encoding="utf-8")
        print(f"wrote {len(attempts)} attempts to {args.dump_attempts}")

    if args.dump_advance_dist:
        polar = [a for a in attempts if abs(a["latitude_abs_deg"]) >= 70.0]
        json.dump(dict(n=len(polar),
                       advances=[a["handover_advance_s"] for a in polar],
                       late=[1 if a.get("cause") == "late_handover" else 0 for a in polar]),
                  open(args.dump_advance_dist, "w", encoding="utf-8"))

    from almond.analysis.metrics import satisfaction

    def region(lo, hi, neg=False):
        sel = [r for r in rows if (abs(r["lat"]) >= lo and abs(r["lat"]) < hi)]
        att = sum(r["attempts"] for r in sel)
        suc = sum(r["successes"] for r in sel)
        return (suc / att if att else float("nan")), att, sel

    arc_hsr, arc_att, arc_rows = region(70, 90)
    mid_hsr, mid_att, mid_rows = region(30, 70)
    equ_hsr, equ_att, equ_rows = region(0, 15)
    out = dict(
        label=args.label or (Path(args.run).name if args.run else args.policy),
        policy=args.policy,
        rules=args.rule,
        arctic=(arc_hsr, arc_att),
        midlat=(mid_hsr, mid_att),
        equatorial=(equ_hsr, equ_att),
        overall=(sum(r["successes"] for r in rows) / max(1, sum(r["attempts"] for r in rows)),
                 sum(r["attempts"] for r in rows)),
        n_attempts=len(attempts),
        satisfaction=satisfaction(rows, weights),
        satisfaction_arctic=satisfaction(arc_rows, weights),
        satisfaction_midlat=satisfaction(mid_rows, weights),
        satisfaction_equatorial=satisfaction(equ_rows, weights),
    )

    # diagnostics on the attempts themselves
    ad = np.array([a["handover_advance_s"] for a in attempts], dtype=float)
    polar = [a for a in attempts if abs(a["latitude_abs_deg"]) >= 70]
    pad = np.array([a["handover_advance_s"] for a in polar], dtype=float)
    causes = {}
    for a in polar:
        causes[a["cause"]] = causes.get(a["cause"], 0) + 1
    out["polar_causes"] = {k: v / max(1, len(polar)) for k, v in causes.items()}
    out["polar_advance_mean"] = float(pad.mean()) if pad.size else float("nan")
    out["polar_share_ge12"] = float((pad >= 12).mean()) if pad.size else float("nan")
    out["polar_share_ge16"] = float((pad >= 16).mean()) if pad.size else float("nan")

    print(f"{out['label']:<34} arctic {100 * out['arctic'][0]:5.1f}%  "
          f"mid {100 * out['midlat'][0]:5.1f}%  equat {100 * out['equatorial'][0]:5.1f}%  "
          f"overall {100 * out['overall'][0]:5.1f}%  "
          f"S {out['satisfaction']:5.1f}  "
          f"adv(polar) {out['polar_advance_mean']:4.1f}s  "
          f"late {100 * out['polar_causes'].get('late_handover', 0):5.1f}%  "
          f"win {100 * out['polar_causes'].get('window_exceeded', 0):5.1f}%")

    if args.out:
        prev = []
        p = Path(args.out)
        if p.exists():
            prev = json.loads(p.read_text(encoding="utf-8"))
        prev.append(out)
        p.write_text(json.dumps(prev, indent=2, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
