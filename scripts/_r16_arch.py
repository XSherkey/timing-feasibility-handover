"""R16: rebuild Fig. 8 (architecture) with pad-exact arrows, a connected failure-log box and clear stage labels."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本" / "figures"
plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "savefig.dpi": 300})
PAD = 0.06


def fig_architecture() -> None:
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    rects = {}

    def box(name, x, y, w, h, label, fc="#dce9f5", fs=6.6):
        rects[name] = (x, y, w, h)
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad={PAD}",
                                    fc=fc, ec="#33506e", lw=0.8))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs)

    def edge(name, side):
        x, y, w, h = rects[name]
        return {
            "l": (x - PAD, y + h / 2), "r": (x + w + PAD, y + h / 2),
            "t": (x + w / 2, y + h + PAD), "b": (x + w / 2, y - PAD),
        }[side]

    def arrow(p1, p2, style="-|>", ls="-"):
        # shrink 0 and endpoints already on the padded border: nothing pokes in or leaves a gap
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, lw=0.8, color="#33506e",
                                     linestyle=ls, mutation_scale=8, shrinkA=0, shrinkB=0))

    # ---- discovery row (training window) --------------------------------
    box("intent", 0.15, 3.6, 1.55, 0.9, "operator intent")
    box("llm", 2.05, 3.6, 1.75, 0.9, "LLM predicate\nservice")
    box("store", 4.15, 3.6, 1.55, 0.9, "training-log\nstore")
    box("km", 6.05, 3.6, 1.55, 0.9, "KM diagnostic\n(not deployed)")

    # ---- calibration and admission row (validation window) --------------
    box("fail", 0.15, 2.2, 1.55, 0.9, "failure log\ninjection")
    box("probe", 2.05, 2.2, 1.75, 0.9, "probe runner\n(validation only)")
    box("gate", 4.15, 2.2, 1.55, 0.9, "audit gate\n(validation replay)")
    box("kg", 6.05, 2.2, 1.75, 0.9, "versioned KG\n(commit / rollback)")

    # ---- deployment column ----------------------------------------------
    box("shield", 8.15, 2.2, 1.7, 0.9, "runtime shield\n(decision time)")
    box("ctrl", 8.15, 0.9, 1.7, 0.9, "network controller\n(PPO policy, frozen)")

    # ---- monitoring row ---------------------------------------------------
    box("mon", 0.15, 0.9, 3.65, 0.9,
        "monitoring: late_handover / no_route /\nwindow / drift trigger", fc="#f6e7d5", fs=6.2)

    # ---- arrows, all between padded borders ------------------------------
    arrow(edge("intent", "r"), edge("llm", "l"))
    arrow(edge("llm", "r"), edge("store", "l"))
    arrow(edge("store", "r"), edge("km", "l"))

    # LLM predicate service feeds the probe runner (predicate comes from the model)
    ax.add_patch(FancyArrowPatch((2.25, rects["llm"][1] - PAD), (2.25, rects["probe"][1] + 0.9 + PAD),
                                 arrowstyle="-|>", lw=0.8, color="#33506e", mutation_scale=8,
                                 shrinkA=0, shrinkB=0))
    # failure-log injection -> probe runner  (this box was previously unconnected)
    arrow(edge("fail", "r"), edge("probe", "l"))
    arrow(edge("probe", "r"), edge("gate", "l"))
    arrow(edge("gate", "r"), edge("kg", "l"))
    arrow(edge("kg", "r"), edge("shield", "l"))
    ax.add_patch(FancyArrowPatch((9.0, rects["shield"][1] - PAD), (9.0, rects["ctrl"][1] + 0.9 + PAD),
                                 arrowstyle="-|>", lw=0.8, color="#33506e", mutation_scale=8,
                                 shrinkA=0, shrinkB=0))

    # KM diagnostic feeds the audit gate (diagnostic only, dotted)
    ax.add_patch(FancyArrowPatch((6.30, rects["km"][1] - PAD), (5.60, rects["gate"][1] + 0.9 + PAD),
                                 arrowstyle="-|>", lw=0.8, color="#33506e", linestyle=":",
                                 mutation_scale=8, shrinkA=0, shrinkB=0))
    # runtime telemetry feeds monitoring (dashed), monitoring feeds the log injection (dashed)
    arrow(edge("ctrl", "l"), (rects["mon"][0] + 3.65 + PAD, 1.35), style="-|>", ls="--")
    ax.add_patch(FancyArrowPatch((0.9, rects["mon"][1] + 0.9 + PAD), (0.9, rects["fail"][1] - PAD),
                                 arrowstyle="-|>", lw=0.8, color="#33506e", linestyle="--",
                                 mutation_scale=8, shrinkA=0, shrinkB=0))

    # ---- stage labels, each attached to its own row ----------------------
    ax.text(0.15, 4.62, "discovery — training window only", fontsize=6.4, ha="left",
            style="italic", color="#33506e")
    ax.text(2.45, 3.30, "calibration and admission — validation window only", fontsize=6.4,
            ha="left", style="italic", color="#33506e")
    ax.text(9.0, 3.30, "deployment", fontsize=6.4, ha="center", style="italic", color="#33506e")
    ax.text(0.15, 0.70, "monitoring and drift detection — feeds the log, never the weights",
            fontsize=6.0, ha="left", style="italic", color="#7a5a2e")

    fig.tight_layout()
    fig.savefig(OUT / "fig8_architecture.png")
    fig.savefig(OUT / "fig8_architecture.pdf")
    plt.close(fig)
    print("fig8 rebuilt")


if __name__ == "__main__":
    fig_architecture()
