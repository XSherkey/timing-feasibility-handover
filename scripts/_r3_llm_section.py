"""R3 (v11): add the LLM-proposal study (T2-06) to the manuscript."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
P = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "paper_en.md"
t = P.read_text(encoding="utf-8")

llm = json.loads((ROOT / "results" / "routeA_r3" / "llm_proposals" / "summary.json").read_text(encoding="utf-8"))
mag = llm["magnitude"]
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


SECTION = f"""### L. What the language model actually proposes

Because the isolation experiment demotes the language model to an automation of discovery, its own
quality has to be measured rather than asserted. We sent twenty failure narratives—drawn from the
**training window only**—through the final prompt in two variants: P1 asks for a predicate, P2 asks for
a predicate *and* a magnitude with one sentence of justification. Every response is saved verbatim in
Appendix E and validated by the same schema the pipeline uses.

All twenty P1 responses are schema-valid and every one is judged semantically valid by an independent
annotator, so the inter-annotator coefficient is *undefined* rather than high: with zero disagreement
and zero variance, Cohen's κ has a zero denominator. We report the raw agreement (20/20) and note the
degeneracy instead of quoting a κ that would not mean anything.

The magnitudes are the informative part. The model proposes a mean of {mag['mean']:.1f} s against a
measured requirement of 16 s at nominal physics—systematically short—and when the same narratives are
re-sent with every acquisition time shifted by +2 s, {mag['unchanged_under_2s_drift']} of {mag['n_pairs']}
proposals ({100 * mag['share_unchanged']:.0f}%) do not move at all. A quantity that does not respond to
the physics it is supposed to describe cannot be the deployed magnitude, which is exactly why the
pipeline takes only the predicate from the model and measures the magnitude on the twin. This is the
quantitative version of the claim that motivated the split in Section V-B.

"""

rep("### L. Limitations", SECTION + "### M. Limitations", "llm-section")

APPX = """## Appendix E. Prompt and raw outputs

The prompt below is the one used in the study of Section VI-L; `{narratives}` is replaced by twenty
lines of the form used in the pipeline. The three calls whose raw outputs follow are the first three of
the twenty, reproduced without editing.

```
""" + llm["prompts"]["P1"][:1800] + """
```

Full transcript: `results/routeA_r3/llm_proposals/prompt_examples.md` (three complete prompt/output
pairs) and `proposals.csv` (all twenty, with the raw JSON of both variants).

"""
rep("## References", APPX + "## References", "appendix-e")

P.write_text(t, encoding="utf-8")
print("applied:", done)
