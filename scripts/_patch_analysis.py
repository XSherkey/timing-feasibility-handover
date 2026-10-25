"""One-off patcher: add convergence-rate / median reporting to the analysis."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "scripts" / "analyse_campaign.py"
s = p.read_text(encoding="utf-8")

old1 = '        entry["params"] = summarise(params).as_dict()\n'
new1 = '''        entry["params"] = summarise(params).as_dict()
        # PPO on this task has an absorbing passive-policy optimum, so the seed
        # distribution is bimodal.  Report the convergence rate and the median
        # explicitly rather than hiding it inside a mean.
        arc_vals = [r["final"]["arctic"]["hsr"] * 100 for r in rs]
        conv = [v for v in arc_vals if v >= 80.0]
        entry["converged_rate"] = len(conv) / max(len(arc_vals), 1)
        entry["arctic_converged_median"] = float(np.median(conv)) if conv else float("nan")
        entry["arctic_median"] = float(np.median(arc_vals)) if arc_vals else float("nan")
        if arc_vals:
            q75, q25 = np.percentile(arc_vals, [75, 25])
            entry["arctic_iqr"] = float(q75 - q25)
        else:
            entry["arctic_iqr"] = float("nan")
'''
assert old1 in s
s = s.replace(old1, new1, 1)

old2 = '''    hdr = f"{'method':<26}" + "".join(f"{r + ' HSR%':>14}" for r in REGIONS) + f"{'S':>10}{'params':>9}"'''
new2 = '''    hdr = (
        f"{'method':<26}"
        + "".join(f"{r + ' HSR%':>14}" for r in REGIONS)
        + f"{'S':>10}{'params':>9}{'conv':>7}{'arc.med':>9}{'arc.IQR':>9}"
    )'''
assert old2 in s
s = s.replace(old2, new2, 1)

old3 = '''        row += f"{e['satisfaction']['mean']:10.1f}{e['params']['mean']:9.0f}"'''
new3 = '''        row += (
            f"{e['satisfaction']['mean']:10.1f}{e['params']['mean']:9.0f}"
            f"{e['converged_rate'] * 100:6.0f}%{e['arctic_median']:9.1f}{e['arctic_iqr']:9.1f}"
        )'''
assert old3 in s
s = s.replace(old3, new3, 1)

p.write_text(s, encoding="utf-8")
print("patched", p)
