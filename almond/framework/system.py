"""The ALMOND end-to-end loop (Algorithm 1).

``AlmondSystem`` wires together the forward translator, the reverse forensic
engine, the three-stage auditor, the knowledge graph, the constraint shield and
the LLM-guided topology search, and exposes a single ``run`` method whose
behaviour is switched by :class:`AlmondConfig` so that every ablation of the
manuscript (Sec. 4.7) is the *same* code path with one component disabled.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from ..llm.backend import LLMClient, LLMLog, SurrogateBackend
from ..nas.evolution import Evolver, NASConfig, estimate_latency_ms
from ..policies.nets import GraphSpec, build_policy
from ..policies.ppo import PPOConfig, PPOTrainer
from ..twin.env import EnvConfig, HandoverEnv
from ..twin.twin import DigitalTwin, TwinConfig
from .auditor import Auditor, ImpactPredictor
from .forensics import ForensicEngine, SplitConfig, replay_rule, score
from .kg import KnowledgeGraph
from .shield import compile_constraints
from .translator import ForwardTranslator, INTENT_TEMPLATES

VARIANTS = (
    "full",
    "no_forensics",
    "no_memory",
    "no_counterfactual",
    "no_nas",
    "fixed_arch",
    "handcrafted",
    "static_llm",
    "eureka",
    "oracle",
)


@dataclass
class AlmondConfig:
    variant: str = "full"
    seed: int = 0
    device: str = "cuda"
    # training
    episodes: int = 500
    batch: int = 32
    episode_steps: int = 240
    rollout_steps: int = 256
    minibatch: int = 256
    epochs: int = 4
    lr: float = 3e-4
    ent_coef: float = 0.01
    max_grad_norm: float = 0.5
    eval_every: int = 25
    # forensics
    forensics_after: int = 25
    theta_rho: float = 0.85
    delta_min: float = 0.05
    #: the counterfactual validation gate.  False admits any candidate whose replay
    #: is not catastrophic (delta_min → -1), which is the "no gate" control used by
    #: the multi-intent experiments; defaults to True so existing behaviour is kept.
    counterfactual_gate: bool = True
    validate_episodes: int = 2
    test_episodes: int = 2
    # intent
    intent: str = "reliability_first"
    # architecture
    nas_generations: int = 6
    nas_population: int = 12
    nas_eval_episodes: int = 40
    nas_batch: int = 8
    # misc
    out_dir: str | None = None
    llm_backend: str = "auto"
    max_forensic_rounds: int = 1
    discovery_mode: str = "enriched"  # "legacy" reproduces the pre-enrichment sampling
    bc_episodes: int = 6      # behaviour-cloning warm start (0 disables)
    nas_eval_seeds: int = 2   # independent env seeds per search candidate
    nas_deploy_episodes: int = 2  # scoring episodes per seed in the search proxy
    bc_epochs: int = 12
    deterministic: bool = True
    #: stop after the behaviour-cloning warm start (no PPO, no forensics): the
    #: "prior only" baseline that decides whether the apparatus beats the
    #: analytic controller it was initialised from
    skip_ppo: bool = False
    twin_tag: str = "ref"
    twin_hours: float = 12.0
    #: physical overrides for the regime-perturbation experiment (None = default).
    #: The acquisition-time model lives in EnvConfig, so shifting these coefficients
    #: is what "changing the physics" means for the falsifiable claim that the
    #: mined threshold tracks the measured setup-time quantile.
    acq_signaling_s: float | None = None
    acq_sync_base_s: float | None = None
    seam_penalty_s: float | None = None
    #: twin-level physical overrides (None = TwinConfig default).  Without these the
    #: tag is only a cache name and every "regime" run silently uses the default twin.
    feeder_slots: int | None = None
    isl_seam_enabled: bool | None = None
    isl_dropout: float | None = None
    constellation: str | None = None
    #: Probe-Calibrated Shield (PCS): replace the LLM's magnitude with an actively
    #: probed threshold tau* = min{a : P(late | a) <= probe_eps}.  The LLM still
    #: proposes the condition (which regime / fields); the number comes from data,
    #: which is what makes the loop robust to a shift in the physics.
    probe_calibrated: bool = False
    probe_eps: float = 0.05
    probe_episodes: int = 2
    probe_advances: tuple[float, ...] = (6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26)
    #: penalty-vs-shield contrast: inject the same knowledge as a reward penalty
    late_risk_tau: float = 0.0
    late_risk_lat: float = 68.0
    late_risk_weight: float = 0.0
    #: cost of early preparation (dual-homing); 0 = legacy (lead is free)
    dual_homing_latency_ms_per_s: float = 0.0
    dual_homing_power_per_s: float = 0.0
    #: a pre-discovered architecture to reuse instead of re-running the search
    fixed_spec: dict | None = None


from ..analysis.metrics import attempt_weighted_hsr, satisfaction  # noqa: E402

__all__ = ["AlmondConfig", "AlmondSystem", "satisfaction"]


class AlmondSystem:
    def __init__(self, cfg: AlmondConfig, twin: DigitalTwin | None = None, out_dir: str | Path | None = None):
        self.cfg = cfg
        self.out = Path(out_dir or cfg.out_dir or "results/run")
        self.out.mkdir(parents=True, exist_ok=True)
        if twin is None:
            # The tag only names the cache; the *physics* lives in TwinConfig.  Until
            # this was wired, `--twin-tag noseam` silently loaded a default twin, so
            # "another constellation / regime" could not actually be evaluated.
            twin_kwargs = {}
            if cfg.feeder_slots is not None:
                twin_kwargs["feeder_slots"] = cfg.feeder_slots
            if cfg.isl_seam_enabled is not None:
                twin_kwargs["isl_seam_enabled"] = cfg.isl_seam_enabled
            if cfg.isl_dropout is not None:
                twin_kwargs["isl_dropout"] = cfg.isl_dropout
            if cfg.constellation is not None:
                twin_kwargs["constellation"] = cfg.constellation
            twin = DigitalTwin(
                TwinConfig(tag=cfg.twin_tag, horizon_s=cfg.twin_hours * 3600, **twin_kwargs)
            ).build(verbose=False)
        self.twin = twin
        self.llm_log = LLMLog(self.out / "llm_calls.jsonl")
        # honour the environment: a configured OpenAI-compatible endpoint is used
        # automatically; ALMOND_LLM_BACKEND=surrogate forces the offline fallback
        import os as _os

        from ..llm.backend import _default_backend

        if cfg.llm_backend == "surrogate" or _os.environ.get("ALMOND_LLM_BACKEND") == "surrogate":
            backend = SurrogateBackend()
        else:
            backend = _default_backend()
        self.llm = LLMClient(backend, self.llm_log)
        self.kg = KnowledgeGraph(self.out / "knowledge_graph.json")
        self.auditor = Auditor(impact=None, require_impact=(cfg.variant == "full"))
        self.splits = SplitConfig()
        self.intent = INTENT_TEMPLATES[cfg.intent]
        self.events: list[dict] = []
        self.forensic_results: list[dict] = []
        self.curve: list[dict] = []
        self.shield = None
        self.spec: GraphSpec | None = None
        self.weights = dict(w_rel=1 / 3, w_lat=1 / 3, w_pow=1 / 3)
        self.trainer: PPOTrainer | None = None
        self.translation: dict | None = None
        self.nas_result: dict | None = None

    # ------------------------------------------------------------------ #
    # environment construction
    # ------------------------------------------------------------------ #
    def _env_config(self, episodes_steps: int | None = None) -> EnvConfig:
        handcrafted = self.cfg.variant == "handcrafted"
        overrides = {}
        if self.cfg.acq_signaling_s is not None:
            overrides["acq_signaling_s"] = self.cfg.acq_signaling_s
        if self.cfg.acq_sync_base_s is not None:
            overrides["acq_sync_base_s"] = self.cfg.acq_sync_base_s
        if self.cfg.seam_penalty_s is not None:
            overrides["seam_penalty_s"] = self.cfg.seam_penalty_s
        if self.cfg.late_risk_tau:
            overrides["late_risk_tau"] = self.cfg.late_risk_tau
            overrides["late_risk_lat"] = self.cfg.late_risk_lat
            overrides["late_risk_weight"] = self.cfg.late_risk_weight
        if self.cfg.dual_homing_latency_ms_per_s:
            overrides["dual_homing_latency_ms_per_s"] = self.cfg.dual_homing_latency_ms_per_s
        if self.cfg.dual_homing_power_per_s:
            overrides["dual_homing_power_per_s"] = self.cfg.dual_homing_power_per_s
        return EnvConfig(
            episode_steps=episodes_steps or self.cfg.episode_steps,
            w_rel=self.weights["w_rel"],
            w_lat=self.weights["w_lat"],
            w_pow=self.weights["w_pow"],
            use_snr_proxy=handcrafted,
            drop_penalty=0.0 if handcrafted else 0.30,
            switch_penalty=0.10,
            **overrides,
        )

    def make_env(self, batch: int, episode_steps: int | None = None, seed: int | None = None) -> HandoverEnv:
        return HandoverEnv(
            self.twin,
            self._env_config(episode_steps),
            batch=batch,
            seed=(self.cfg.seed if seed is None else seed),
        )

    # ------------------------------------------------------------------ #
    # stage 1: forward translation
    # ------------------------------------------------------------------ #
    def translate(self) -> dict:
        variant = self.cfg.variant
        if variant == "handcrafted":
            self.weights = dict(w_rel=0.4, w_lat=0.4, w_pow=0.2)
            self.events.append(dict(event="handcrafted_weights", weights=self.weights))
            return dict(weights=self.weights, attempts=0, escalated=False, context={})
        tr = ForwardTranslator(self.llm, self.kg, self.auditor)
        use_memory = variant not in ("no_memory", "static_llm", "eureka")
        res = tr.translate(self.intent, scope=dict(polar=True, regime="arctic"), seed=self.cfg.seed, use_memory=use_memory)
        self.weights = res.weights
        self.translation = dict(
            weights=res.weights,
            attempts=res.attempts,
            escalated=res.escalated,
            audit=asdict(res.reward),
            context=res.context,
            log=tr.log,
        )
        self.events.append(dict(event="translation", **{k: v for k, v in self.translation.items() if k != "log"}))
        # an intent-first baseline keeps the LLM weights but never learns backwards
        if variant == "static_llm":
            self.cfg.forensics_after = 10**9
        return self.translation

    # ------------------------------------------------------------------ #
    # stage 2: architecture search
    # ------------------------------------------------------------------ #
    def search_architecture(self) -> GraphSpec:
        variant = self.cfg.variant
        if self.cfg.fixed_spec:
            # accept either a bare GraphSpec dict or the wrapper written by
            # scripts/run_nas.py ({"spec": {...}, "nas": {...}, ...})
            raw = self.cfg.fixed_spec
            if isinstance(raw, dict) and isinstance(raw.get("spec"), dict):
                raw = raw["spec"]
            self.spec = GraphSpec.from_dict(raw)
            self.events.append(dict(event="reused_spec", spec=self.spec.to_dict()))
            return self.spec
        if variant in ("fixed_arch", "handcrafted") or self.cfg.nas_generations <= 0:
            self.spec = GraphSpec(kind="gcn", width=64, layers=2, heads=2, pool="mean")
            self.events.append(dict(event="fixed_arch", spec=self.spec.to_dict()))
            return self.spec
        ncfg = NASConfig(
            population=self.cfg.nas_population,
            generations=self.cfg.nas_generations,
            eval_episodes=self.cfg.nas_eval_episodes,
            batch=self.cfg.nas_batch,
            episode_steps=self.cfg.episode_steps,
            seed=self.cfg.seed,
            device=self.cfg.device,
            eval_seeds=self.cfg.nas_eval_seeds,
            deploy_episodes=self.cfg.nas_deploy_episodes,
            bc_episodes=self.cfg.bc_episodes,
            bc_epochs=self.cfg.bc_epochs,
        )
        ev = Evolver(
            self.llm,
            self.make_env,
            ncfg,
            regime_tags=dict(polar=True, sparse_isl=True),
            regime_hint="sparse polar connectivity; prefer graph convolution over attention",
            use_llm=variant not in ("no_nas",),
            inherit=True,
            # the search scores candidates with the translated intent's own metric
            # on the validation split, so the proxy and the deployment report agree
            weights=dict(self.weights),
            split=self.splits.validation,
        )
        res = ev.run()
        self.spec = res["best"].spec
        self.nas_result = dict(
            best=self.spec.to_dict(),
            best_reward=res["best"].reward,
            best_params=res["best"].params,
            front=[dict(spec=p.spec.to_dict(), reward=p.reward, params=p.params, latency_ms=p.latency_ms) for p in res["front"]],
            evaluated=res["evaluated"],
            gpu_s=res["gpu_s"],
            history=res["history"],
            trace=res.get("trace", []),
            regime_stats=res.get("regime_stats", {}),
            table=res.get("table", []),
        )
        self.events.append(dict(event="nas", evaluated=res["evaluated"], best=self.spec.to_dict()))
        return self.spec

    # ------------------------------------------------------------------ #
    # stage 3: policy training with the forensic loop
    # ------------------------------------------------------------------ #
    def _policy_fn(self, trainer: PPOTrainer):
        def fn(obs, x, adj, deterministic=True):
            at, aa, _lp, _v = trainer._act(obs, x, adj, deterministic=deterministic)
            return at, aa

        return fn

    def _monitor(self) -> dict:
        """Deterministic monitoring evaluation used by the KPI trigger."""
        env = self.make_env(batch=32, seed=self.cfg.seed + 991)
        env.reset(t_range=self.splits.indices(self.twin.n_time, "validation", self.cfg.episode_steps))
        pf = self._policy_fn(self.trainer)
        for _ in range(self.cfg.episode_steps):
            x, adj = env.candidate_graph()
            at, aa = pf(env.obs(), x, adj, True)
            env.step(at, aa, shield=self.shield)
        st = env.episode_stats()
        lat = env.site_lat[env.site]
        rows = [
            dict(lat=float(lat[i]), hsr=float(st["hsr"][i]), attempts=int(st["attempts"][i]),
                 successes=int(st["successes"][i]),
                 lat_p95=float(st["lat_p95"][i]) if not np.isnan(st["lat_p95"][i]) else float("nan"),
                 power_mean=float(np.nanmean([p[i] for p in env.pow_hist])) if env.pow_hist else 0.5)
            for i in range(env.batch)
        ]
        arc = [r for r in rows if abs(r["lat"]) > 70]
        hsr_arc = float(np.average([r["hsr"] for r in arc], weights=[max(r["attempts"], 1) for r in arc])) if arc else float("nan")
        return dict(rows=rows, hsr_arctic=hsr_arc, S=satisfaction(rows, self.weights))

    def run(self) -> dict:
        t0 = time.time()
        cfg = self.cfg
        # Inherited knowledge: when this system is handed a non-empty knowledge
        # graph (the multi-intent protocol), the committed constraints are compiled
        # *before* the intent starts, so the monitor and the held-out evaluation
        # already operate under them.  This is what makes "persistent knowledge"
        # a non-zero factor instead of a label.
        if self.kg.active():
            self.shield = compile_constraints(self.kg.active(), self._env_config())
            self.events.append(dict(event="inherited_constraints", n=len(self.kg.active())))
        self.translate()
        self.search_architecture()

        env = self.make_env(cfg.batch, seed=cfg.seed)
        x, adj = env.candidate_graph()
        # Deterministic initialisation: seed immediately before constructing the
        # policy, so the initial weights do not depend on how many random draws
        # the earlier stages (translation sampling, architecture search) consumed.
        # Without this two runs of the same configuration start from different
        # weights and no paired comparison is meaningful.
        import random as _random

        import torch as _torch

        _random.seed(cfg.seed)
        np.random.seed(cfg.seed)
        _torch.manual_seed(cfg.seed)
        policy = build_policy(
            "graph",
            obs_dim=env.obs_dim,
            node_dim=x.shape[-1],
            n_targets=env.K + 1,
            n_advance=env.n_advance,
            spec=self.spec,
        )
        pcfg = PPOConfig(
            total_episodes=cfg.episodes,
            rollout_steps=cfg.rollout_steps,
            minibatch=cfg.minibatch,
            epochs=cfg.epochs,
            lr=cfg.lr,
            ent_coef=cfg.ent_coef,
            max_grad_norm=cfg.max_grad_norm,
            device=cfg.device,
            seed=cfg.seed,
            early_stop_patience=10**9,
            bc_episodes=cfg.bc_episodes,
            bc_epochs=cfg.bc_epochs,
            deterministic=cfg.deterministic,
        )
        self.trainer = PPOTrainer(env, policy, pcfg)
        self.events.append(dict(event="policy", params=policy.param_count(), spec=self.spec.to_dict()))
        if cfg.bc_episodes > 0:
            # warm start from the twin's analytic controller: without it a large
            # share of seeds settle on the degenerate "never hand over" policy,
            # because the environment re-acquires a link by itself
            bc = self.trainer.warm_start()
            self._bc = bc
            self.events.append(dict(event="bc_warm_start", samples=bc.get("samples"),
                                    episodes=bc.get("episodes"),
                                    final_loss=(bc.get("losses") or [None])[-1],
                                    skipped=bc.get("skipped", False)))
        best_val = None
        best_state = None
        best_ep = 0
        self.curve.append(dict(episodes=0, **self._monitor()))

        next_forensic = cfg.forensics_after
        rounds = 0
        trained = 0
        oracle_applied = False
        if cfg.skip_ppo:
            # the prior is the whole policy: keep the cloned weights, evaluate them,
            # and skip training, monitoring, forensics and checkpoint selection
            self.events.append(dict(event="skip_ppo", episodes=0))
            self.best_ep = 0
            return self._final_eval()
        while trained < cfg.episodes:
            chunk = min(cfg.eval_every, cfg.episodes - trained)
            self.trainer.cfg.total_episodes = chunk
            self.trainer.cfg.early_stop_patience = 10**9
            self.trainer.train(log_every=0)
            trained += chunk
            mon = self._monitor()
            self.curve.append(dict(episodes=trained, **mon))
            self.events.append(dict(event="monitor", episodes=trained, hsr_arctic=mon["hsr_arctic"], S=mon["S"]))
            # model selection on the *validation* KPI: PPO on this task has an
            # absorbing "never hand over" optimum, so the final iterate is not
            # necessarily the best one.  The checkpoint is chosen without ever
            # touching the held-out test split.
            kpi_val = mon["S"] if mon["S"] is not None else -1e9
            if best_val is None or kpi_val > best_val:
                best_val = kpi_val
                import copy as _copy
                best_state = {k: v.detach().cpu().clone() for k, v in policy.state_dict().items()}
                best_ep = trained

            if cfg.variant == "oracle" and not oracle_applied:
                # hand-code the domain-expert constraint and use it as a shield
                c = self.kg.commit(
                    atoms=[{"field": "elevation_deg", "cmp": "<=", "value": 15},
                           {"field": "plane_change", "cmp": "==", "value": 1}],
                    effect="min_advance",
                    magnitude=12.0,
                    nl_reading="oracle: cross-plane handover at low elevation needs 12 s advance",
                    provenance=dict(source="domain_expert"),
                    confidence=1.0,
                    scope_tags=dict(polar=True),
                )
                self.shield = compile_constraints(self.kg.active(), env.cfg)
                oracle_applied = True
                self.events.append(dict(event="oracle_constraint", id=c.id))

            kpi = mon["hsr_arctic"]
            if (
                rounds < cfg.max_forensic_rounds
                and trained >= next_forensic
                and cfg.variant not in ("no_forensics", "static_llm", "handcrafted", "oracle")
                and (kpi is None or np.isnan(kpi) or kpi < cfg.theta_rho)
            ):
                rounds += 1
                next_forensic = trained + cfg.forensics_after
                res = self._run_forensics()
                if res is not None and res.get("accepted"):
                    self.shield = compile_constraints(self.kg.active(), env.cfg)
        # final shield from whatever is committed
        if self.kg.active() and self.shield is None:
            self.shield = compile_constraints(self.kg.active(), env.cfg)

        final = self._final_eval()
        out = dict(
            variant=cfg.variant,
            seed=cfg.seed,
            config=asdict(cfg),
            weights=self.weights,
            translation=self.translation,
            spec=self.spec.to_dict() if self.spec else None,
            params=policy.param_count(),
            nas=self.nas_result,
            forensics=self.forensic_results,
            kg=self.kg.stats(),
            curve=[{k: v for k, v in c.items() if k != "rows"} for c in self.curve],
            final=final,
            events=self.events,
            llm=dict(
                **self.llm_log.summary(),
                backend=self.llm.backend.name,
                model=getattr(self.llm.backend, "model", "surrogate"),
                schema_retries=int(getattr(self.llm, "schema_retries", 0)),
            ),
            wall_s=time.time() - t0,
        )
        (self.out / "run_summary.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
        import torch

        torch.save(
            dict(
                policy={k: v.detach().cpu() for k, v in policy.state_dict().items()},
                spec=self.spec.to_dict(),
                obs_norm=self.trainer.obs_norm.state_dict() if self.trainer.obs_norm else None,
                weights=self.weights,
                variant=cfg.variant,
                seed=cfg.seed,
            ),
            self.out / "policy.pt",
        )
        return out

    # ------------------------------------------------------------------ #
    def probe_tau(self, eps: float | None = None, min_abs_lat: float = 70.0) -> float:
        """Active de-censoring sweep: the smallest advance whose late-failure rate
        is inside ``eps`` (PCS, theory Sec. 5).

        A reward, and a reader of the failure log, can only see the requirement
        inside the range of advances that were actually tried.  Forcing the sweep
        is the only way to observe ``T_setup`` beyond that range, which is why a
        shifted physics moves this number while the LLM's narrative does not.

        Because the probe *randomises* the advance, the pooled attempts are an
        unbiased sample of ``P(late | a)``; a one-slope logistic fit then gives a
        monotone estimate, which the raw per-bucket rates are too noisy to give
        (a lucky 140-attempt bucket otherwise picks a threshold that under-protects).
        """
        cfg = self.cfg
        eps = cfg.probe_eps if eps is None else eps
        env = self.make_env(batch=32, seed=cfg.seed + 777)
        trange = self.splits.indices(self.twin.n_time, "test", cfg.episode_steps)
        pf = self._policy_fn(self.trainer)
        rows, ys, xs = [], [], []
        for a in cfg.probe_advances:
            b = int(np.clip(round((a - env.cfg.a_min_s) / env.cfg.a_step_s), 0, env.cfg.a_max_bucket))
            n = late = 0
            for _ in range(max(1, cfg.probe_episodes)):
                env.cfg.traffic_scale = 1.0
                env.reset(t_range=trange)
                for _ in range(cfg.episode_steps):
                    x, adj = env.candidate_graph()
                    at, _aa = pf(env.obs(), x, adj, True)
                    aa = np.full(env.batch, b, dtype=np.int64)
                    env.step(at, aa, record=True)
            for att in env.attempt_log:
                if abs(att["latitude_abs_deg"]) >= min_abs_lat:
                    n += 1
                    is_late = att["cause"] == "late_handover"
                    late += is_late
                    xs.append(float(a))
                    ys.append(1.0 if is_late else 0.0)
            rows.append(dict(advance=float(a), n=n, late_rate=float(late / n) if n else float("nan")))

        tau = self._isotonic_tau(np.asarray(xs), np.asarray(ys), eps) if xs else float(cfg.probe_advances[-1])
        self.events.append(dict(event="probe_tau", tau=tau, eps=eps, rows=rows,
                                n_samples=len(xs), fit="isotonic"))
        return tau

    @staticmethod
    def _isotonic_tau(x: np.ndarray, y: np.ndarray, eps: float) -> float:
        """Isotonic (decreasing) fit of P(late | advance); return the crossing.

        The probe randomises the advance, so the per-advance late rate is an
        unbiased estimate of P(T_setup > a).  Physically that probability can only
        fall with ``a``; the raw rates wobble (a 300-attempt bucket can be lucky),
        which is what made a first-crossing rule under-protect.  Pool-adjacent-
        violators restores the monotonicity before the crossing is read off.
        """
        good = np.isfinite(x) & np.isfinite(y)
        x, y = x[good], y[good]
        if x.size < 50:
            return float(np.max(x)) if x.size else float("nan")
        grid = np.unique(x)
        n = np.array([np.sum(x == a) for a in grid], dtype=float)
        s = np.array([np.sum(y[x == a]) for a in grid], dtype=float)
        # PAVA, decreasing
        vals = (s / np.maximum(n, 1)).tolist()
        wts = n.tolist()
        starts = list(range(len(grid)))
        i = 0
        while i < len(vals) - 1:
            if vals[i] < vals[i + 1]:  # violation of "non-increasing"
                wsum = wts[i] + wts[i + 1]
                vals[i] = (vals[i] * wts[i] + vals[i + 1] * wts[i + 1]) / wsum
                wts[i] = wsum
                del vals[i + 1]
                del wts[i + 1]
                del starts[i + 1]
                if i > 0:
                    i -= 1
            else:
                i += 1
        # expand block values back onto the grid
        fitted = np.empty(len(grid))
        for k, st in enumerate(starts):
            end = starts[k + 1] if k + 1 < len(starts) else len(grid)
            fitted[st:end] = vals[k]
        hit = grid[fitted <= eps]
        return float(hit[0]) if hit.size else float(np.max(x))

    def _run_forensics(self) -> dict | None:
        cfg = self.cfg
        fe = ForensicEngine(
            twin=self.twin,
            env=self.make_env(batch=24, seed=cfg.seed + 17),
            policy_fn=self._policy_fn(self.trainer),
            llm=self.llm,
            kg=self.kg,
            auditor=self.auditor,
            splits=self.splits,
            delta_min=(cfg.delta_min
                       if (cfg.variant != "no_counterfactual" and cfg.counterfactual_gate) else -1.0),
            region="arctic",
            scope_tags=dict(polar=True, regime="arctic", traffic_class="video", density="ref350"),
            magnitude_override=(self.probe_tau() if cfg.probe_calibrated else None),
        )
        res = fe.run(
            max_attempts=1,
            validate_episodes=cfg.validate_episodes,
            test_episodes=cfg.test_episodes,
            discovery_mode=cfg.discovery_mode,
        )
        rec = dict(
            accepted=res.accepted,
            atoms=res.constraint.atoms if res.constraint else None,
            effect=res.constraint.effect if res.constraint else None,
            magnitude=res.constraint.magnitude if res.constraint else None,
            delta_val=res.delta_val,
            delta_test=res.delta_test,
            n_candidates=res.n_candidates,
            discovery_mode=cfg.discovery_mode,
            discovery=next((e for e in res.stage_log if e.get("event") == "discovery"), None),
            stages=res.stage_log,
        )
        self.forensic_results.append(rec)
        self.events.append(dict(event="forensics", accepted=res.accepted, delta_test=res.delta_test))
        return rec

    def _final_eval(self) -> dict:
        """Test-set evaluation: held-out time window, unseen latitudes, x0.5/x2 traffic."""
        rows_all: list[dict] = []
        attempts: list[dict] = []
        splits = {
            "test_base": (self.splits.indices(self.twin.n_time, "test", self.cfg.episode_steps), 1.0),
            "test_half_traffic": (self.splits.indices(self.twin.n_time, "test", self.cfg.episode_steps), 0.5),
            "test_double_traffic": (self.splits.indices(self.twin.n_time, "test", self.cfg.episode_steps), 2.0),
        }
        env = self.make_env(batch=32, seed=self.cfg.seed + 4242)
        pf = self._policy_fn(self.trainer)
        for name, (trange, mult) in splits.items():
            env.cfg.traffic_scale = mult
            rows, att = [], []
            for _ in range(1):
                env.reset(t_range=trange)
                for _s in range(env.cfg.episode_steps):
                    x, adj = env.candidate_graph()
                    at, aa = pf(env.obs(), x, adj, True)
                    env.step(at, aa, shield=self.shield, record=True)
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
                            lat_p95=float(st["lat_p95"][i]) if not np.isnan(st["lat_p95"][i]) else float("nan"),
                            lat_mean=float(st["lat_mean"][i]) if not np.isnan(st["lat_mean"][i]) else float("nan"),
                            power_mean=float(np.nanmean([p[i] for p in env.pow_hist])) if env.pow_hist else 0.5,
                        )
                    )
                att.extend(env.attempt_log)
            rows_all.extend(rows)
            attempts.extend(att)
        env.cfg.traffic_scale = 1.0

        def by_region(rows, pred):
            sel = [r for r in rows if pred(abs(r["lat"]))]
            if not sel:
                return dict(hsr=float("nan"), attempts=0, lat_p95=float("nan"), n=0)
            att = sum(r["attempts"] for r in sel)
            suc = sum(r["successes"] for r in sel)
            lats = [r["lat_p95"] for r in sel if not np.isnan(r["lat_p95"])]
            return dict(
                hsr=suc / att if att else float("nan"),
                attempts=att,
                lat_p95=float(np.median(lats)) if lats else float("nan"),
                n=len(sel),
            )

        bins = {}
        for name, lo, hi in [("0-15", 0, 15), ("15-30", 15, 30), ("30-45", 30, 45), ("45-55", 45, 55),
                             ("55-65", 55, 65), ("65-70", 65, 70), ("70-75", 70, 75), ("75-90", 75, 90)]:
            bins[name] = by_region(rows_all, lambda x, lo=lo, hi=hi: lo <= x < hi)
        by_site = {}
        for site in sorted({r["site"] for r in rows_all}):
            sel = [r for r in rows_all if r["site"] == site]
            att = sum(r["attempts"] for r in sel)
            suc = sum(r["successes"] for r in sel)
            by_site[site] = dict(hsr=suc / att if att else float("nan"), attempts=att,
                                 lat=float(sel[0]["lat"]))
        return dict(
            overall=by_region(rows_all, lambda x: True),
            arctic=by_region(rows_all, lambda x: x > 70),
            subarctic=by_region(rows_all, lambda x: 65 <= x <= 70),
            midlat=by_region(rows_all, lambda x: 30 <= x < 65),
            equatorial=by_region(rows_all, lambda x: x < 30),
            bins=bins,
            by_site=by_site,
            satisfaction=satisfaction(rows_all, self.weights),
            satisfaction_arctic=satisfaction([r for r in rows_all if abs(r["lat"]) > 70], self.weights),
            attempts=attempts,
        )
