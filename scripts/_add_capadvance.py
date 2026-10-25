from pathlib import Path

# 1) vocabulary: a sixth executable effect that can express "do not ask for more
#    lead time than the target will still be visible" (the window_exceeded class)
p = Path(r"D:\almond-repro\almond\llm\kg_fields.py")
s = p.read_text(encoding="utf-8")
old = """        "power_cap",
        "buffer_drain","""
new = """        "power_cap",
        "buffer_drain",
        "cap_advance","""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# 2) shield: same clamp as power_cap, but reachable under a visibility predicate
p = Path(r"D:\almond-repro\almond\framework\shield.py")
s = p.read_text(encoding="utf-8")
old = """        elif c.effect == "power_cap":"""
new = """        elif c.effect in ("power_cap", "cap_advance"):"""
assert old in s
s = s.replace(old, new, 1)
old = """``power_cap``
    clamp the requested lead time to ``magnitude`` seconds (bounded
    dual-homing) when the battery state is low;"""
new = """``power_cap``
    clamp the requested lead time to ``magnitude`` seconds (bounded
    dual-homing) when the battery state is low;
``cap_advance``
    clamp the requested lead time to ``magnitude`` seconds so that it stays below
    the target's remaining visibility (the remedy for the ``window_exceeded``
    failure class, which none of the other five effects can express);"""
assert old in s
s = s.replace(old, new, 1)
s = s.replace("runs inside the environment step.  Five effects are executable:",
              "runs inside the environment step.  Six effects are executable:", 1)
p.write_text(s, encoding="utf-8")

# 3) grammar shown to the model
p = Path(r"D:\almond-repro\almond\llm\surrogate.py")
s = p.read_text(encoding="utf-8")
old = """    dict(name="buffer_drain", params=dict(max_buffer=[0.5, 0.7, 0.85])),
]"""
new = """    dict(name="buffer_drain", params=dict(max_buffer=[0.5, 0.7, 0.85])),
    dict(name="cap_advance", params=dict(max_lead_s=[6, 8, 10, 12, 14])),
]"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("cap_advance added to grammar, shield and vocabulary")
