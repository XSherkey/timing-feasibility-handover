"""R12 part 9: exchange the two caption paragraphs so the gate figure is 7 and the dose figure is 6."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"


def swap_captions(name: str, gate_marker: str, dose_marker: str, gate_new: str, dose_new: str) -> None:
    p = D / name
    t = p.read_text(encoding="utf-8")
    ig = t.find(gate_marker)
    id_ = t.find(dose_marker)
    if ig < 0 or id_ < 0:
        raise SystemExit(f"{name}: markers not found ({ig}, {id_})")
    ag = t.find("\n\n", ig)
    ad = t.find("\n\n", id_)
    gate_block = t[ig:ag]
    dose_block = t[id_:ad]
    # rebuild with the wanted numbers
    gate_block = gate_block.replace(gate_marker, gate_new, 1)
    dose_block = dose_block.replace(dose_marker, dose_new, 1)
    first, second = (ig, id_) if ig < id_ else (id_, ig)
    blocks = (gate_block, dose_block) if ig < id_ else (dose_block, gate_block)
    new = blocks[0] + t[min(ag, ad):max(ag, ad)][:0] + "\n\n" + blocks[1]
    # replace the whole span from first marker to the end of the later block
    start = first
    end = max(ag, ad)
    t = t[:start] + new + t[end:]
    p.write_text(t, encoding="utf-8")
    print(name, "captions exchanged")


swap_captions("paper_en.md", "**Fig. 7.** The audit gate", "**Fig. 6.** Reward injection", "**Fig. 7.** The audit gate", "**Fig. 6.** Reward injection")
