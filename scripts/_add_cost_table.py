import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

# --- Markdown ---
md_path = D / "main.md"
md = md_path.read_text(encoding="utf-8")
old = """*Cost.* One probe is 11 advances x 2 episodes = 22 episodes, about 0.46% of the 9600-episode
training budget (1.83% at 8 episodes per advance) [A21]. Probing is cheap; the currency it lacks is
identifiability, not compute."""
new = """*Cost.* One probe is 11 advances x 2 episodes = 22 episodes, about 0.23% of the 9600-episode
training budget (0.92% at 8 episodes per advance), Table VI [A21]. Probing is cheap; the currency it
lacks is identifiability, not compute.

**Table VI. Probe cost per calibration.**
| configuration | episodes | env steps | share of a 9600-episode training run |
|---|---|---|---|
| probe, 2 episodes/advance | 22 | 5,280 | 0.23% |
| probe, 8 episodes/advance | 88 | 21,120 | 0.92% |"""
assert old in md
md = md.replace(old, new, 1)
md_path.write_text(md, encoding="utf-8")

# --- LaTeX ---
tex_path = D / "main.tex"
tex = tex_path.read_text(encoding="utf-8")
old_tex = r"""\emph{Cost.} One probe is 11 advances $\times$ 2 episodes $=22$ episodes, about 0.46\% of the 9600-episode training budget (1.83\% at 8 episodes per advance). Probing is cheap; the currency it lacks is identifiability, not compute."""
new_tex = r"""\emph{Cost.} One probe is 11 advances $\times$ 2 episodes $=22$ episodes, about 0.23\% of the 9600-episode training budget (0.92\% at 8 episodes per advance), Table~\ref{tab:cost}. Probing is cheap; the currency it lacks is identifiability, not compute.

\begin{table}[t]
\centering
\caption{Probe cost per calibration.}
\label{tab:cost}
\footnotesize
\begin{tabular}{@{}lccc@{}}
\toprule
configuration & episodes & env steps & share of training \\
\midrule
2 episodes/advance & 22 & 5{,}280 & 0.23\% \\
8 episodes/advance & 88 & 21{,}120 & 0.92\% \\
\bottomrule
\end{tabular}
\end{table}"""
assert old_tex in tex
tex = tex.replace(old_tex, new_tex, 1)
tex_path.write_text(tex, encoding="utf-8")

print("tables in tex:", len(re.findall(r"\\begin\{table\}", tex)))
print("Table VI in md:", "Table VI" in md)
