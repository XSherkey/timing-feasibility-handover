from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for rel, seed_expr in (("experiments/run_window_case2.py", "0"),
                       ("experiments/run_closed_loop.py", "policy_seed")):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    early = ('    from almond.policies.ppo import PPOConfig, PPOTrainer\n'
             f'    trainer = PPOTrainer(pol, PPOConfig(device="cpu", seed={seed_expr}, deterministic=True))\n')
    n = t.count(early)
    print(rel, "early block:", n)
    t = t.replace(early, "", 1)
    anchor = "    pol.eval()\n"
    add = ("    pol.eval()\n"
           "    from almond.policies.ppo import PPOConfig, PPOTrainer\n"
           f"    trainer = PPOTrainer(pol, PPOConfig(device=\"cpu\", seed={seed_expr}, deterministic=True))\n")
    print(rel, "anchor:", t.count(anchor))
    t = t.replace(anchor, add, 1)
    p.write_text(t, encoding="utf-8")
print("done")
