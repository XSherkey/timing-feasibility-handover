from pathlib import Path

kg = Path("almond/framework/kg.py")
t = kg.read_text(encoding="utf-8")
old = '    "cap_advance",'
new = '    "cap_advance",\n    "cap_advance_vis",'
print("kg hits:", t.count(old))
t = t.replace(old, new, 1)
kg.write_text(t, encoding="utf-8")

sh = Path("almond/framework/shield.py")
s = sh.read_text(encoding="utf-8")
old2 = '        elif c.effect in ("power_cap", "cap_advance"):'
new2 = '''        elif c.effect == "cap_advance_vis":
            # cap the lead at (remaining visibility - magnitude) on the predicate rows
            si, t = env.site, env.t_idx
            srv = np.maximum(env.serving, 0)
            trem = env.trem[si, srv, t]
            cap_s = np.clip(trem - float(c.magnitude), env_cfg.a_min_s, 26.0)
            cap_bucket = np.rint(np.clip((cap_s - env_cfg.a_min_s) / env_cfg.a_step_s,
                                         0, env_cfg.a_max_bucket)).astype(np.int64)
            aa = np.where(mask & np.isfinite(trem), np.minimum(aa, cap_bucket), aa)
        elif c.effect in ("power_cap", "cap_advance"):'''
print("shield hits:", s.count(old2))
s = s.replace(old2, new2, 1)
sh.write_text(s, encoding="utf-8")
print("added cap_advance_vis")
