from r3lib import evaluate, arctic, late_share

r = evaluate("smoke_rule", run="results/campaign_1023/almond_seed0",
             rule="min_advance:18@latitude_abs_deg>=68")
print("test  arctic", round(arctic(r), 2), "late", round(late_share(r), 2), "attempts", r["arctic"][1])
r2 = evaluate("smoke_val", run="results/campaign_1023/almond_seed0",
              rule="min_advance:18@latitude_abs_deg>=68", window="validation")
print("val   arctic", round(arctic(r2), 2), "attempts", r2["arctic"][1])
