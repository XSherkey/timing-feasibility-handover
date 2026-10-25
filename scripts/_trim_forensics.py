from pathlib import Path
p = Path(r"D:\almond-repro\almond\framework\system.py")
s = p.read_text(encoding="utf-8")
for old, new in (
    ("    validate_episodes: int = 3", "    validate_episodes: int = 2"),
    ("    test_episodes: int = 4", "    test_episodes: int = 2"),
    ("    max_forensic_rounds: int = 3", "    max_forensic_rounds: int = 1"),
):
    assert old in s, old
    s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("forensic replay budget trimmed: validate 2, test 2, max 1 round")
