import re
from pathlib import Path

t = Path("results/routeA_r2/commands.log").read_text(encoding="utf-8")
print("acq values:", sorted(set(re.findall(r"--acq-signaling (\S+)", t))))
print("epochs:", sorted(set(re.findall(r"--epoch-doy (\S+)", t))))
print("leads:", sorted(set(re.findall(r"--lead (\S+)", t))))
print("policies:", sorted(set(re.findall(r"--policy (\S+)", t))))
