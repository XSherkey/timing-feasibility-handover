"""LLM-guided graph neuroevolution with weight inheritance (Sec. 3.3).

The search space is the graph grammar :class:`almond.policies.nets.GraphSpec`.
Population-based evolution applies LLM-seeded initialisation, LLM-guided
mutation and crossover, weight inheritance, and Pareto selection over
``(task reward, parameter count, inference latency)``.  Every individual is
evaluated by short PPO training in the twin, so the search is budget-matched
against the unseeded baseline of Sec. 4.4.
"""
from __future__ import annotations

import copy
import json
import time
from dataclasses import dataclass, field

import numpy as np
import torch

from ..policies.nets import GraphSpec, build_policy, inherit_weights
from ..policies.ppo import PPOConfig, PPOTrainer


@dataclass
class NASConfig:
    population: int = 20
    generations: int = 8
    #: instance-episodes of proxy training per candidate.  Measured on twelve
    #: architectures: rho against deployment is 0.23 at 24 episodes, 0.48 at 960
    #: and flat afterwards, so 960 is the cheapest predictive horizon.
    eval_episodes: int = 960
    batch: int = 8
    episode_steps: int = 240
    param_budget: int = 50_000
    latency_budget_ms: float = 15.0
    critique_every: int = 10
    seed: int = 0
    device: str = "cpu"
    mutation_rate: float = 0.35
    crossover_rate: float = 0.40
    #: per-architecture GPU-hour cost model (calibrated from the evaluation runs)
    gpu_hours_per_eval: float | None = None
    # ---- evaluation protocol (round-4 fixes C1 / C2) -------------------- #
    #: independent environment seeds per candidate, averaged.  A single rollout
    #: is noise-dominated: the same architecture scored 0.76-1.34 on repeat.
    eval_seeds: int = 2
    #: deployment-facing scoring episodes per seed (validation split only)
    deploy_episodes: int = 2
    #: common random numbers: one policy-initialisation seed for the whole search,
    #: so candidates are compared under the same initialisation instead of under
    #: their own private draw of the init lottery
    init_seed: int | None = None
    #: behaviour-cloning warm start inside each proxy evaluation, so the proxy
    #: measures "what this architecture can do with the shared prior", which is
    #: what deployment measures
    bc_episodes: int = 6
    bc_epochs: int = 12


@dataclass(eq=False)
class Individual:
    """One candidate architecture in the population.

    ``eq=False`` keeps identity semantics: the default dataclass ``__eq__`` would
    compare every field, including ``weights`` (a dict of tensors), and comparing
    two tensors raises "Boolean value of Tensor with more than one value is
    ambiguous".  The Pareto bookkeeping uses ``in`` / ``not in``, which relies on
    ``==``, so this bit randomly aborted searches.
    """
    spec: GraphSpec
    reward: float = -np.inf
    params: int = 0
    latency_ms: float = np.inf
    episodes: int = 0
    gpu_s: float = 0.0
    rank: int = -1
    crowd: float = 0.0
    origin: str = "seed"
    weights: dict | None = None
    #: deployment-facing sub-scores recorded alongside the satisfaction objective
    hsr_arctic: float = float("nan")
    train_return: float = float("nan")

    def fitness(self, param_budget: int) -> tuple[float, float, float]:
        return (
            -self.reward,
            self.params / max(param_budget, 1),
            self.latency_ms,
        )

    def feasible(self, param_budget: int, latency_budget: float) -> bool:
        return self.params <= param_budget and self.latency_ms <= latency_budget


def estimate_latency_ms(params: int, node_count: int, hard: float = 12.0) -> float:
    """Analytic latency model used when a hardware measurement is not available.

    Calibrated on the batch-1 CPU measurements of Sec. 4.4: a 50 K-parameter
    policy needs a single forward pass of roughly 50 K multiplies, which on the
    reference embedded class costs ``hard`` milliseconds including framework
    overhead.  The value is later replaced by the measured distribution.
    """
    base = 1.2  # framework + dispatch overhead
    per_param = (hard - base) / 50_000.0
    return base + per_param * params + 0.02 * node_count


