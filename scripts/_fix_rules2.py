from pathlib import Path
p = Path(r"D:\almond-repro\scripts\tbd_rules.py")
s = p.read_text(encoding="utf-8")

old_oracle = '''        ("oracle value", [
            f"Oracle-PPO reaches {h('oracle')} Arctic HSR, below ALMOND's {h('almond')} and close to "
            f"PPO-MLP's {h('ppomlp')}; medians are 88.9% for ALMOND against 69.7% for PPO-MLP, and "
            f"ALMOND converges in 4 of 6 seeds versus 4 of 10"
        ]),'''
new_oracle = '''        ("oracle value", [
            f"Oracle-PPO reaches {h('oracle')} Arctic HSR against ALMOND's {h('almond')} and "
            f"PPO-MLP's {h('ppomlp')}. With ten seeds the ordering of ALMOND, Oracle-PPO and "
            f"Static-LLM is not resolvable: each of them failed to converge in seven of ten seeds, "
            f"and the architecture control in the reproduction report (same variant, searched "
            f"architecture swapped for the fixed GCN) gives 55.9% versus 54.5%, i.e. the spread is "
            f"convergence luck rather than the discovered architecture"
        ]),'''
assert old_oracle in s
s = s.replace(old_oracle, new_oracle, 1)

old_conv = '''        ("ALMOND converges roughly three times faster", [
            f"[MEASURED, NOT CONFIRMED] median episodes to 90% of each method's own asymptote: "
            f"ALMOND {ep['almond']} vs PPO-MLP {ep['ppomlp']}",
            "the confidence interval of the ratio is unbounded because the two medians fall in a "
            "different order than assumed: PPO-MLP reaches 90% of its (much lower) asymptote sooner",
            "no significant paired test is possible: runs are not bit-reproducible across "
            "processes, so comparisons are unpaired over independent seeds",
            f"fixed target S >= 75: PPO-MLP 1080 episodes, Unseeded-EvoNAS 3200, Static-LLM 3360, "
            f"ALMOND 4000",
            f"no resolvable Delta S: ALMOND test-set satisfaction {tbd.get('satisfaction.almond', {}).get('value', 'n/a')} "
            f"versus Static-LLM {tbd.get('satisfaction.static_llm', {}).get('value', 'n/a')} and "
            f"PPO-MLP {tbd.get('satisfaction.ppomlp', {}).get('value', 'n/a')} is a real ordering but "
            f"the ablation is swamped by run-to-run variance",
        ]),'''
new_conv = '''        ("ALMOND converges roughly three times faster", [
            f"[MEASURED, NOT CONFIRMED] median episodes to 90% of each method's own asymptote: "
            f"ALMOND {ep['almond']} versus PPO-MLP {ep['ppomlp']}",
            "the ratio's confidence interval is unbounded because the medians fall in the opposite "
            "order to the claim: PPO-MLP reaches 90% of its (much lower) asymptote sooner",
            "no paired test is possible: runs are not bit-reproducible across processes, so every "
            "comparison here is unpaired over independent seeds",
            "fixed absolute target S >= 75: PPO-MLP 1080 episodes, Unseeded-EvoNAS 3200, "
            "Static-LLM 3360, ALMOND 3360",
            f"test-set satisfaction: ALMOND {tbd.get('satisfaction.almond', {}).get('value', 'n/a')} "
            f"versus Static-LLM {tbd.get('satisfaction.static_llm', {}).get('value', 'n/a')} and "
            f"PPO-MLP {tbd.get('satisfaction.ppomlp', {}).get('value', 'n/a')} — the differences are "
            f"inside the seed spread",
        ]),'''
assert old_conv in s
s = s.replace(old_conv, new_conv, 1)

old_nas = '''            f"[MEASURED, NOT CONFIRMED] at an equal budget of {n_ev} architectures the "
            f"LLM-seeded search reached reward 1.417 in {n_wall} and the unseeded control 1.400, "
            f"i.e. the seeding is marginally better but does not reduce cost",'''
new_nas = '''            f"[MEASURED, NOT CONFIRMED] over five seeds per arm at an equal budget of {n_ev} "
            f"architectures, the LLM-seeded search reached best reward 1.146 +- 0.206 (median 1.07) "
            f"and the unseeded control 1.170 +- 0.189 (median 1.04): no advantage and no cost "
            f"reduction",'''
assert old_nas in s
s = s.replace(old_nas, new_nas, 1)
p.write_text(s, encoding="utf-8")
print("rules updated for the 10-seed results")
