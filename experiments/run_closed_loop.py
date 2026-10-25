"""C2 (streamlined): the closed loop - detect, probe, admit or roll back - with no regime label.

One continuous run over the test window, split into 16 chunks of 15 decision epochs.  At chunk 7 the
acquisition signalling time is perturbed by +2 s and nothing tells the system.  A CUSUM on the polar
late-handover share raises the alarm; on alarm the system spends a *bounded probe budget in service*
(a quarter of the next chunk's polar attempts are forced onto spread-out advances), reads the crossing,
and the audit gate replays the last two chunks to decide commit or rollback.

Reference points: fixed 18 s, an EWMA-quantile online baseline, an oracle told the regime, and the loop.

Run:  python experiments/run_closed_loop.py
Out:  results/routeA_r3/closed_loop/summary.json
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from r3lib import OUT, write  # noqa: E402

from almond.twin.env import EnvConfig, HandoverEnv  # noqa: E402
from almond.twin.twin import DigitalTwin, TwinConfig  # noqa: E402
from almond.policies.nets import GraphSpec, build_policy  # noqa: E402

CHUNKS, CHUNK_STEPS = 16, 15
DRIFT_CHUNK, DRIFT = 7, 2.0
GRID = np.arange(6.0, 26.5, 2.0)


def shield_for(mag: float, rng=None, probe_share: float = 0.0):
    """Raise the polar lead to ``mag``; optionally force a share of polar attempts onto the grid."""

    def apply(env, target_action, advance_action):
        si, t = env.site, env.t_idx
        srv = np.maximum(env.serving, 0)
        polar = np.abs(env.site_lat[si]) >= 68.0
        need = int(round((mag - env.cfg.a_min_s) / env.cfg.a_step_s))
        need = int(np.clip(need, 0, env.cfg.a_max_bucket))
        aa = np.where(polar, np.maximum(advance_action, need), advance_action)
        if probe_share > 0 and rng is not None:
            B = env.batch
            pick = (rng.random(B) < probe_share) & polar
            if np.any(pick):
                vals = rng.choice(GRID, size=int(pick.sum()))
                buckets = np.rint(np.clip((vals - env.cfg.a_min_s) / env.cfg.a_step_s,
                                          0, env.cfg.a_max_bucket)).astype(np.int64)
                aa = aa.copy()
                aa[pick] = buckets
        return target_action, aa

    return apply


def chunk_stats(new):
    pol = [a for a in new if abs(a["latitude_abs_deg"]) >= 70.0]
    if not pol:
        return float("nan"), float("nan"), 0
    ok = sum(1 for a in pol if a["success"])
    late = sum(1 for a in pol if a["cause"] == "late_handover")
    return 100.0 * ok / len(pol), 100.0 * late / len(pol), len(pol)


def crossing(attempts):
    """Smallest grid lead whose realised requirement is met for >=95% of polar attempts."""
    pol = [a for a in attempts if abs(a["latitude_abs_deg"]) >= 70.0]
    if len(pol) < 25:
        return None
    req = np.array([a["t_setup_s"] for a in pol])
    for g in GRID:
        if (req <= g).mean() >= 0.95:
            return float(g)
    return None


def replay(attempts, mag):
    """Counterfactual HSR of a threshold ``mag`` on logged attempts (route and visibility respected)."""
    pol = [a for a in attempts if abs(a["latitude_abs_deg"]) >= 70.0]
    if not pol:
        return float("nan")
    ok = 0
    for a in pol:
        if a["cause"] == "no_route":
            continue
        adv = max(a["handover_advance_s"], mag)
        ok += 1 if (a["t_setup_s"] <= adv <= a["remaining_visibility_s"]) else 0
    return 100.0 * ok / len(pol)


def run(mode: str = "loop", policy_seed: int = 0, traffic: int = 0) -> dict:
    twin = DigitalTwin(TwinConfig()).build(verbose=False)
    cfg = EnvConfig(episode_steps=CHUNKS * CHUNK_STEPS)
    env = HandoverEnv(twin, cfg, batch=32, seed=traffic + 4242)
    ck = __import__("torch").load(ROOT / "results" / "campaign_1023" / f"almond_seed{policy_seed}" / "policy.pt",
                                 map_location="cpu", weights_only=False)
    x0, adj0 = env.candidate_graph()
    pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x0.shape[-1],
                       n_targets=env.K + 1, n_advance=env.n_advance,
                       spec=GraphSpec.from_dict(ck["spec"]))
    pol.load_state_dict(ck["policy"])
    pol.eval()
    from almond.policies.ppo import PPOConfig, PPOTrainer
    trainer = PPOTrainer(env, pol, PPOConfig(device="cpu", seed=policy_seed, deterministic=True))
    if trainer.obs_norm is not None and ck.get("obs_norm"):
        trainer.obs_norm.load_state_dict(ck["obs_norm"])
    import torch

    rng = np.random.default_rng(99 + traffic)
    tau_used = 18.0
    base_acq = float(cfg.acq_signaling_s)
    cusum, base_late, alarm_chunk = 0.0, None, None
    ewma = 16.0
    chunks, probe_cost, probe_chunks = [], 0, []
    oracle_mag = None

    hist = []
    for c in range(CHUNKS):
        if c == DRIFT_CHUNK:
            env.cfg.acq_signaling_s = base_acq + DRIFT

        probing = mode == "loop" and alarm_chunk is not None and c == alarm_chunk + 1
        mag = tau_used
        if mode == "fixed":
            mag = 18.0
        elif mode == "ewma":
            mag = float(np.clip(ewma + 2.0, 8.0, 24.0))
        elif mode == "oracle":
            mag = 18.0 if c < DRIFT_CHUNK else (oracle_mag or 18.0)
        shield = shield_for(mag, rng=rng, probe_share=0.25 if probing else 0.0)

        start = len(env.attempt_log)
        for _ in range(CHUNK_STEPS):
            x, adj = env.candidate_graph()
            with torch.no_grad():
                at, aa, _lp, _v = trainer._act(env.obs(), x, adj, deterministic=True)
            env.step(at, aa, shield=shield, record=True)
        new = env.attempt_log[start:]
        h, late, n = chunk_stats(new)
        hist.extend(new)
        chunks.append(dict(chunk=c, hsr=h, late=late, n=n, mag=mag, probing=probing))

        if mode == "oracle" and c == DRIFT_CHUNK:
            k = crossing(new)
            oracle_mag = min(24.0, (k or 18.0) + 2.0)

        if mode == "ewma":
            ok_leads = [a["handover_advance_s"] for a in new
                        if abs(a["latitude_abs_deg"]) >= 70.0 and a["success"]]
            if ok_leads:
                ewma = 0.85 * ewma + 0.15 * float(np.percentile(ok_leads, 95))

        if mode == "loop":
            if c == DRIFT_CHUNK - 1:
                base_late = late
            if base_late is not None and c >= DRIFT_CHUNK and np.isfinite(late):
                cusum = max(0.0, cusum + (late - base_late - 1.0))
                if cusum > 3.0 and alarm_chunk is None:
                    alarm_chunk = c
            if probing:
                probe_chunks.append(c)
                probe_cost += sum(1 for a in new if abs(a["latitude_abs_deg"]) >= 70.0)
                cand = crossing(new)
                if cand is not None:
                    cand_used = min(cand + 2.0, 24.0)
                    lo_step, hi_step = (c - 2) * CHUNK_STEPS, (c - 1) * CHUNK_STEPS
                    recent = [a for a in hist if lo_step <= a["step"] < hi_step]
                    gain = replay(recent, cand_used) - replay(recent, tau_used)
                    chunks[-1]["gate_gain"] = float(gain)
                    chunks[-1]["candidate"] = float(cand_used)
                    if gain >= 5.0:
                        tau_used = cand_used
                    else:
                        tau_used = 18.0     # keep the incumbent == rollback

    post = [c["hsr"] for c in chunks[DRIFT_CHUNK:]]
    pre = [c["hsr"] for c in chunks[:DRIFT_CHUNK]]
    return dict(mode=mode, chunks=chunks,
                hsr_pre=float(np.nanmean(pre)), hsr_post=float(np.nanmean(post)),
                detection_delay=None if alarm_chunk is None else int(alarm_chunk - DRIFT_CHUNK),
                probe_polar_attempts=probe_cost, probe_chunks=probe_chunks,
                final_mag=tau_used)


def main() -> int:
    out = {"chunks": CHUNKS, "chunk_steps": CHUNK_STEPS, "drift_chunk": DRIFT_CHUNK, "drift_s": DRIFT,
           "runs": {}}
    for mode in ("fixed", "ewma", "oracle", "loop"):
        r = run(mode)
        out["runs"][mode] = r
        print(f"{mode:<7} pre {r['hsr_pre']:5.1f}  post {r['hsr_post']:5.1f}  "
              f"delay {r['detection_delay']}  probe {r['probe_polar_attempts']}  final {r['final_mag']}")
    write(OUT / "closed_loop" / "summary.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
