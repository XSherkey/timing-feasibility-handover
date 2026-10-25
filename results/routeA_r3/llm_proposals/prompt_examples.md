# Prompt appendix (verbatim, first three calls)

## Call 1

**P1 raw output**
```json
{"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":">=","value":60},{"field":"handover_advance_s","cmp":"<","value":10}],"magnitude":10}
```

**P2 raw output**
```json
{"effect":"min_advance","atoms":[{"field":"handover_advance_s","cmp":"<","value":12},{"field":"latitude_abs_deg","cmp":">=","value":60}],"magnitude":12,"magnitude_justification":"Observed acquisitions took 8.0-9.8 s while a 6 s advance failed, so 12 s provides margin above the worst-case acquisition time for reliable polar handovers."}
```

## Call 2

**P1 raw output**
```json
{"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":">=","value":64},{"field":"handover_advance_s","cmp":"<","value":10}],"magnitude":10}
```

**P2 raw output**
```json
{"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":">=","value":60}],"magnitude":12,"magnitude_justification":"Polar failures show acquisition latencies up to 9.9 s against a 6 s advance, so enforcing a 12 s lead provides margin before the visibility window can be lost."}
```

## Call 3

**P1 raw output**
```json
{"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":">=","value":64},{"field":"handover_advance_s","cmp":"<=","value":6}],"magnitude":10}
```

**P2 raw output**
```json
{"effect":"min_advance","atoms":[{"field":"latitude_abs_deg","cmp":">=","value":60}],"magnitude":10,"magnitude_justification":"High-latitude/polar handovers in the failure set had acquisition times up to 8.9 s, so a 10 s minimum lead prevents the observed 6 s advance from being exhausted before acquisition completes."}
```