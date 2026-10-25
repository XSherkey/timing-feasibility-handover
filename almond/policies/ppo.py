"""PPO with two categorical heads over the batched handover environment.

Hyperparameters follow the manuscript's Table 3: clip 0.2, GAE lambda 0.95,
learning rate 3e-4, gamma 0.99, minibatch 256.  The implementation is
deliberately dependency-light (no gymnasium, no stable-baselines) so that the
same code runs on the ground GPU and, in CPU mode, inside the Ubuntu VM.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .nets import build_policy


@dataclass
class PPOConfig:
    total_episodes: int = 500
    rollout_steps: int = 256
    minibatch: int = 256
    epochs: int = 4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip: float = 0.2
    lr: float = 3e-4
    vf_coef: float = 0.5
    ent_coef: float = 0.01
    max_grad_norm: float = 0.5
    target_kl: float = 0.03
    seed: int = 0
    device: str = "cpu"
    early_stop_patience: int = 60
    early_stop_delta: float = 1e-3
    # -- stability -------------------------------------------------------- #
    #: episodes of behaviour cloning on the twin's analytic controller before
    #: PPO.  Without it a large fraction of seeds settle on the degenerate
    #: "never hand over" policy: the environment re-acquires a serving link by
    #: itself, so doing nothing is a strong local optimum and the first
    #: successful handover is never discovered.  Applied to every method.
    bc_episodes: int = 6
    bc_epochs: int = 12
    bc_lr: float = 1e-3
    #: linear decay of the entropy coefficient over training
    ent_coef_final: float = 0.002
    #: deterministic kernels; required for bit-reproducible runs
    deterministic: bool = True


class RunningNorm:
    """Observation normaliser fitted on the fly."""

    def __init__(self, dim: int, clip: float = 10.0):
        self.mean = np.zeros(dim, dtype=np.float64)
        self.var = np.ones(dim, dtype=np.float64)
        self.count = 1e-4
        self.clip = clip

    def update(self, x: np.ndarray) -> None:
        b = x.shape[0]
        bm = x.mean(axis=0)
        bv = x.var(axis=0)
        delta = bm - self.mean
        tot = self.count + b
        self.mean = self.mean + delta * b / tot
        m_a = self.var * self.count
        m_b = bv * b
        self.var = (m_a + m_b + delta**2 * self.count * b / tot) / tot
        self.count = tot

    def __call__(self, x: np.ndarray) -> np.ndarray:
        z = (x - self.mean) / np.sqrt(self.var + 1e-8)
        return np.clip(z, -self.clip, self.clip).astype(np.float32)

    def state_dict(self) -> dict:
        return dict(mean=self.mean, var=self.var, count=self.count)

    def load_state_dict(self, d: dict) -> None:
        self.mean = np.asarray(d["mean"], dtype=np.float64)
        self.var = np.asarray(d["var"], dtype=np.float64)
        self.count = float(d["count"])


class RunningRewardNorm:
    """Reward scaling by a running standard deviation."""

    def __init__(self, clip: float = 10.0):
        self.mean = 0.0
        self.var = 1.0
        self.count = 1e-4
        self.clip = clip

    def __call__(self, x: np.ndarray) -> np.ndarray:
        return np.clip(x / math.sqrt(self.var + 1e-8), -self.clip, self.clip).astype(np.float32)

    def update(self, x: np.ndarray) -> None:
        b = x.size
        bm = float(x.mean())
        bv = float(x.var())
        delta = bm - self.mean
        tot = self.count + b
        self.mean += delta * b / tot
        self.var = (self.var * self.count + bv * b + delta**2 * self.count * b / tot) / tot
        self.count = tot


class RolloutBuffer:
    def __init__(self):
        self.obs: list[np.ndarray] = []
        self.x: list[np.ndarray] = []
        self.adj: list[np.ndarray] = []
        self.act_t: list[np.ndarray] = []
        self.act_a: list[np.ndarray] = []
        self.logp: list[np.ndarray] = []
        self.val: list[np.ndarray] = []
        self.rew: list[np.ndarray] = []
        self.done: list[np.ndarray] = []

    def add(self, obs, x, adj, at, aa, lp, v, r, d) -> None:
        self.obs.append(obs)
        self.x.append(x)
        self.adj.append(adj)
        self.act_t.append(at)
        self.act_a.append(aa)
        self.logp.append(lp)
        self.val.append(v)
        self.rew.append(r)
        self.done.append(d)

    def __len__(self) -> int:
        return len(self.obs)

    def clear(self) -> None:
        self.__init__()

    def as_arrays(self):
        return (
            np.concatenate(self.obs),
            np.concatenate(self.x),
            np.concatenate(self.adj),
            np.concatenate(self.act_t),
            np.concatenate(self.act_a),
            np.concatenate(self.logp),
            np.concatenate(self.val),
            np.concatenate(self.rew),
            np.concatenate(self.done),
            np.array([o.shape[0] for o in self.obs]),
        )


class PPOTrainer:
    """PPO trainer bound to a batched environment."""

    def __init__(
        self,
        env,
        policy: nn.Module,
        cfg: PPOConfig | None = None,
        norm_obs: bool = True,
        norm_reward: bool = True,
        shield=None,
    ):
        self.env = env
        self.policy = policy.to(cfg.device if cfg else "cpu")
        self.cfg = cfg or PPOConfig()
        self.opt = torch.optim.Adam(self.policy.parameters(), lr=self.cfg.lr, eps=1e-5)
        self.obs_norm = RunningNorm(env.obs_dim) if norm_obs else None
        self.rew_norm = RunningRewardNorm() if norm_reward else None
        self.shield = shield
        self.history: list[dict] = []
        self.device = torch.device(self.cfg.device)
        self._seed_everything(self.cfg.seed)

    def _seed_everything(self, seed: int) -> None:
        """Seed every generator the training loop draws from.

        Bit-reproducibility matters for the manuscript's paired statistics: two
        runs with the same seed must follow the same trajectory, otherwise a
        per-seed comparison measures process scheduling rather than the method.
        """
        import random

        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        if self.cfg.deterministic:
            torch.use_deterministic_algorithms(True, warn_only=True)
            try:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
            except AttributeError:  # pragma: no cover
                pass
            torch.set_num_threads(1)

    # -- helpers ------------------------------------------------------- #
    def _to_t(self, arr: np.ndarray) -> torch.Tensor:
        return torch.as_tensor(arr, dtype=torch.float32, device=self.device)

    def _act(self, obs, x, adj, deterministic: bool = False, mask=None):
        o = self.obs_norm(obs) if self.obs_norm else obs
        ot, xt, at = self._to_t(o), self._to_t(x), self._to_t(adj)
        with torch.no_grad():
            lt, la, v = self.policy(ot, xt, at)
            if mask is not None:
                lt = lt.masked_fill(~mask, -1e9)
            dt = torch.distributions.Categorical(logits=lt)
            da = torch.distributions.Categorical(logits=la)
            if deterministic:
                at_t = lt.argmax(-1)
                at_a = la.argmax(-1)
            else:
                at_t = dt.sample()
                at_a = da.sample()
            logp = dt.log_prob(at_t) + da.log_prob(at_a)
        return (
            at_t.cpu().numpy(),
            at_a.cpu().numpy(),
            logp.cpu().numpy(),
            v.cpu().numpy(),
        )

    def action_mask(self, env) -> torch.Tensor | None:
        """Boolean mask over the target head: False for empty candidate slots."""
        cand = np.asarray(env.cand_idx[env.site, env.t_idx])
        valid = cand >= 0
        m = np.concatenate([np.ones((env.batch, 1), dtype=bool), valid], axis=1)
        return torch.as_tensor(m, device=self.device)

    # -- training ------------------------------------------------------ #
    def warm_start(self, episodes: int | None = None, log: bool = False) -> dict:
        """Behaviour-clone the twin's analytic controller, then hand over to PPO.

        The controller is the twin's own ``teacher_action`` (highest elevation
        whose acquisition time fits inside the remaining visibility).  Cloning it
        moves the actor out of the "never hand over" basin before the first
        policy-gradient step; PPO then improves on it, and every method in the
        comparison is warm-started identically.
        """
        episodes = self.cfg.bc_episodes if episodes is None else episodes
        if episodes <= 0 or not hasattr(self.env, "teacher_action"):
            return dict(skipped=True)
        obs_buf, x_buf, adj_buf, at_buf, aa_buf = [], [], [], [], []
        for _ in range(episodes):
            obs = self.env.reset()
            for _s in range(self.env.cfg.episode_steps):
                x, adj = self.env.candidate_graph()
                at, aa = self.env.teacher_action()
                obs_buf.append(obs.copy())
                x_buf.append(x.copy())
                adj_buf.append(adj.copy())
                at_buf.append(at.copy())
                aa_buf.append(aa.copy())
                obs, _r, _d, _i = self.env.step(at, aa, record=False)
        obs_all = np.concatenate(obs_buf, axis=0)
        x_all = np.concatenate(x_buf, axis=0)
        adj_all = np.concatenate(adj_buf, axis=0)
        at_all = np.concatenate(at_buf, axis=0)
        aa_all = np.concatenate(aa_buf, axis=0)
        if self.obs_norm is not None:
            self.obs_norm.update(obs_all)
        opt = torch.optim.Adam(self.policy.parameters(), lr=self.cfg.bc_lr)
        n = obs_all.shape[0]
        bs = max(64, min(512, n))
        losses = []
        for ep in range(self.cfg.bc_epochs):
            perm = np.random.permutation(n)
            tot = 0.0
            for i in range(0, n, bs):
                idx = perm[i: i + bs]
                o = self._to_t(self.obs_norm(obs_all[idx]) if self.obs_norm else obs_all[idx])
                lt, la, _v = self.policy(o, self._to_t(x_all[idx]), self._to_t(adj_all[idx]))
                t = torch.as_tensor(at_all[idx], dtype=torch.long, device=self.device)
                a = torch.as_tensor(aa_all[idx], dtype=torch.long, device=self.device)
                loss = (torch.nn.functional.cross_entropy(lt, t)
                        + torch.nn.functional.cross_entropy(la, a))
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.cfg.max_grad_norm)
                opt.step()
                tot += float(loss) * len(idx)
            losses.append(tot / max(1, n))
            if log:
                print(f"    bc epoch {ep + 1}/{self.cfg.bc_epochs} loss {losses[-1]:.4f}")
        return dict(skipped=False, samples=int(n), episodes=episodes, losses=losses)

    def train(self, total_episodes: int | None = None, log_every: int = 10, callback=None) -> dict:
        cfg = self.cfg
        total = total_episodes or cfg.total_episodes
        B = self.env.batch
        steps_per_episode = self.env.cfg.episode_steps
        obs = self.env.reset()
        ep_return = np.zeros(B, dtype=np.float64)
        ep_count = 0
        best_obj = -1e9
        since_improve = 0
        t_start = time.time()
        buffer = RolloutBuffer()
        ep_metrics: list[dict] = []
        update_count = 0

        while ep_count < total:
            buffer.clear()
            for _ in range(cfg.rollout_steps):
                x, adj = self.env.candidate_graph()
                at, aa, lp, v = self._act(obs, x, adj)
                nobs, rew, done, info = self.env.step(at, aa, shield=self.shield)
                if self.obs_norm:
                    self.obs_norm.update(obs)
                r = self.rew_norm(rew) if self.rew_norm else rew
                if self.rew_norm:
                    self.rew_norm.update(rew)
                buffer.add(obs, x, adj, at, aa, lp, v, r, done.astype(np.float32))
                ep_return += rew
                obs = nobs
                if np.any(done):
                    ep_count += int(done.sum())
                    st = self.env.episode_stats()
                    for i in np.flatnonzero(done):
                        ep_metrics.append(
                            dict(
                                lat=float(self.env.site_lat[self.env.site[i]]),
                                hsr=float(st["hsr"][i]),
                                attempts=int(st["attempts"][i]),
                                drops=int(st["drops"][i]),
                                ret=float(ep_return[i]),
                            )
                        )
                    ep_return[np.asarray(done, bool)] = 0.0
            self._update(buffer)

            if len(ep_metrics) >= 10:
                recent = ep_metrics[-min(len(ep_metrics), 4 * B):]
                lat = np.array([m["lat"] for m in recent])
                hsr = np.array([m["hsr"] for m in recent])
                att = np.array([m["attempts"] for m in recent], dtype=np.float64)
                arc = np.abs(lat) > 70
                obj = float(np.mean([m["ret"] for m in recent]))
                rec = dict(
                    episodes=ep_count,
                    steps=update_count,
                    obj=obj,
                    hsr_all=float(hsr.mean()),
                    hsr_arctic=float(hsr[arc].mean()) if arc.any() else float("nan"),
                    ret_mean=float(np.mean([m["ret"] for m in recent])),
                )
                self.history.append(rec)
                if obj > best_obj + cfg.early_stop_delta:
                    best_obj = obj
                    since_improve = 0
                else:
                    since_improve += 1
                if log_every and len(self.history) % log_every == 0:
                    cb = "" if callback is None else callback(rec)
                    print(
                        f"  ep {ep_count:5d} ret {rec['ret_mean']:7.3f} "
                        f"hsr {rec['hsr_all']*100:5.1f}% arctic {rec['hsr_arctic']*100:5.1f}% {cb}"
                    )
                if since_improve >= cfg.early_stop_patience:
                    print(f"  early stop at {ep_count} episodes (plateau)")
                    break
            update_count += 1

        return dict(
            episodes=ep_count,
            wall_s=time.time() - t_start,
            history=self.history,
            ep_metrics=ep_metrics,
            updates=update_count,
        )

    def _update(self, buf: RolloutBuffer) -> dict:
        cfg = self.cfg
        obs, x, adj, at, aa, lp_old, val, rew, done, lengths = buf.as_arrays()
        if self.obs_norm:
            obs_n = self.obs_norm(obs)
        else:
            obs_n = obs.astype(np.float32)
        n = obs_n.shape[0]

        # GAE over the flattened batch of parallel environments
        adv = np.zeros(n, dtype=np.float32)
        last_adv = np.zeros(self.env.batch, dtype=np.float32)
        idx = 0
        val = np.asarray(val, dtype=np.float32)
        for L in lengths:
            seg_v = val[idx: idx + L]
            seg_r = rew[idx: idx + L]
            seg_d = done[idx: idx + L]
            gae = 0.0
            for t in range(L - 1, -1, -1):
                next_v = 0.0 if t == L - 1 else seg_v[t + 1]
                nonterm = 1.0 - seg_d[t]
                delta = seg_r[t] + cfg.gamma * next_v * nonterm - seg_v[t]
                gae = delta + cfg.gamma * cfg.gae_lambda * nonterm * gae
                adv[idx + t] = gae
            idx += L
        ret = adv + val

        o_t = torch.as_tensor(obs_n, device=self.device)
        x_t = torch.as_tensor(x, device=self.device)
        a_t = torch.as_tensor(adj, device=self.device)
        at_t = torch.as_tensor(at, device=self.device)
        aa_t = torch.as_tensor(aa, device=self.device)
        lp_t = torch.as_tensor(lp_old, device=self.device)
        adv_t = torch.as_tensor(adv, device=self.device)
        ret_t = torch.as_tensor(ret, device=self.device)
        adv_t = (adv_t - adv_t.mean()) / (adv_t.std() + 1e-8)

        stats = {}
        for _epoch in range(cfg.epochs):
            perm = torch.randperm(n, device=self.device)
            for start in range(0, n, cfg.minibatch):
                mb = perm[start: start + cfg.minibatch]
                lt, la, v = self.policy(o_t[mb], x_t[mb], a_t[mb])
                dt = torch.distributions.Categorical(logits=lt)
                da = torch.distributions.Categorical(logits=la)
                logp = dt.log_prob(at_t[mb]) + da.log_prob(aa_t[mb])
                ratio = torch.exp(logp - lp_t[mb])
                s1 = ratio * adv_t[mb]
                s2 = torch.clamp(ratio, 1 - cfg.clip, 1 + cfg.clip) * adv_t[mb]
                pi_loss = -torch.min(s1, s2).mean()
                v_loss = F.mse_loss(v, ret_t[mb])
                ent = dt.entropy().mean() + da.entropy().mean()
                loss = pi_loss + cfg.vf_coef * v_loss - cfg.ent_coef * ent
                self.opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.policy.parameters(), cfg.max_grad_norm)
                self.opt.step()
                with torch.no_grad():
                    approx_kl = float(((ratio - 1) - torch.log(ratio)).mean())
                stats = dict(
                    pi_loss=float(pi_loss), v_loss=float(v_loss), entropy=float(ent), kl=approx_kl
                )
            if stats.get("kl", 0.0) > cfg.target_kl:
                break
        return stats

    # -- evaluation ---------------------------------------------------- #
    def evaluate(
        self,
        episodes: int = 5,
        sites: np.ndarray | None = None,
        t_range: tuple[int, int] | None = None,
        traffic_scale: float | None = None,
        deterministic: bool = True,
        record_attempts: bool = False,
    ) -> dict:
        env = self.env
        old_scale = env.cfg.traffic_scale
        if traffic_scale is not None:
            env.cfg.traffic_scale = traffic_scale
        saved_batch = env.batch
        rows = []
        attempts: list[dict] = []
        for _ in range(episodes):
            obs = env.reset(sites=sites, t_range=t_range)
            for _s in range(env.cfg.episode_steps):
                x, adj = env.candidate_graph()
                at, aa, lp, v = self._act(obs, x, adj, deterministic=deterministic)
                obs, rew, done, info = env.step(at, aa, shield=self.shield, record=record_attempts)
            st = env.episode_stats()
            lat = env.site_lat[env.site]
            for i in range(env.batch):
                rows.append(
                    dict(
                        lat=float(lat[i]),
                        site=env.twin.sites[int(env.site[i])].name,
                        hsr=float(st["hsr"][i]),
                        attempts=int(st["attempts"][i]),
                        successes=int(st["successes"][i]),
                        drops=int(st["drops"][i]),
                        lat_p95=float(st["lat_p95"][i]) if not np.isnan(st["lat_p95"][i]) else float("nan"),
                        lat_mean=float(st["lat_mean"][i]) if not np.isnan(st["lat_mean"][i]) else float("nan"),
                        served_frac=float(st["served_frac"][i]),
                    )
                )
            if record_attempts:
                attempts.extend(env.attempt_log)
        env.cfg.traffic_scale = old_scale
        return dict(rows=rows, attempts=attempts)

    def save(self, path: str, extra: dict | None = None) -> None:
        torch.save(
            dict(
                policy=self.policy.state_dict(),
                obs_norm=self.obs_norm.state_dict() if self.obs_norm else None,
                cfg=self.cfg,
                extra=extra or {},
            ),
            path,
        )

    def load(self, path: str, map_location: str = "cpu") -> dict:
        blob = torch.load(path, map_location=map_location, weights_only=False)
        self.policy.load_state_dict(blob["policy"])
        if self.obs_norm and blob.get("obs_norm"):
            self.obs_norm.load_state_dict(blob["obs_norm"])
        return blob.get("extra", {})
