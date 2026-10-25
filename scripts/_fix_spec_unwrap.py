from pathlib import Path
p = Path(r"D:\almond-repro\almond\framework\system.py")
s = p.read_text(encoding="utf-8")
old = """        if self.cfg.fixed_spec:
            self.spec = GraphSpec.from_dict(self.cfg.fixed_spec)
            self.events.append(dict(event="reused_spec", spec=self.spec.to_dict()))
            return self.spec"""
new = """        if self.cfg.fixed_spec:
            # accept either a bare GraphSpec dict or the wrapper written by
            # scripts/run_nas.py ({"spec": {...}, "nas": {...}, ...})
            raw = self.cfg.fixed_spec
            if isinstance(raw, dict) and "spec" in raw and isinstance(raw["spec"], dict):
                raw = raw["spec"]
            self.spec = GraphSpec.from_dict(raw)
            self.events.append(dict(event="reused_spec", spec=self.spec.to_dict()))
            return self.spec"""
assert old in s, "fixed_spec branch not found"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("fixed_spec loader now unwraps the NAS wrapper")
