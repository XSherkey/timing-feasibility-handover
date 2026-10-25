from pathlib import Path
p = Path(r"D:\almond-repro\almond\llm\prompts.py")
s = p.read_text(encoding="utf-8")
old = """    return dict(system=system, user=user)"""
new = """    # the templates are plain strings (not f-strings), so the JSON examples carry
    # doubled braces; a real model should see ordinary JSON braces
    user = user.replace("{{", "{").replace("}}", "}")
    return dict(system=system, user=user)"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("prompt braces normalised")
