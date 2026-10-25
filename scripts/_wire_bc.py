from pathlib import Path
p = Path(r"D:\almond-repro\almond\framework\system.py")
s = p.read_text(encoding="utf-8")

# expose the stability knobs on the system config
old = "    discovery_mode: str = \"enriched\"  # \"legacy\" reproduces the pre-enrichment sampling"
new = ("    discovery_mode: str = \"enriched\"  # \"legacy\" reproduces the pre-enrichment sampling\n"
       "    bc_episodes: int = 6      # behaviour-cloning warm start (0 disables)\n"
       "    bc_epochs: int = 12\n"
       "    deterministic: bool = True")
assert old in s
s = s.replace(old, new, 1)

# pass them to PPOConfig and warm-start before training
old = """            seed=cfg.seed,
            early_stop_patience=10**9,
        )"""
new = """            seed=cfg.seed,
            early_stop_patience=10**9,
            bc_episodes=cfg.bc_episodes,
            bc_epochs=cfg.bc_epochs,
            deterministic=cfg.deterministic,
        )"""
assert old in s
s = s.replace(old, new, 1)

old = """        self.trainer = PPOTrainer(env, policy, pcfg)
        self.events.append(dict(event="policy", params=policy.param_count(), spec=self.spec.to_dict()))"""
new = """        self.trainer = PPOTrainer(env, policy, pcfg)
        self.events.append(dict(event="policy", params=policy.param_count(), spec=self.spec.to_dict()))
        if cfg.bc_episodes > 0:
            # warm start from the twin's analytic controller: without it a large
            # share of seeds settle on the degenerate "never hand over" policy,
            # because the environment re-acquires a link by itself
            bc = self.trainer.warm_start()
            self.events.append(dict(event="bc_warm_start", **{k: v for k, v in bc.items() if k != "losses"},
                                    final_loss=(bc.get("losses") or [None])[-1]))
            self._bc = bc"""
assert old in s
s = s.replace(old, new, 1)

# record it in the run summary
old = """            spec=self.spec.to_dict(),
            params=policy.param_count(),"""
new = """            spec=self.spec.to_dict(),
            params=policy.param_count(),
            bc_warm_start=len(getattr(self, "_bc", {}).get("losses") or []),"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("warm start wired into the system")
