"""Convert the Chinese reproduction report to DOCX.

Reuses the author's own ``md2docx_local.py`` converter (same fonts, table style
and heading hierarchy as the rest of the submission folder) without modifying
it, so the review copy looks like the other documents in EAAI/.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EAAI = Path(
    r"D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写"
    r"\From Human Intent to In-Orbit Action\EAAI"
)


def load_converter():
    spec = importlib.util.spec_from_file_location("md2docx_local", EAAI / "md2docx_local.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.convert


def clean_markdown(text: str) -> str:
    """Strip constructs the shared converter does not consume.

    The converter handles ``#`` headings, tables, bullet lists, fenced code and
    ``**bold**``; it does not consume horizontal rules or single-asterisk
    italics, which would otherwise appear literally in the review copy.
    """
    out = []
    for line in text.split("\n"):
        if re.fullmatch(r"\s*-{3,}\s*", line):
            out.append("")
            continue
        # *italic* -> plain (avoid touching ** bold ** which the converter handles)
        line = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", line)
        out.append(line)
    return "\n".join(out)


def main() -> int:
    src = ROOT / "docs" / "REPRODUCTION_REPORT_中文.md"
    dst = EAAI / "复现结果" / "复现报告_中文.docx"
    dst.parent.mkdir(parents=True, exist_ok=True)
    cleaned = clean_markdown(src.read_text(encoding="utf-8"))
    tmp = Path(tempfile.gettempdir()) / "almond_report_cn_clean.md"
    tmp.write_text(cleaned, encoding="utf-8")
    convert = load_converter()
    convert(str(tmp), str(dst), title_east="SimHei")
    print("wrote", dst, dst.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

