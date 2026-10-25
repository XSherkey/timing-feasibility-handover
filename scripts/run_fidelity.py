"""Digital-twin fidelity and sim-to-real sensitivity (manuscript Sec. 4.8).

Three measurements:

1. **Analytic agreement.**  The twin's slant range and received SNR are compared
   with the closed-form spherical-Earth link budget
   ``d = sqrt((Re+h)^2 - (Re cos e)^2) - Re sin e`` for the polar shell; the
   disagreement is reported in dB.
2. **Perturbation sensitivity.**  Atmospheric attenuation, traffic load and ISL
   availability are perturbed independently by +-10 % and the mined constraints
   are re-validated: how many of them still replicate (delta >= 5 %)?
3. **Sim-to-real proxy.**  A policy trained on the reference twin is evaluated
   on each perturbed twin without retraining; the HSR drop is the proxy for the
   sim-to-real gap.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.framework.forensics import replay_rule, score
from almond.framework.kg import Constraint, KnowledgeGraph
from almond.policies.nets import GraphSpec, build_policy
from almond.policies.ppo import PPOTrainer
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig

R_EARTH = 6378.137


def analytic_range_km(el_deg, alt_km):
    e = np.deg2rad(el_deg)
    return np.sqrt((R_EARTH + alt_km) ** 2 - (R_EARTH * np.cos(e)) ** 2) - R_EARTH * np.sin(e)


def link_budget_agreement(twin) -> dict:
    si = twin.user_site_index[0]
    el = np.asarray(twin["el"][si], dtype=np.float32)
    rng = np.asarray(twin["rng"][si], dtype=np.float32)
    snr = np.asarray(twin["snr"][si], dtype=np.float32)
    pos = np.asarray(twin["pos"], dtype=np.float32)
    alt = np.linalg.norm(pos, axis=-1).mean() - R_EARTH
    m = (el > 5.0) & (el < 80.0)
    d_num = rng[m].astype(np.float64)
    d_ana = analytic_range_km(el[m].astype(np.float64), alt)
    ratio = d_num / np.maximum(d_ana, 1.0)
    err_db = 20.0 * np.log10(np.maximum(ratio, 1e-6))
    # independent SNR recomputation from the analytic range
    f_ghz = 20.0
    fspl = 92.45 + 20 * np.log10(d_ana) + 20 * np.log10(f_ghz)
    atm = 0.4 * (1.0 / np.maximum(np.sin(np.deg2rad(el[m].astype(np.float64))), 0.087))
    cn0 = 50.0 - fspl - atm - 1.0 + 5.0 + 228.6
    snr_ana = cn0 - 10 * np.log10(250e6)
    ds = np.abs(np.asarray(snr[m], dtype=np.float64) - snr_ana)
    return dict(
        n_samples=int(m.sum()),
        altitude_km=float(alt),
        range_rel_error_median=float(np.median(np.abs(ratio - 1.0))),
        range_error_db_p50=float(np.percentile(np.abs(err_db), 50)),
        range_error_db_p95=float(np.percentile(np.abs(err_db), 95)),
        range_error_db_max=float(np.abs(err_db).max()),
        snr_error_db_p50=float(np.percentile(ds, 50)),
        snr_error_db_p95=float(np.percentile(ds, 95)),
        snr_error_db_max=float(ds.max()),
    )


class PerturbedEnv(HandoverEnv):
    """Environment with in-RAM physical perturbations (no cache rebuild)."""

    def __init__(self, twin, cfg, batch, seed, snr_shift_db=0.0, hop_penalty=0.0,
                 isl_dropout=0.0, traffic=1.0, rng_seed=0):
        super().__init__(twin, cfg, batch=batch, seed=seed)
        rr = np.random.default_rng(rng_seed)
        if snr_shift_db:
            self.snr = np.asarray(twin["snr"], dtype=np.float32) + np.float32(snr_shift_db)
        if hop_penalty or isl_dropout:
            hop = np.asarray(twin["hop"], dtype=np.int16)
            if hop_penalty:
                hop = np.where(hop >= 0, hop + int(round(hop_penalty)), hop).astype(np.int16)
            if isl_dropout:
                mask = rr.random(hop.shape) < isl_dropout
                hop = np.where(mask & (hop >= 0), -1, hop).astype(np.int16)
            self.hop = hop
        self.cfg.traffic_scale = traffic


def load_policy(env, path):
    import torch

    blob = torch.load(path, map_location="cpu", weights_only=False)
    spec = GraphSpec.from_dict(blob["spec"])
    x, adj = env.candidate_graph()
    pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                       n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
    pol.load_state_dict(blob["policy"])
    pol.eval()
    return pol, blob


def make_policy_fn(pol, obs_norm=None):
    import torch

    def fn(obs, x, adj, deterministic=True):
        o = obs_norm(obs) if obs_norm is not None else obs
        with torch.no_grad():
            lt, la, _ = pol(torch.as_tensor(o), torch.as_tensor(x), torch.as_tensor(adj))
        cand = None
        return lt.argmax(-1).numpy(), la.argmax(-1).numpy()

    return fn


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="results/campaign/almond_seed0/policy.pt")
    ap.add_argument("--kg", default="results/campaign/almond_seed0/knowledge_graph.json")
    ap.add_argument("--out", default="results/fidelity.json")
    ap.add_argument("--episodes", type=int, default=2)
    args = ap.parse_args()

    twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=12 * 3600)).build(verbose=False)
    out: dict = dict(link_budget=link_budget_agreement(twin))

    base_env = HandoverEnv(twin, EnvConfig(episode_steps=240), batch=24, seed=3)
    pol = None
    try:
        pol, _blob = load_policy(base_env, args.policy)
    except FileNotFoundError:
        print(f"[fidelity] no policy at {args.policy}; skipping policy transfer")
    pf = make_policy_fn(pol) if pol is not None else None

    constraints = []
    kg_path = Path(args.kg)
    if kg_path.exists():
        kg = KnowledgeGraph(kg_path)
        constraints = kg.active()
    print(f"[fidelity] {len(constraints)} active constraints")

    pertrb = {
        "atm_minus10": dict(snr_shift_db=-0.23),
        "atm_plus10": dict(snr_shift_db=+0.23),
        "traffic_minus10": dict(traffic=0.9),
        "traffic_plus10": dict(traffic=1.1),
        "isl_minus10": dict(isl_dropout=0.10, hop_penalty=0.0),
        "combined": dict(snr_shift_db=-0.23, traffic=1.1, isl_dropout=0.05),
    }

    # baseline on the reference twin
    base_rows, _ = (replay_rule(base_env, pf, None, args.episodes, (3000, 3400))["rows"], None) if pf else ([], None)
    base_score = score(base_rows, "arctic") if base_rows else dict(hsr=float("nan"))

    results = {}
    for name, kw in pertrb.items():
        env = PerturbedEnv(twin, EnvConfig(episode_steps=240), 24, seed=3, **kw)
        # (a) does the mined rule still replicate?
        rep = []
        for c in constraints:
            base = replay_rule(env, pf, None, args.episodes, (3000, 3400)) if pf else dict(rows=[])
            withc = replay_rule(env, pf, c, args.episodes, (3000, 3400)) if pf else dict(rows=[])
            d = score(withc["rows"], "arctic")["hsr"] - score(base["rows"], "arctic")["hsr"]
            rep.append(dict(id=c.id, effect=c.effect, delta=float(d), replicated=bool(d >= 0.05)))
        # (b) policy transfer without retraining
        trans = None
        if pf is not None:
            rows = replay_rule(env, pf, None, args.episodes, (3000, 3400))["rows"]
            trans = dict(hsr_arctic=score(rows, "arctic")["hsr"], hsr_all=score(rows, "all")["hsr"])
        results[name] = dict(
            perturbation=kw,
            rules_replicated=sum(r["replicated"] for r in rep),
            rules_tested=len(rep),
            replication_details=rep,
            transfer=trans,
        )
    out["perturbations"] = results
    n_rep = sum(v["rules_replicated"] for v in results.values())
    n_tot = sum(v["rules_tested"] for v in results.values())
    out["summary"] = dict(
        rules_replicated=n_rep,
        rules_tested=n_tot,
        replication_rate=n_rep / n_tot if n_tot else float("nan"),
        base_arctic_hsr=base_score["hsr"],
    )
    Path(args.out).write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")

    lb = out["link_budget"]
    print(f"link budget: {lb['n_samples']} samples, altitude {lb['altitude_km']:.0f} km")
    print(f"  range error p50 {lb['range_error_db_p50']:.4f} dB, p95 {lb['range_error_db_p95']:.4f} dB, "
          f"max {lb['range_error_db_max']:.4f} dB")
    print(f"  SNR recomputation error p50 {lb['snr_error_db_p50']:.3f} dB, "
          f"p95 {lb['snr_error_db_p95']:.3f} dB")
    print(f"rule replication: {n_rep}/{n_tot} ({out['summary']['replication_rate'] * 100:.1f}%)")
    for name, v in results.items():
        t = v["transfer"]
        print(f"  {name:<16} replicated {v['rules_replicated']}/{v['rules_tested']}"
              + (f"  arctic HSR {t['hsr_arctic'] * 100:.1f}% (base {base_score['hsr'] * 100:.1f}%)" if t else ""))
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
