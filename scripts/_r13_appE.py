"""R14 part 3: inline the three raw prompt/output pairs into both appendices."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

PAIRS_EN = """
**Raw outputs, first three calls (verbatim JSON, P1 = predicate only, P2 = predicate + magnitude).**

```
call 1  P1  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":60},
             {"field":"handover_advance_s","cmp":"lt","value":10}],"magnitude":10}
        P2  {"effect":"min_advance","atoms":[{"field":"handover_advance_s","cmp":"lt","value":12},
             {"field":"latitude_abs_deg","cmp":"ge","value":60}],"magnitude":12,
             "magnitude_justification":"Observed acquisitions took 8.0-9.8 s while a 6 s advance
             failed, so 12 s provides margin above the worst-case acquisition time."}

call 2  P1  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":64},
             {"field":"handover_advance_s","cmp":"lt","value":10}],"magnitude":10}
        P2  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":60}],
             "magnitude":12,"magnitude_justification":"Polar failures show acquisition latencies
             up to 9.9 s against a 6 s advance, so enforcing a 12 s lead provides margin."}

call 3  P1  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":64},
             {"field":"handover_advance_s","cmp":"le","value":6}],"magnitude":10}
        P2  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":60}],
             "magnitude":10,"magnitude_justification":"High-latitude handovers in the failure set
             had acquisition times up to 8.9 s, so a 10 s minimum lead prevents the observed 6 s
             advance from being exhausted before acquisition completes."}
```

Three observations that the statistics of Section VI-L quantify: the predicate is stable across calls
(the same polar band, the same latitude field), the magnitude is not (10, 12, 10 s against a 16 s
requirement), and the recomputed json is stable across the two variants for the predicate but not for
the magnitude.
"""

PAIRS_ZH = """
**原始输出，前三次调用（逐字 JSON；P1 = 只给谓词，P2 = 谓词 + 幅值）。**

```
调用 1  P1  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":60},
             {"field":"handover_advance_s","cmp":"lt","value":10}],"magnitude":10}
        P2  {"effect":"min_advance","atoms":[{"field":"handover_advance_s","cmp":"lt","value":12},
             {"field":"latitude_abs_deg","cmp":"ge","value":60}],"magnitude":12,
             "magnitude_justification":"实测建链 8.0–9.8 s，而 6 s 提前量失败，故 12 s 提供余量。"}

调用 2  P1  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":64},
             {"field":"handover_advance_s","cmp":"lt","value":10}],"magnitude":10}
        P2  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":60}],
             "magnitude":12,"magnitude_justification":"极区失败案例的建链时延达 9.9 s，
             相对 6 s 提前量，强制 12 s 可留出余量。"}

调用 3  P1  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":64},
             {"field":"handover_advance_s","cmp":"le","value":6}],"magnitude":10}
        P2  {"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":"ge","value":60}],
             "magnitude":10,"magnitude_justification":"高纬失败案例的建链时长达 8.9 s，
             10 s 最小提前量可避免 6 s 提前量在建链完成前被耗尽。"}
```

三点观察（第六节 L 用统计量化）：谓词在三次调用间稳定（同为极区带、同一纬度字段）；
幅值不稳定（10、12、10 s，而需求是 16 s）；JSON 语法全部合法。
"""

for name, block, anchor in (("paper_en.md", PAIRS_EN, "Full transcript:"),
                            ("paper_zh.md", PAIRS_ZH, "完整记录：")):
    p = D / name
    t = p.read_text(encoding="utf-8")
    i = t.find(anchor)
    if i < 0:
        print("  anchor not found in", name)
        continue
    t = t[:i] + block.strip() + "\n\n" + t[i:]
    p.write_text(t, encoding="utf-8")
    print(name, "pairs inlined")
