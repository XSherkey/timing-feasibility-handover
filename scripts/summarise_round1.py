"""Summarise the round-1 theory experiments: PCS, penalty-vs-shield, decomposition."""
import glob
import json
import os
import statistics as st


def load(root, method="almond"):
    out = {}
    for p in sorted(glob.glob(os.path.join(r"results", root, f"{method}_seed*", "run_summary.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if not d.get("ok"):
            continue
        seed = int(os.path.basename(os.path.dirname(p)).rsplit("_seed", 1)[1])
        out[seed] = dict(arctic=d["final"]["arctic"]["hsr"] * 100,
                         mid=d["final"]["midlat"]["hsr"] * 100,
                         s=d["final"]["satisfaction"])
    return out


def line(name, d):
    if not d:
        print(f"{name:<26} (no runs)")
        return
    v = [x["arctic"] for x in d.values()]
    m = [x["mid"] for x in d.values()]
    s = [x["s"] for x in d.values()]
    print(f"{name:<26} n={len(v):2d}  arctic {st.mean(v):5.1f} +- {st.stdev(v) if len(v) > 1 else 0:4.1f}"
          f"  mid {st.mean(m):5.1f}  S {st.mean(s):5.1f}")


print("=" * 78)
print("A. Probe-Calibrated Shield (PCS) vs the LLM's own magnitude")
print("=" * 78)
base_ref = load("campaign_1023")
pcs_ref = load("campaign_pcs_ref")
base_sig = load("campaign_sig32")
pcs_sig = load("campaign_pcs_sig32")
line("ref: LLM magnitude (16s)", base_ref)
line("ref: PCS", pcs_ref)
line("+2s: LLM magnitude (16s)", base_sig)
line("+2s: PCS", pcs_sig)
print()
for s in sorted(set(pcs_sig) & set(base_sig)):
    print(f"  +2s seed {s}: LLM {base_sig[s]['arctic']:.1f} -> PCS {pcs_sig[s]['arctic']:.1f} "
          f"({pcs_sig[s]['arctic'] - base_sig[s]['arctic']:+.1f} pp)")
for s in sorted(set(pcs_ref) & set(base_ref)):
    print(f"  ref  seed {s}: LLM {base_ref[s]['arctic']:.1f} -> PCS {pcs_ref[s]['arctic']:.1f} "
          f"({pcs_ref[s]['arctic'] - base_ref[s]['arctic']:+.1f} pp)")

print()
print("=" * 78)
print("B. penalty in the reward vs shield at decision time (same knowledge tau=16@68)")
print("=" * 78)
line("no forensics, no shield", load("campaign_clean", "no_forensics"))
line("reward penalty (lambda=1.0)", load("campaign_penalty", "no_forensics"))
line("decision shield (ALMOND)", base_ref)

print()
print("=" * 78)
print("C. per-seed: none / penalty / shield")
print("=" * 78)
none = load("campaign_clean", "no_forensics")
pen = load("campaign_penalty", "no_forensics")
print(f"{'seed':>4}{'none':>9}{'penalty':>9}{'shield':>9}")
for s in sorted(set(none) & set(pen) & set(base_ref)):
    print(f"{s:>4}{none[s]['arctic']:>8.1f}%{pen[s]['arctic']:>8.1f}%{base_ref[s]['arctic']:>8.1f}%")
