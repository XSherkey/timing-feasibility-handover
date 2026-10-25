import sys, numpy as np
sys.path.insert(0, r"D:\almond-repro")
from almond.twin.twin import DigitalTwin, TwinConfig
from almond.twin.env import HandoverEnv, EnvConfig
twin = DigitalTwin(TwinConfig(tag="ref", horizon_s=12*3600)).build(verbose=False)
env = HandoverEnv(twin, EnvConfig(episode_steps=1), batch=8, seed=0)
rng = np.random.default_rng(0)
rows = []
for _ in range(4000):
    si = env.user_idx[rng.integers(0, len(env.user_idx))]
    t = int(rng.integers(20, twin.n_time - 20))
    cand = twin["cand_idx"][si, t]
    valid = [c for c in cand if c >= 0]
    if len(valid) < 2: continue
    srv, tgt = int(valid[0]), int(valid[1])
    el = np.array([twin["el"][si, tgt, t]], dtype=float)
    dop = np.array([twin["doprate"][si, tgt, t]], dtype=float)
    hop = np.array([twin["hop"][tgt, t]], dtype=float)
    fp = np.array([twin["feed_press"][tgt, t]], dtype=float)
    from almond.twin.geometry import link_acquisition_time_s
    base = link_acquisition_time_s(np.deg2rad(el), dop, np.maximum(hop, 0), fp,
                                   feeder_slots=twin.cfg.feeder_queue_slots, t_slot_s=1.8,
                                   t_signaling_s=1.2, t_sync_base_s=0.6, doppler_coeff_s=1e-4,
                                   hop_coeff_s=0.10, low_el_coeff_s=0.6)[0]
    same = float(np.dot(twin["nrm"][srv, t], twin["nrm"][tgt, t])) > 0.995
    above = abs(float(twin["lat_sat"][tgt, t])) > 70
    pen = 0.0 if same else (6.0 if above else 0.3)
    rows.append((abs(twin.sites[si].lat_deg), base + pen, same))
r = np.array([(a, b, c) for a, b, c in rows])
arc = r[r[:,0] > 70]; mid = r[(r[:,0] >= 30) & (r[:,0] < 65)]
for name, x in (("arctic>70", arc), ("midlat 30-65", mid)):
    print(f"{name:<14} n={len(x):5d}  t_setup p50={np.median(x[:,1]):5.1f}s  p90={np.percentile(x[:,1],90):5.1f}s  same_plane={100*np.mean(x[:,2]):4.1f}%")
print("P(t_setup<=6 | arctic) = %.3f   P(<=12 | arctic) = %.3f" % (
    np.mean(arc[:,1] <= 6), np.mean(arc[:,1] <= 12)))
print("P(t_setup<=6 | midlat) = %.3f   P(<=12 | midlat) = %.3f" % (
    np.mean(mid[:,1] <= 6), np.mean(mid[:,1] <= 12)))
