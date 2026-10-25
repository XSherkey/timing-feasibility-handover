from pathlib import Path
p = Path(r"D:\almond-repro\scripts\run_llm_stability.py")
s = p.read_text(encoding="utf-8")
old = """    ap.add_argument("--backend", default="auto", choices=["auto", "surrogate"])"""
new = """    ap.add_argument("--backend", default="auto", choices=["auto", "surrogate"])
    ap.add_argument("--types", default="all", help="comma-separated subset of call types")"""
assert old in s
s = s.replace(old, new, 1)

old = """    out = {}
    for ct in TYPES:
        n_rep = args.repeats if ct in SAFETY else args.other_repeats
        group = max(1, n_rep // 4)"""
new = """    types = TYPES if args.types == "all" else [t.strip() for t in args.types.split(",") if t.strip()]
    out = {}
    for ct in types:
        n_rep = args.repeats if ct in SAFETY else args.other_repeats
        group = max(2, n_rep // 4)
        retries_before = client.schema_retries"""
assert old in s
s = s.replace(old, new, 1)

old = """        out[ct] = dict(
            exact_match=float(np.mean(exact)) if exact else float("nan"),
            semantic_equivalence=float(np.mean(sem)) if sem else float("nan"),
            schema_failure_rate=float(1.0 - n_ok / max(n_calls, 1)),
            retry_rate=float(client.schema_retries / max(n_calls, 1)),"""
new = """        retries_here = client.schema_retries - retries_before
        out[ct] = dict(
            exact_match=float(np.mean(exact)) if exact else float("nan"),
            semantic_equivalence=float(np.mean(sem)) if sem else float("nan"),
            schema_failure_rate=float(1.0 - n_ok / max(n_calls, 1)),
            retry_rate=float(retries_here / max(n_calls, 1)),
            retries=retries_here,"""
assert old in s
s = s.replace(old, new, 1)

old = """    print(f"\\n{'call type':<24}{'exact':>8}{'semantic':>10}{'schema-fail':>13}{'retry':>8}")
    for ct in TYPES:"""
new = """    print(f"\\n{'call type':<24}{'exact':>8}{'semantic':>10}{'schema-fail':>13}{'retry':>8}")
    for ct in types:"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("stability script: per-type retries, --types filter, group>=2")
