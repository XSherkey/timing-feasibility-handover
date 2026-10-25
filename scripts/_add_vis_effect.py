from pathlib import Path

# 1) vocabulary
p = Path(r"D:\almond-repro\almond\llm\kg_fields.py")
s = p.read_text(encoding="utf-8")
s = s.replace('        "cap_advance",', '        "cap_advance",\n        "prefer_long_visibility",', 1)
p.write_text(s, encoding="utf-8")

# 2) shield: pick the candidate with the most remaining visibility
p = Path(r"D:\almond-repro\almond\framework\shield.py")
s = p.read_text(encoding="utf-8")
old = '''def compile_constraint(c: Constraint, env_cfg):'''
new = '''def _best_visibility(env, idx) -> np.ndarray:
    """Index (1..K) of the candidate with the longest remaining visibility."""
    idx = np.asarray(idx, dtype=np.int64)
    si = env.site[idx]
    t = env.t_idx[idx]
    cand = env.cand_idx[si, t]
    cc = np.maximum(cand, 0)
    trem = env.trem[si[:, None], cc, t[:, None]]
    hop = env.hop[cc, t[:, None]]
    ok = (hop >= 0) & (cand >= 0)
    score = np.where(ok, trem, -1.0)
    best = np.argmax(score, axis=1)
    found = np.take_along_axis(score, best[:, None], axis=1)[:, 0] > 0
    return np.where(found, best + 1, 0).astype(np.int64)


def compile_constraint(c: Constraint, env_cfg):'''
assert old in s
s = s.replace(old, new, 1)

old = '''        elif c.effect == "buffer_drain":'''
new = '''        elif c.effect == "prefer_long_visibility":
            need = mask & (ta > 0)
            if np.any(need):
                idx = np.flatnonzero(need)
                repl = _best_visibility(env, idx)
                ta[idx] = np.where(repl > 0, repl, ta[idx])
        elif c.effect == "buffer_drain":'''
assert old in s
s = s.replace(old, new, 1)

old = """``cap_advance``
    clamp the requested lead time to ``magnitude`` seconds so that it stays below
    the target's remaining visibility (the remedy for the ``window_exceeded``
    failure class, which none of the other five effects can express);"""
new = """``cap_advance``
    clamp the requested lead time to ``magnitude`` seconds (bounded dual-homing
    under a visibility predicate);
``prefer_long_visibility``
    replace the commanded target by the routed candidate with the longest
    remaining visibility - the remedy for the ``window_exceeded`` class, where the
    requested lead is longer than the target will stay visible;"""
assert old in s
s = s.replace(old, new, 1)
s = s.replace("Six effects are executable:", "Seven effects are executable:", 1)
p.write_text(s, encoding="utf-8")

# 3) grammar
p = Path(r"D:\almond-repro\almond\llm\surrogate.py")
s = p.read_text(encoding="utf-8")
old = '''    dict(name="cap_advance", params=dict(max_lead_s=[6, 8, 10, 12, 14]),
         remedy="removes window_exceeded: the requested lead exceeds the target's remaining visibility"),
]'''
new = '''    dict(name="cap_advance", params=dict(max_lead_s=[6, 8, 10, 12, 14]),
         remedy="bounds the lead so it cannot exceed a short window"),
    dict(name="prefer_long_visibility", params={},
         remedy="removes window_exceeded: pick the routed candidate that stays visible longest"),
]'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# 4) prompt remedy mapping
p = Path(r"D:\almond-repro\almond\llm\prompts.py")
s = p.read_text(encoding="utf-8")
s = s.replace("window_exceeded -> cap_advance", "window_exceeded -> prefer_long_visibility", 1)
p.write_text(s, encoding="utf-8")
print("prefer_long_visibility added")
