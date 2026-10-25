"""Instrument the builder's table branch temporarily to see whether Table V's rows reach it."""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "build_paper_docx.js"
t = p.read_text(encoding="utf-8")
old = """  if (line.trim().startsWith("|")) {
    const tbl = [];"""
new = """  if (line.trim().startsWith("|")) {
    if (process.env.DSH_DOCX_DEBUG) console.error(`[table] line ${i}: ${line.trim().slice(0, 60)}`);
    const tbl = [];"""
if t.count(old) != 1:
    raise SystemExit("branch not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("instrumented")
