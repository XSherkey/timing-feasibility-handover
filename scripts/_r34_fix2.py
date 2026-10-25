"""R34 part 3: the last two inconsistencies - probe budget wording and the bare Table D1 reference."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = p.read_text(encoding="utf-8")
done = []


def rep(old, new, label):
    global t
    n = t.count(old)
    if n != 1:
        print("  MISS", label, n)
        return
    t = t.replace(old, new, 1)
    done.append(label)


# 1. one budget pair everywhere
rep("run-to-run sd of the estimate is 2.45 s at 2 episodes/advance and 1.10 s at 16, with bootstrap intervals returned "
    "per probe run.",
    "run-to-run sd of the estimate is 2.45 s at 2 episodes/advance and 1.10 s at the largest budget we ran, 16 "
    "episodes/advance, with bootstrap intervals returned per probe run.", "stats budget wording")

rep("*More episodes do not buy accuracy.* Doubling the probe budget from 2 to 8 episodes per advance reduces run-to-run "
    "sd from 2.45 s to 1.10 s but *lowers* the estimate from the 16 s grid point toward 14 s,",
    "*More episodes do not buy accuracy.* Raising the probe budget from 2 to 16 episodes per advance reduces run-to-run "
    "sd from 2.45 s to 1.10 s but *lowers* the estimate from the 16 s grid point toward 14 s,", "more-episodes paragraph")

# 2. the cost sentence: keep 8 episodes but label it as an intermediate budget
rep("(1.83% at 8 episodes per advance)", "(1.83% at an intermediate budget of 8 episodes per advance)",
    "cost sentence")

# 3. Table D1 -> Tables D1A and D1B
rep("are given in Appendix D (Table D1), together with the KM curve's per-quantile event/censoring support.",
    "are given in Appendix D (Tables D1A and D1B), together with the KM curve's per-quantile event/censoring support.",
    "Table D1 -> D1A/D1B")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", done)
