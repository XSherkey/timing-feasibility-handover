from pathlib import Path
p = Path(r"D:\almond-repro\almond\framework\forensics.py")
s = p.read_text(encoding="utf-8")
old = """        if best is None or not best.accepted:
            return best or ForensicResult(None, None, 0.0, 0.0, False, self.stage_log)"""
new = """        if best is None or not best.accepted:
            return best or ForensicResult(
                None, None, 0.0, 0.0, False, self.stage_log, self.n_candidates
            )"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("n_candidates now reported on the no-commit path")
