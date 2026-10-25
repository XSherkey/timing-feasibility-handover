from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for rel, seed_expr in (("experiments/run_window_case2.py", "0"),
                       ("experiments/run_closed_loop.py", "policy_seed")):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    old = f"    trainer = PPOTrainer(pol, PPOConfig(device=\"cpu\", seed={seed_expr}, deterministic=True))\n"
    new = (f"    trainer = PPOTrainer(env, pol, PPOConfig(device=\"cpu\", seed={seed_expr}, deterministic=True))\n"
           "    if trainer.obs_norm is not None and ck.get(\"obs_norm\"):\n"
           "        trainer.obs_norm.load_state_dict(ck[\"obs_norm\"])\n")
    print(rel, t.count(old))
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
print("fixed trainer args")
