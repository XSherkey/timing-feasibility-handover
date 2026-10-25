"""v12: n=10 cross-intent + the annotation study (Table IX) in the English manuscript."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "almond-repro"
D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
ci = json.loads((ROOT / "results" / "routeA_r3" / "cross_intent" / "summary.json").read_text(encoding="utf-8"))
llm = json.loads((ROOT / "results" / "routeA_r3" / "llm_proposals" / "summary.json").read_text(encoding="utf-8"))
ag = json.loads((ROOT / "results" / "routeA_r3" / "llm_proposals" / "agreement.json").read_text(encoding="utf-8"))
pi = ci["per_intent"]
done = []


def rep(old: str, new: str, label: str) -> None:
    global t
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected 1, found {n}")
    t = t.replace(old, new, 1)
    done.append(label)


# ---- Table V at n = 10 ---------------------------------------------------
start = t.find("**Table V. Cross-intent transfer")
end = t.find("\n\n", t.find("|", start))
rows = ["| knowledge graph | intent 0 reliability | intent 1 latency | intent 2 power | intent 3 balanced | n |",
        "|---|---|---|---|---|---|",
        "| shared (inherited) | %.2f | **%.2f** | **%.2f** | **%.2f** | %d |" % (
            pi["reliability_first"]["shared"]["mean"], pi["latency_first"]["shared"]["mean"],
            pi["power_first"]["shared"]["mean"], pi["balanced"]["shared"]["mean"], len(ci["seeds"])),
        "| fresh per intent | %.2f | %.2f | %.2f | %.2f | %d |" % (
            pi["reliability_first"]["fresh"]["mean"], pi["latency_first"]["fresh"]["mean"],
            pi["power_first"]["fresh"]["mean"], pi["balanced"]["fresh"]["mean"], len(ci["seeds"])),
        "| transfer gain (pp) | +%.2f | +%.2f | +%.2f | +%.2f | |" % (
            pi["reliability_first"]["pair"]["mean_diff"], pi["latency_first"]["pair"]["mean_diff"],
            pi["power_first"]["pair"]["mean_diff"], pi["balanced"]["pair"]["mean_diff"])]
t = t[:start] + ("**Table V. Cross-intent transfer (polar HSR at |lat| ≥ 70°, mean over %d policy seeds; "
                 "%d of them committed a rule at intent 0, and the table reports all seeds, so seeds "
                 "without a committed rule contribute identically to both arms).**\n\n"
                 % (len(ci["seeds"]), ci["committed"]["n"]) + "\n".join(rows) + "\n") + t[end:]
done.append("table5")

# ---- VI-F prose ----------------------------------------------------------
s = t.find("### F. One constraint, four intents")
e = t.find("### G.", s)
NEWF = """### F. One constraint, four intents

A constraint mined under a reliability-first intent is inherited by three later intents that are
**forbidden to mine**: latency-first, power-first and balanced. Under a shared knowledge graph the
three reach 90.21%, 89.99% and 90.75%; with a fresh graph per intent they reach 72.19%, 68.22% and
69.85%. The gain is +18.02, +21.77 and +20.91 pp, exact two-sided Wilcoxon p = 0.0039 on ten training
seeds (Table V), and the first intent—which is identical in both arms—differs by 0.03 pp (p = 1.00),
as it must. The effect is large because feasibility is intent-independent: whatever the next
objective, the constraint removes the same failure class.

Two qualifications belong with the number. *First, discovery does not always commit.* On one of the
ten seeds the discovery pipeline returned no committed rule (the gate admitted nothing), and on that
seed both arms fall to 72–76%; we report it rather than drop it, because it is the honest failure rate
of an automatic pipeline (9/10 commits). *Second,* the seeds on which nothing was committed contribute
identically to both arms, so they dilute the contrast rather than bias it.

"""
t = t[:s] + NEWF + t[e:]
done.append("VI-F")

# ---- VI-L: annotation results -------------------------------------------
old = ("All twenty P1 responses are schema-valid and every one is judged semantically valid by an independent\n"
       "annotator, so the inter-annotator coefficient is *undefined* rather than high: with zero disagreement\n"
       "and zero variance, Cohen's κ has a zero denominator. We report the raw agreement (20/20) and note the\n"
       "degeneracy instead of quoting a κ that would not mean anything.")
new = ("""All twenty P1 responses are schema-valid: every predicate uses declared telemetry fields and an
executable effect, so the mechanical rubric accepts 20/20 (Table IX). Syntactic validity is not
deployability, however, and the two annotations that ask the operational question disagree with the
mechanical one and with each other. A domain annotator, working from the written rubric (Appendix E),
accepts 4 of the 20 as deployable as proposed and returns 16 for revision, typically because the scope
drops part of the evidence (a `plane_change` or elevation guard that covers half the failures) or
because a global scope would raise the lead where nothing fails. A second annotator—asked only whether
an operator could deploy the rule as-is—accepts 2 of 20. Cohen's κ between the two operational
annotations is 0.23 on 0.80 raw agreement, and κ against the mechanical rubric is 0 because that rubric
has no variance. The useful reading is the gap, not any single rate: **every** proposal is well formed,
**one in five** is deployable without revision, and the two annotators agree on only four of the five
items where they differ. This is precisely the division of labour the pipeline assumes—the model is a
proposal generator, and the audit gate, not the model, decides what may touch the network.

**Table IX. Annotation of the twenty proposals.** Mechanical: predicate uses declared fields and an
executable effect. Deployable (author): rule could be deployed as proposed. Deployable (second
annotator): independent operational judgement. κ is computed on the binary "deployable" outcome.

| rater | accepts | rate | κ vs author |
|---|---|---|---|
| mechanical (schema) | 20/20 | 1.00 | 0.00 |
| author, operational rubric | 4/20 | 0.20 | -- |
| second annotator (operational) | 2/20 | 0.10 | 0.23 |
| raw agreement, author vs second | -- | 0.80 | -- |
""")
rep(old, new, "VI-L-annotation")
rep("and when the same narratives are\nre-sent with every acquisition time shifted by +2 s,",
    "and when the same narratives are re-sent with every acquisition time shifted by +2 s,",
    "flow-fix")
p.write_text(t, encoding="utf-8")
print("applied:", done)
