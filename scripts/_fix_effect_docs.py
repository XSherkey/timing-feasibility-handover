from pathlib import Path

p = Path(r"D:\almond-repro\almond\llm\surrogate.py")
s = p.read_text(encoding="utf-8")
old = '''EFFECT_GRAMMAR = [
    dict(name="min_advance", params=dict(seconds=[6, 8, 10, 12, 14, 16])),
    dict(name="forbid_unrouted_target", params={}),
    dict(name="prefer_same_plane", params={}),
    dict(name="power_cap", params=dict(max_lead_s=[6, 9, 12])),
    dict(name="buffer_drain", params=dict(max_buffer=[0.5, 0.7, 0.85])),
    dict(name="cap_advance", params=dict(max_lead_s=[6, 8, 10, 12, 14])),
]'''
new = '''EFFECT_GRAMMAR = [
    dict(name="min_advance", params=dict(seconds=[6, 8, 10, 12, 14, 16]),
         remedy="removes late_handover: the requested lead is shorter than the acquisition time"),
    dict(name="forbid_unrouted_target", params={},
         remedy="removes no_route: the selected candidate has no feeder path"),
    dict(name="prefer_same_plane", params={},
         remedy="removes cross-plane fragility above the polar seam"),
    dict(name="power_cap", params=dict(max_lead_s=[6, 9, 12]),
         remedy="bounds dual-homing time when the battery is low"),
    dict(name="buffer_drain", params=dict(max_buffer=[0.5, 0.7, 0.85]),
         remedy="removes feeder congestion: prefer the least loaded candidate"),
    dict(name="cap_advance", params=dict(max_lead_s=[6, 8, 10, 12, 14]),
         remedy="removes window_exceeded: the requested lead exceeds the target's remaining visibility"),
]'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

p = Path(r"D:\almond-repro\almond\llm\prompts.py")
s = p.read_text(encoding="utf-8")
old = """Propose at most three rules. Rules must be a conjunction of at most two atoms of the form
<telemetry_field> <cmp> <value>, plus one effect from the grammar. Output JSON only:"""
new = """Each narrative may report a gateway error code. Choose the effect whose "remedy" matches that
code, and use the telemetry values in the narratives to pick the threshold: late_handover ->
min_advance, no_route -> forbid_unrouted_target, window_exceeded -> cap_advance, congestion ->
buffer_drain, cross-plane fragility -> prefer_same_plane.

Propose at most three rules. Rules must be a conjunction of at most two atoms of the form
<telemetry_field> <cmp> <value>, plus one effect from the grammar. Output JSON only:"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("effect remedies documented in the prompt")