class Evolver:
    """LLM-guided Pareto evolution over the graph grammar."""

    def __init__(
        self,
        llm,
        env_factory,
        cfg: NASConfig,
        regime_tags: dict | None = None,
        regime_hint: str = "balanced",
        use_llm: bool = True,
        inherit: bool = True,
        weights: dict | None = None,
        split: tuple[float, float] = (0.76, 0.81),
    ):
        self.llm = llm
        self.env_factory = env_factory
        self.cfg = cfg
        self.regime_tags = regime_tags or {}
        self.regime_hint = regime_hint
        self.use_llm = use_llm
        self.inherit = inherit
        #: reward weights of the translated intent, needed to score candidates with
        #: the same satisfaction metric the deployment pipeline reports
        self.weights = weights or dict(w_rel=0.4, w_lat=0.4, w_pow=0.2)
        #: evaluation window as fractions of the twin horizon (validation split, so
        #: the search never touches the held-out test window)
        self.split = split
        self.rng = np.random.default_rng(cfg.seed)
        self.population: list[Individual] = []
        self.history: list[dict] = []
        self.trace: list[dict] = []
        self.eval_count = 0
        self.gpu_s = 0.0
        self.probs = dict(mutation_rate=cfg.mutation_rate, crossover_rate=cfg.crossover_rate)
        self.critiques: list[dict] = []
        #: computed once per search: what the polar regime actually looks like, so
        #: the LLM reasons about telemetry instead of a hard-coded sentence
        self.regime_stats: dict = {}
        #: completed evaluations, in the compact form the prompts receive
        self.table: list[dict] = []

    # -- regime description --------------------------------------------- #
    def _regime_stats(self) -> dict:
        """Summarise the polar regime from the twin matrices.

        Replaces the constant ``regime_hint`` sentence with numbers the model can
        act on: how often a candidate has no feeder route, how long visibility
        lasts, how low the elevations are, how many candidates exist.
        """
        env = self._make_env(seed=int(self.cfg.seed) + 11)
        nt = env.nt
        si = np.flatnonzero(np.abs(env.site_lat) > 70.0)
        if si.size == 0:
            si = np.arange(len(env.site_lat))
        cand = env.cand_idx[si]                      # (S, T, K)
        valid = cand >= 0
        cc = np.maximum(cand, 0)
        tidx = np.broadcast_to(np.arange(nt)[None, :, None], cc.shape)
        hop = env.hop[cc, tidx]
        el = env.el[si[:, None, None], cc, tidx]
        trem = env.trem[si[:, None, None], cc, tidx]
        routed = valid & (hop >= 0)
        vals_h = hop[routed] if routed.any() else np.zeros(1)
        vals_t = trem[routed] if routed.any() else np.zeros(1)
        vals_e = el[valid] if valid.any() else np.zeros(1)
        return dict(
            polar_sites=int(si.size),
            epochs=int(nt),
            candidates_per_step_mean=round(float(valid.sum(-1).mean()), 2),
            no_route_fraction=round(float(1.0 - routed.mean()), 3),
            hop_p50=float(np.percentile(vals_h, 50)),
            hop_p90=float(np.percentile(vals_h, 90)),
            visibility_below_60s_fraction=round(float((vals_t < 60).mean()), 3),
            visibility_p50_s=float(np.percentile(vals_t, 50)),
            elevation_below_15deg_fraction=round(float((vals_e < 15).mean()), 3),
            elevation_p50_deg=float(np.percentile(vals_e, 50)),
        )

    def _brief(self, i: int) -> str:
        """Differentiated seeding brief (fix C5).

        Ten identical prompts produced ten near-identical sketches; each seed now
        asks for a different design hypothesis.
        """
        briefs = [
            "the smallest architecture likely to remain competent (parameter efficiency first)",
            "a graph-heavy design, since candidate structure is relational",
            "a design with a wider decision trunk than the graph trunk (asymmetric heads)",
            "a design that conditions on edge semantics instead of treating all edges alike",
            "a deeper-but-narrow design, if depth buys receptive field cheaply",
            "a design that trades parameter count for a wider context encoder over the telemetry fields",
            "a hybrid that mixes attention where degrees vary and convolution where they do not",
            "a conservative design close to the incumbent elite, as a local refinement",
            "a design that maximises robustness to un-routed candidates rather than raw capacity",
            "an aggressive design at the parameter-budget boundary, as an upper bound probe",
        ]
        return briefs[i % len(briefs)]

    def _table_row(self, ind: "Individual") -> dict:
        return dict(
            kind=ind.spec.kind,
            width=int(ind.spec.width),
            layers=int(ind.spec.layers),
            heads=int(ind.spec.heads),
            head_width=int(getattr(ind.spec, "head_width", 0) or 0),
            edge_types=int(getattr(ind.spec, "edge_types", 0) or 0),
            params=int(ind.params),
            latency_ms=round(float(ind.latency_ms), 2),
            satisfaction=round(float(ind.reward), 1),
            arctic_hsr=round(float(ind.hsr_arctic) * 100, 1) if ind.hsr_arctic == ind.hsr_arctic else None,
            origin=ind.origin,
            diag=getattr(ind, "diag", None) or {},
        )

    def _task_card(self) -> dict:
        """What the model is designing for, in one structured card."""
        return dict(
            task="LEO handover control: choose a candidate satellite and a preparation lead time",
            action_heads="target (K+1 options, 0 = keep current link) and advance bucket (M options)",
            observations="14 telemetry fields + a local subgraph of 1 serving node + K candidates",
            objective="intent satisfaction S (reliability / latency / power weighted), Arctic HSR",
            constraints=[
                "parameters <= 50000",
                "estimated single-batch latency <= 15 ms",
                "no recurrence over the episode (the policy is a per-step function)",
            ],
            known_failure_modes=[
                "target head collapses onto 'keep current link' and never hands over",
                "advance head saturates at the minimum bucket, so acquisition is never covered",
                "no route to the chosen candidate (feeder path missing above the polar seam)",
                "requested lead exceeds the remaining visibility of the chosen candidate",
            ],
        )

    # -- seeding -------------------------------------------------------- #
    def seed_population(self, n: int) -> None:
        specs: list[GraphSpec] = []
        if not self.regime_stats:
            self.regime_stats = self._regime_stats()
        if self.use_llm:
            # C5: one brief per seed, plus the computed regime statistics and
            # whatever the knowledge graph already holds, so the ten proposals are
            # ten hypotheses rather than ten draws from the same prompt
            history = list(self.history)
            for i in range(min(n, 10)):
                out = self.llm(
                    "topology_seed",
                    dict(
                        regime_tags=self.regime_tags,
                        regime_hint=self.regime_hint,
                        design_brief=self._brief(i),
                        regime_stats=dict(self.regime_stats),
                        task=self._task_card(),
                        history=history,
                    ),
                    seed=self.cfg.seed * 1000 + i,
                )
                specs.append(GraphSpec.from_dict(out))
        # fill the remainder with random grammar samples (the unseeded baseline)
        while len(specs) < n:
            specs.append(self._random_spec())
        for i, s in enumerate(specs[:n]):
            self.population.append(Individual(spec=s, origin="llm_seed" if i < (min(n, 10) if self.use_llm else 0) else "random"))

    def _random_spec(self) -> GraphSpec:
        kinds = ["mlp", "gcn", "att", "hybrid"]
        widths = [32, 64, 96, 128, 192, 256]
        return GraphSpec(
            kind=kinds[int(self.rng.integers(0, 4))],
            width=int(widths[int(self.rng.integers(0, len(widths)))]),
            layers=int(self.rng.integers(1, 4)),
            heads=int([1, 2, 4][int(self.rng.integers(0, 3))]),
            pool=["mean", "max"][int(self.rng.integers(0, 2))],
            ctx_width=int(widths[int(self.rng.integers(0, len(widths)))]),
            ctx_layers=int(self.rng.integers(1, 3)),
            # the two structural switches are sampled too, so the unseeded arm can
            # reach every architecture the LLM arm can
            head_width=int([0, 0, 32, 64, 96, 128][int(self.rng.integers(0, 6))]),
            edge_types=int(self.rng.integers(0, 2)),
            provenance=dict(origin="random"),
        )

    # -- evaluation ----------------------------------------------------- #
    def _make_env(self, seed: int | None = None):
        """Build an environment, passing a seed when the factory supports it."""
        try:
            return self.env_factory(self.cfg.batch, self.cfg.episode_steps, seed=seed)
        except TypeError:
            return self.env_factory(self.cfg.batch, self.cfg.episode_steps)

    def _deploy_score(self, trainer, episodes: int | None = None) -> dict:
        """Score a trained candidate the way the deployment pipeline does.

        Two differences from the old proxy: the window is the validation split
        (never the test split), and the metric is the reported objective —
        attempt-weighted Arctic HSR plus the intent-satisfaction score — rather
        than the mean training return over a handful of rollouts.

        Alongside the score it records the *diagnostics* the prompts need
        (action histograms, head entropy, dominant failure cause), which is what
        turns the LLM's next proposal into a hypothesis about a real limitation.
        """
        from ..analysis.metrics import attempt_weighted_hsr, satisfaction

        episodes = self.cfg.deploy_episodes if episodes is None else episodes
        rows: list[dict] = []
        target_hist = np.zeros(trainer.policy.n_targets, dtype=np.int64)
        advance_hist = np.zeros(trainer.policy.n_advance, dtype=np.int64)
        causes: dict[str, int] = {}
        for k in range(self.cfg.eval_seeds):
            env = self._make_env(seed=int(self.cfg.seed) * 7919 + 100 + k)
            lo, hi = self.split
            t0 = int(lo * env.nt)
            t1 = max(t0 + env.cfg.episode_steps + 2, int(hi * env.nt))
            for ep_i in range(episodes):
                env.reset(t_range=(t0, t1))
                # record only the last episode of the last seed: enough for the
                # failure-cause histogram without storing every rollout
                rec = (k == self.cfg.eval_seeds - 1) and (ep_i == episodes - 1)
                for _s in range(env.cfg.episode_steps):
                    x, adj = env.candidate_graph()
                    mask = trainer.action_mask(env)
                    at, aa, _lp, _v = trainer._act(env.obs(), x, adj, deterministic=True, mask=mask)
                    target_hist += np.bincount(at, minlength=target_hist.size)
                    advance_hist += np.bincount(aa, minlength=advance_hist.size)
                    env.step(at, aa, record=rec)
                if rec:
                    for a in env.attempt_log:
                        key = str(a.get("cause", "unknown"))
                        causes[key] = causes.get(key, 0) + 1
                st = env.episode_stats()
                lat = env.site_lat[env.site]
                for i in range(env.batch):
                    rows.append(
                        dict(
                            lat=float(lat[i]),
                            hsr=float(st["hsr"][i]),
                            attempts=int(st["attempts"][i]),
                            successes=int(st["successes"][i]),
                            lat_p95=float(st["lat_p95"][i]) if not np.isnan(st["lat_p95"][i]) else float("nan"),
                            power_mean=float(np.nanmean([p[i] for p in env.pow_hist])) if env.pow_hist else 0.5,
                        )
                    )
        keep_frac = float(target_hist[0] / max(1, target_hist.sum()))
        p = advance_hist / max(1, advance_hist.sum())
        ent_adv = float(-(p[p > 0] * np.log(p[p > 0])).sum())
        return dict(
            S=float(satisfaction(rows, self.weights)),
            hsr_arctic=float(attempt_weighted_hsr(rows)),
            hsr_all=float(attempt_weighted_hsr(rows, min_abs_lat=None)),
            rows=rows,
            diag=dict(
                keep_link_fraction=round(keep_frac, 3),
                never_hands_over=bool(keep_frac > 0.95),
                advance_min_bucket_fraction=round(float(advance_hist[0] / max(1, advance_hist.sum())), 3),
                advance_entropy=round(ent_adv, 3),
                failure_causes=causes,
            ),
        )

    def evaluate(self, ind: Individual, parent: Individual | None = None) -> Individual:
        t0 = time.time()
        env = self._make_env(seed=int(self.cfg.seed) + 1)
        x, adj = env.candidate_graph()
        # project the sketch onto the parameter envelope before spending an
        # evaluation on it (the grammar rule "parameter budget <= 50K" is
        # enforced by construction, not by post-hoc rejection)
        spec = self._project_to_budget(ind.spec, env, x)
        ind.spec = spec
        # C1: common random numbers.  The *initialisation* is fixed for the whole
        # search, so two candidates are never compared across different draws of
        # the init lottery; only the environment seed varies, and that is averaged.
        import random as _random

        import torch as _torch

        init_seed = self.cfg.init_seed if self.cfg.init_seed is not None else int(self.cfg.seed) * 100003 + 7
        _random.seed(init_seed)
        np.random.seed(init_seed)
        _torch.manual_seed(init_seed)
        policy = build_policy(
            "graph",
            obs_dim=env.obs_dim,
            node_dim=x.shape[-1],
            n_targets=env.K + 1,
            n_advance=env.n_advance,
            spec=spec,
        )
        if self.inherit and parent is not None and parent.weights is not None:
            inherit_weights(policy, parent.weights)
        pcfg = PPOConfig(
            total_episodes=self.cfg.eval_episodes,
            rollout_steps=64,
            minibatch=64,
            epochs=2,
            lr=1e-3,
            device=self.cfg.device,
            early_stop_patience=10_000,
            bc_episodes=self.cfg.bc_episodes,
            bc_epochs=self.cfg.bc_epochs,
            seed=init_seed,
        )
        trainer = PPOTrainer(env, policy, pcfg, norm_obs=True, norm_reward=True)
        # C2: warm start from the analytic teacher, exactly as deployment does
        if self.cfg.bc_episodes > 0:
            trainer.warm_start()
        res = trainer.train(log_every=0)
        # C2: score with the reported objective on the validation split
        score = self._deploy_score(trainer)
        ind.reward = float(score["S"])
        ind.hsr_arctic = float(score["hsr_arctic"])
        ind.diag = score["diag"]
        ind.train_return = float(np.mean([m["ret"] for m in res["ep_metrics"]] or [-1.0]))
        ind.params = policy.param_count()
        ind.latency_ms = estimate_latency_ms(ind.params, 1 + env.K)
        ind.episodes = res["episodes"]
        ind.gpu_s = time.time() - t0
        ind.weights = {k: v.detach().clone() for k, v in policy.state_dict().items()}
        self.table.append(self._table_row(ind))
        self.eval_count += 1
        self.gpu_s += ind.gpu_s
        # anytime trace: best-so-far objective after every evaluation
        self.trace.append(
            dict(
                evals=self.eval_count,
                gpu_s=float(self.gpu_s),
                reward=float(ind.reward),
                hsr_arctic=float(ind.hsr_arctic),
                train_return=float(ind.train_return),
                params=int(ind.params),
                best_reward=float(
                    max(
                        (q.reward for q in self.population + [ind]
                         if q.feasible(self.cfg.param_budget, self.cfg.latency_budget_ms)),
                        default=ind.reward,
                    )
                ),
            )
        )
        return ind

    def _project_to_budget(self, spec: GraphSpec, env, x) -> GraphSpec:
        """Shrink a sketch until its parameter count fits the on-board envelope."""
        import copy as _copy

        s = _copy.deepcopy(spec)
        for _ in range(6):
            pol = build_policy(
                "graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                n_targets=env.K + 1, n_advance=env.n_advance, spec=s,
            )
            if pol.param_count() <= self.cfg.param_budget:
                return s
            # shrink the widest component first
            if s.width >= s.ctx_width and s.width > 32:
                s.width = max(32, s.width // 2)
            elif s.ctx_width > 32:
                s.ctx_width = max(32, s.ctx_width // 2)
            elif int(getattr(s, "head_width", 0) or 0) > 32:
                s.head_width = max(32, int(s.head_width) // 2)
            elif s.layers > 1:
                s.layers -= 1
            else:
                s.kind = "mlp"
                s.width = 32
                s.ctx_width = 32
        return s

    # -- operators ------------------------------------------------------ #
    def _mutate(self, parent: Individual) -> Individual:
        if self.use_llm and self.rng.random() < 0.7:
            rewards = [p.reward for p in self.population if np.isfinite(p.reward)]
            fb = dict(
                objective="params" if parent.params > self.cfg.param_budget * 0.9 else "satisfaction",
                too_large=bool(parent.params > self.cfg.param_budget * 0.9),
                underfit=bool(parent.reward < (np.median(rewards) if rewards else 0.0)),
                satisfaction=round(float(parent.reward), 1),
                arctic_hsr=round(float(parent.hsr_arctic) * 100, 1),
                params=int(parent.params),
                latency_ms=round(float(parent.latency_ms), 2),
                diagnosis=getattr(parent, "diag", None) or {},
                recent_results=self.table[-6:],
            )
            out = self.llm(
                "topology_mutation",
                dict(sketch=parent.spec.to_dict(), fitness_feedback=fb),
                seed=int(self.rng.integers(0, 1 << 30)),
            )
            spec = GraphSpec.from_dict(out)
        else:
            spec = self._random_spec()
        return Individual(spec=spec, origin="llm_mut" if self.use_llm else "rand_mut")

    def _crossover(self, a: Individual, b: Individual) -> Individual:
        if self.use_llm and self.rng.random() < 0.7:
            out = self.llm(
                "topology_crossover",
                dict(sketch_a=a.spec.to_dict(), sketch_b=b.spec.to_dict()),
                seed=int(self.rng.integers(0, 1 << 30)),
            )
            spec = GraphSpec.from_dict(out)
        else:
            spec = copy.deepcopy(a.spec if self.rng.random() < 0.5 else b.spec)
            spec.layers = b.spec.layers
        return Individual(spec=spec, origin="llm_cross" if self.use_llm else "rand_cross")

    # -- selection ------------------------------------------------------ #
    def _pareto(self) -> None:
        feasible = [p for p in self.population if p.feasible(self.cfg.param_budget, self.cfg.latency_budget_ms)]
        pool = feasible or self.population
        fronts: list[list[Individual]] = []
        remaining = list(pool)
        while remaining:
            front = []
            for p in remaining:
                dominated = False
                for q in remaining:
                    if q is p:
                        continue
                    if all(
                        x <= y for x, y in zip(q.fitness(self.cfg.param_budget), p.fitness(self.cfg.param_budget))
                    ) and any(
                        x < y for x, y in zip(q.fitness(self.cfg.param_budget), p.fitness(self.cfg.param_budget))
                    ):
                        dominated = True
                        break
                if not dominated:
                    front.append(p)
            for p in front:
                p.rank = len(fronts)
            fronts.append(front)
            remaining = [p for p in remaining if not any(p is f for f in front)]
        for f in fronts:
            if len(f) > 2:
                for key in ("reward", "params", "latency_ms"):
                    vals = np.array([getattr(p, key) for p in f], dtype=float)
                    rng = vals.max() - vals.min()
                    if rng <= 0:
                        continue
                    order = np.argsort(vals)
                    d = np.zeros(len(f))
                    d[order[0]] = d[order[-1]] = np.inf
                    d[order[1:-1]] = (vals[order[2:]] - vals[order[:-2]]) / rng
                    for i, p in enumerate(f):
                        p.crowd += float(d[i])

    def _select(self, n: int) -> list[Individual]:
        self._pareto()
        ranked = sorted(self.population, key=lambda p: (p.rank, -p.crowd))
        return ranked[:n]

    # -- loop ----------------------------------------------------------- #
    def run(self) -> dict:
        cfg = self.cfg
        t0 = time.time()
        self.seed_population(cfg.population)
        for i, p in enumerate(self.population):
            self.evaluate(p)
            self.history.append(self._snapshot(gen=0, evals=self.eval_count))
        gen = 0
        while gen < cfg.generations:
            gen += 1
            elites = self._select(max(2, cfg.population // 4))
            children: list[Individual] = []
            while len(children) < cfg.population - len(elites):
                if self.rng.random() < self.probs["crossover_rate"] and len(elites) >= 2:
                    a, b = self.rng.choice(len(elites), size=2, replace=False)
                    child = self._crossover(elites[a], elites[b])
                    parent = elites[a] if elites[a].reward >= elites[b].reward else elites[b]
                else:
                    a = int(self.rng.integers(0, len(elites)))
                    child = self._mutate(elites[a])
                    parent = elites[a]
                self.evaluate(child, parent if self.inherit else None)
                children.append(child)
            self.population = elites + children
            if self.use_llm and gen % 3 == 0:
                out = self.llm(
                    "population_critique",
                    dict(
                        elites=[self._table_row(e) for e in elites],
                        probs=self.probs,
                        regime_stats=dict(self.regime_stats),
                        best_so_far=max((p.reward for p in self.population), default=0.0),
                        evaluated=self.eval_count,
                        recent_results=self.table[-10:],
                    ),
                    seed=int(self.rng.integers(0, 1 << 30)),
                )
                self.critiques.append(out)
                self.probs["mutation_rate"] = float(np.clip(out.get("mutation_rate", 0.35), 0.1, 0.6))
                self.probs["crossover_rate"] = float(np.clip(out.get("crossover_rate", 0.4), 0.1, 0.7))
            self.history.append(self._snapshot(gen=gen, evals=self.eval_count))
        self._pareto()
        feasible = [p for p in self.population if p.feasible(cfg.param_budget, cfg.latency_budget_ms)]
        front = sorted(feasible or self.population, key=lambda p: (p.rank, -p.reward))
        best = max(front, key=lambda p: p.reward) if front else self.population[0]
        return dict(
            best=best,
            front=front[:6],
            evaluated=self.eval_count,
            gpu_s=self.gpu_s,
            wall_s=time.time() - t0,
            history=self.history,
            trace=self.trace,
            table=self.table,
            regime_stats=self.regime_stats,
            critiques=self.critiques,
            probs=self.probs,
            protocol=dict(
                eval_episodes=self.cfg.eval_episodes,
                eval_seeds=self.cfg.eval_seeds,
                deploy_episodes=self.cfg.deploy_episodes,
                bc_episodes=self.cfg.bc_episodes,
                init_seed=self.cfg.init_seed,
                split=list(self.split),
                metric="satisfaction on the validation split",
            ),
        )

    def _snapshot(self, gen: int, evals: int) -> dict:
        feasible = [p for p in self.population if p.feasible(self.cfg.param_budget, self.cfg.latency_budget_ms)]
        best = max((p.reward for p in (feasible or self.population)), default=-np.inf)
        return dict(
            gen=gen,
            evals=evals,
            gpu_s=self.gpu_s,
            best_reward=float(best),
            hypervolume=self.hypervolume(),
            feasible=len(feasible),
        )

    def hypervolume(self, ref: tuple[float, float] = (0.0, -1.0)) -> float:
        """2-D hypervolume of the feasible front in ``(reward, -params/budget)``.

        Only individuals that satisfy both the parameter and the latency cap
        contribute, which is what makes the Pareto metric a *budgeted* quality
        measure rather than a raw reward average.
        """
        pts = sorted(
            {
                (round(float(p.reward), 6), round(-p.params / self.cfg.param_budget, 6))
                for p in self.population
                if p.feasible(self.cfg.param_budget, self.cfg.latency_budget_ms)
            }
        )
        if not pts:
            return 0.0
        r_ref, q_ref = ref
        # ascending in the first objective; for each strip the achievable second
        # objective is the best q among all points at or beyond that strip
        suffix_max = np.maximum.accumulate(np.array([q for _, q in pts])[::-1])[::-1]
        area = 0.0
        prev_r = r_ref
        for i, (r, _q) in enumerate(pts):
            if r <= prev_r:
                continue
            area += (r - prev_r) * max(suffix_max[i] - q_ref, 0.0)
            prev_r = r
        return float(area)
