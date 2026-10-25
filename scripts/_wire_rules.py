from pathlib import Path
p = Path(r"D:\almond-repro\scripts\fill_docx.py")
s = p.read_text(encoding="utf-8")
start = s.index("def build_rules(tbd: dict)")
end = s.index("def fill_doc(src: Path")
new_fn = '''def build_rules(tbd: dict) -> list[tuple[str, list[str]]]:
    """Delegate to scripts/tbd_rules.py so the mapping stays reviewable in one place."""
    import sys
    from pathlib import Path as _P

    sys.path.insert(0, str(_P(__file__).resolve().parent))
    from tbd_rules import build_rules as _build

    return _build(tbd, lambda d, k, default="n/a": (d.get(k) or {}).get("value", default))


'''
s = s[:start] + new_fn + s[end:]
p.write_text(s, encoding="utf-8")
print("fill_docx now delegates the rules")
