"""R27 part 6: shrink figures slightly, park the governance subsection, trim the system model."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
supp_path = D / "supplementary" / "supp_en.md"
t = p.read_text(encoding="utf-8")
supp = supp_path.read_text(encoding="utf-8")
done = []

# 1. figures a touch smaller
b = D / "build_paper_docx.js"
js = b.read_text(encoding="utf-8")
old = "const widthTwips = IEEE ? COL_WIDTH - 620 : 5800;"
new = "const widthTwips = IEEE ? COL_WIDTH - 900 : 5800;"
if old in js:
    js = js.replace(old, new, 1)
    b.write_text(js, encoding="utf-8")
    done.append("figures 2.7 in")

# 2. governance subsection -> supplement
i = t.find("### M. Deployment and governance")
j = t.find("### N. What the language model actually proposes")
if i > 0 and j > i:
    block = t[i:j].strip()
    t = t[:i] + ("### M. Deployment and governance\n\nThe three services (discovery, calibration and admission, "
                 "deployment) and the rollback rule are specified in Appendix N of the supplementary material; the "
                 "point that matters for the claims above is that the shield reads the committed constraint and "
                 "writes nothing.\n\n") + t[j:]
    supp = supp.rstrip() + "\n\n## Appendix N. Deployment and governance\n\n" + block + "\n"
    done.append("governance -> supp")

# 3. trim the constellation paragraph
i = t.find("**Constellation and links.**")
j = t.find("\n\n", i)
if i > 0 and j > i:
    NEW = ("**Constellation and links.** The twin models 350 satellites in three Walker shells—polar (200 sats, "
           "10 × 20, 89.5°, 700 km), mid-latitude (120, 6 × 20, 53°, 550 km) and equatorial (30, 2 × 15, 5°, 600 km)—"
           "propagated with SGP4 over 12 h at 10 s resolution. Link budgets cover free-space loss with "
           "elevation-dependent atmospheric attenuation at 20 GHz over 250 MHz channels, Doppler, inter-satellite "
           "links (≤ 5200 km), eclipse and gateway feeder capacity; a polar gateway sees an order of magnitude more "
           "candidates than a mid-latitude one, which is why the 70° seam carries a penalty. Sites draw Poisson "
           "session arrivals with video and emergency mixes.")
    t = t[:i] + NEW + t[j:]
    done.append("constellation trimmed")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
supp_path.write_text(supp, encoding="utf-8")
print("edits:", done, "| words:", len(re.findall(r"[A-Za-z0-9']+", t)))
