from pathlib import Path

p = Path(__file__).resolve().parent / "_r15_figs.py"
t = p.read_text(encoding="utf-8")
old = '    ax.set_ylim(40, 102)\n    ax.set_ylabel("polar handover success (%)")\n    # legend outside the axes'
new = ('    lo6 = min(min(n - d for n, d in zip(nom, nom_sd)), min(q - d for q, d in zip(p2, p2_sd)))\n'
       '    ax.set_ylim(int(np.floor(lo6 - 2)), 102)   # keep every whisker inside the axes\n'
       '    ax.set_ylabel("polar handover success (%)")\n    # legend outside the axes')
print("found:", t.count(old))
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("patched")
