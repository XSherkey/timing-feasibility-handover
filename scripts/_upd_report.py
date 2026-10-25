from pathlib import Path
p = Path(r"D:\almond-repro\docs\REPRODUCTION_REPORT.md")
s = p.read_text(encoding="utf-8")
old = """| Region | `t_setup` median | p90 | pathless targets |
|---|---|---|---|
| Arctic (>70° N) | **12.3 s** | 15.8 s | 4–27 % |
| Mid-latitude (30–65°) | **5.4 s** | 9.7 s | ~0 % |

That 2.3× asymmetry reproduces the manuscript's claim that about 10–12 s of preparation is needed in the Arctic while a few seconds suffice elsewhere."""
new = """| Region | `t_setup` p50 | p90 | P(t_setup <= 6 s) | P(<= 12 s) |
|---|---|---|---|---|
| Arctic (>70° N) | **10.0 s** | 15.7 s | 0.15 | **0.55** |
| Mid-latitude (30–65°) | **4.2 s** | 5.5 s | 0.91 | 0.97 |

A 2.4x asymmetry, which reproduces the manuscript's claim that about 10-12 s of
preparation is needed in the Arctic while a few seconds suffice elsewhere.  Note
what the two probabilities imply: a policy that always uses the protocol's
minimum 6 s lead keeps only **15 %** of its Arctic handovers, and one that uses
**12 s** keeps **55 %** -- the draft's 55 % figure is exactly the marginal-lead
regime.  Only a lead of about 16 s, or same-plane/route-aware target selection,
reaches the 86-92 % seen in the converged runs."""
assert old in s
s = s.replace(old, new, 1)
old2 = """The one place the 55 % figure does reappear is *under-trained or collapsed* runs, which is precisely the regime the draft's "25 training episodes" observation describes."""
new2 = """The 55 % figure does reappear, but at a different place than the draft puts it: it is the handover success of a **marginal 12 s preparation lead** in the Arctic (P(t_setup <= 12 s) = 0.55), not the plateau of a trained baseline.  A 6 s lead gives 15 %, a 16 s lead or plane-aware targeting gives ~90 %."""
assert old2 in s
s = s.replace(old2, new2, 1)
p.write_text(s, encoding="utf-8")
print("report updated with the verified acquisition-time table")
