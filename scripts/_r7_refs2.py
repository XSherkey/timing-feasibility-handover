"""R7 (v9): complete the two references whose details are verifiable from the titles."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

PAIRS = [
    ('[15] A. Ray, J. Achiam, and D. Amodei, "Benchmarking safe exploration in deep reinforcement learning," 2019.',
     '[15] A. Ray, J. Achiam, and D. Amodei, "Benchmarking safe exploration in deep reinforcement learning," OpenAI Tech. Rep., 2019.'),
    ('[38] W. K. Hastings, "Monte Carlo sampling methods using Markov chains," 1970.',
     '[38] W. K. Hastings, "Monte Carlo sampling methods using Markov chains and their applications," *Biometrika*, vol. 57, no. 1, pp. 97–109, 1970.'),
]

for name in ("paper_en.md", "paper_zh.md"):
    p = D / name
    t = p.read_text(encoding="utf-8")
    n = 0
    for old, new in PAIRS:
        if t.count(old) == 1:
            t = t.replace(old, new, 1)
            n += 1
    p.write_text(t, encoding="utf-8")
    print(name, "refs completed:", n)
