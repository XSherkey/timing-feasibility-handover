"""R27 part 7: give the acquisition requirement its formula and constants (review 18 item 7 / review 20 item 2)."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

anchor = "**Decision process.**"
i = t.find(anchor)
if i < 0:
    raise SystemExit("decision-process paragraph not found")

FORMULA = """**Acquisition requirement.** The requirement is not an exogenous constant; the twin computes it per
attempt from five physically motivated terms plus a plane-change penalty,

```
T_z = t_sig + (t_sync + c_dop |nu_dot|) + c_hop h
      + c_low [1 - sin(el)/sin(el_ref)]_+ + t_slot [P/s - 1]_+
      + penalty(seam, plane),                                        (5)
```

with `t_sig = 1.2 s` (handover signalling round trip), `t_sync = 0.6 s` and `c_dop = 1.0e-4 s/(Hz/s)`
(carrier and symbol synchronisation, which degrades with Doppler rate `nu_dot`), `c_hop = 0.1 s` per
re-programmed ISL hop `h`, `c_low = 0.6 s` with `el_ref = 25 deg` (grazing-elevation acquisition),
`t_slot = 1.8 s` and `s = 3` feeder slots against the `P` satellites visible from the target's best
gateway, and `penalty = 6.0 s` when the target sits above the 70 deg seam and the handover changes
plane, `0.3 s` for a cross-plane change elsewhere and `0` within a plane. The feeder term is why the
polar band needs the longest lead: a polar gateway sees an order of magnitude more satellites, so
`P/s` is large exactly there. Every constant is in the sealed configuration and is varied
independently in the sensitivity arms of Table L1 (seam and feeder capacity). The requirement is thus
a modelled quantity, not a measured one—which is what bounds the claims to this twin.

"""
t = t[:i] + FORMULA + t[i:]
t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("formula inserted; words:", len(re.findall(r"[A-Za-z0-9']+", t)))
