"""R17 part 2: the [33] replacement with the exact source wording."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

OLD = 'ITU-R, "Characteristics of inter-satellite links," Recommendation, 2022.'
NEW = ('R. Radhakrishnan, W. W. Edmonson, F. Afghah, R. M. Rodriguez-Osorio, F. Pinto, and S. C. Burleigh, '
       '"Survey of inter-satellite communication for small satellite systems: Physical layer to network layer '
       'view," *IEEE Commun. Surveys Tuts.*, vol. 18, no. 4, pp. 2442–2473, 2016.')

for name in ("paper_en.md", "paper_zh.md"):
    p = D / name
    t = p.read_text(encoding="utf-8")
    print(name, "count", t.count(OLD))
    if t.count(OLD) == 1:
        t = t.replace(OLD, NEW, 1)
        p.write_text(t, encoding="utf-8")
        print(name, "[33] replaced")
