import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

MD_ABS = """Handover reliability in low-Earth-orbit constellations is usually framed as a
reinforcement-learning problem, yet the differences between learned controllers disappear once one
timing constraint is applied. On a 350-satellite digital twin driven by real two-line elements we
show that most of the gap between a tuned RL baseline and an "LLM-assisted" system is not learning:
adding a single 16 s handover-advance constraint to frozen policies raises polar success from 67.5%
to 92.4% (sd 0.1 pp) across ten independent policies. The reason is structural: the failure log
reveals the acquisition requirement only from above, so it is right-censored and no reward-based
objective can identify a bound it never observes. Scanning nine reward penalties from 0 to 64 peaks
at 84.4% and then degrades, while the decision shield dominates that family on both reliability and
intent satisfaction. We therefore design the constraint itself: a language model proposes only the
predicate, a Kaplan-Meier analysis recovers the censored requirement, a probe on the deployed policy
locates the threshold, and a 2 s cost-asymmetric margin converts a +/-2 s identifiability limit into
a safety property. The shield holds 94.0% nominally and 93.3% after 4.4 s of acquisition drift, where
a tuned constant falls from 94.0% to 87.7%. A counterfactual audit gate is worth +42.9 pp (92.1%
versus 49.2%) while leaving the model's own good proposal intact (+0.4 pp). We also report where it
stops: at nominal physics a tuned constant matches us, and in a feeder-constrained twin the shield
saturates at 79.4% because route failures become binding."""

TEX_ABS = r"""Handover reliability in low-Earth-orbit constellations is usually framed as a reinforcement-learning problem, yet the differences between learned controllers disappear once one timing constraint is applied. On a 350-satellite digital twin driven by real two-line elements we show that most of the gap between a tuned RL baseline and an ``LLM-assisted'' system is not learning: adding a single 16\,s handover-advance constraint to frozen policies raises polar success from 67.5\% to 92.4\% (sd 0.1\,pp) across ten independent policies. The reason is structural: the failure log reveals the acquisition requirement only from above, so it is right-censored and no reward-based objective can identify a bound it never observes. Scanning nine reward penalties from 0 to 64 peaks at 84.4\% and then degrades, while the decision shield dominates that family on both reliability and intent satisfaction. We therefore design the constraint itself: a language model proposes only the predicate, a Kaplan--Meier analysis recovers the censored requirement, a probe on the deployed policy locates the threshold, and a 2\,s cost-asymmetric margin converts a $\pm2$\,s identifiability limit into a safety property. The shield holds 94.0\% nominally and 93.3\% after 4.4\,s of acquisition drift, where a tuned constant falls from 94.0\% to 87.7\%. A counterfactual audit gate is worth $+42.9$\,pp (92.1\% versus 49.2\%) while leaving the model's own good proposal intact ($+0.4$\,pp). We also report where it stops: at nominal physics a tuned constant matches us, and in a feeder-constrained twin the shield saturates at 79.4\% because route failures become binding."""

md = (D / "main.md").read_text(encoding="utf-8")
md = re.sub(r"(## Abstract\n).*?(\n---)", r"\1\n" + MD_ABS.replace("\\", "\\\\") + r"\2", md, count=1, flags=re.S)
(D / "main.md").write_text(md, encoding="utf-8")

tex = (D / "main.tex").read_text(encoding="utf-8")
tex = re.sub(r"(\\begin\{abstract\}\n).*?(\n\\end\{abstract\})", lambda m: m.group(1) + TEX_ABS + m.group(2),
             tex, count=1, flags=re.S)
(D / "main.tex").write_text(tex, encoding="utf-8")

m = re.search(r"## Abstract\n(.*?)\n---", md, re.S)
print("md abstract words:", len(m.group(1).split()))
m2 = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
print("tex abstract words:", len(m2.group(1).split()))
