from pathlib import Path
p = Path(r"D:\almond-repro\docs\REPRODUCTION_REPORT.md")
s = p.read_text(encoding="utf-8")
anchor = "### 4.8 Architecture search"
table9 = """### 4.8 Threshold sensitivity (Table 9)

Forensic trigger `theta_rho` swept over {75, 80, 85, 90, 95} % and the validation
gate `Delta_min` over {2, 5, 10} %, 3 seeds each, 2400 training episodes per seed
(mean monitored Arctic KPI 75.4 %).  Ground truth for recall is the set of three
constraint classes the twin can express (timing, routing, plane discipline);
precision is operational (an accepted rule is a true positive if it still gains
>= 5 pp Arctic HSR on the held-out test set).

| theta_rho | runs firing | accepted | precision | recall | mean Delta_test |
|---|---|---|---|---|---|
| 75 % | 1 | 1 | 100 % | 33 % | +5.3 pp |
| 80 % | 2 | 1 | 100 % | 33 % | +5.3 pp |
| 85 % | 2 | 1 | 100 % | 33 % | +5.3 pp |
| 90 % | 3 | 1 | 100 % | 33 % | +5.3 pp |
| 95 % | 3 | 1 | 100 % | 33 % | +5.3 pp |

| Delta_min | runs | accepted | precision | recall | mean Delta_test |
|---|---|---|---|---|---|
| 2 % | 3 | 1 | 100 % | 33 % | +5.3 pp |
| 5 % | 3 | 1 | 100 % | 33 % | +5.3 pp |
| 10 % | 3 | 0 | n/a | 0 % | n/a |

A higher trigger fires more often but changes nothing downstream: the auditor and
the replay gate, not the trigger, decide acceptance.  The gate behaves as designed
-- the one rule that replicates gains only 5.3 pp, so a 10 % gate correctly
rejects it and a 2 % gate accepts the same rule with no false positive.  Recall
is capped at 33 % because only one of the three expressible rule classes was ever
mined in this twin.

### 4.9 Architecture search"""
assert anchor in s
s = s.replace(anchor, table9, 1)
p.write_text(s, encoding="utf-8")
print("Table 9 added to the report")
