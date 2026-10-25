"""R21 part 4: shorten long author lists to 'et al.' (IEEE allows this beyond six authors) and trim ~400 words."""
from __future__ import annotations

import re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")

AUTHORS = [
    ('N. Shinn, F. Cassano, E. Berman, A. Gopinath, K. Narasimhan, and S. Yao,', 'N. Shinn et al.,'),
    ('H. Ma, Y. Liang, W. Wang, D.-A. Huang, O. Bastani, D. Jayaraman, Y. Zhu, L. Fan, and A. Anandkumar,', 'H. Ma et al.,'),
    ('T. Xie, S. Zhao, C. H. Wu, Y. Liu, Q. Liu, V. Zhong, Y. Yang, and T. Yu,', 'T. Xie et al.,'),
    ('Y. Huang, H. Du, X. Zhang, F. R. Yu, and Z. Han,', 'Y. Huang et al.,'),
    ('S. Paul, K. Singh, M. H. T. Nguyen, T. Q. Duong, H. Shu, and H. Yu,', 'S. Paul et al.,'),
    ('L. U. Khan, W. Saad, D. Niyato, Z. Han, and C. S. Hong,', 'L. U. Khan et al.,'),
    ('N. C. Luong, D. T. Hoang, S. Gong, D. Niyato, P. Wang, Y.-C. Liang, and D. I. Kim,', 'N. C. Luong et al.,'),
    ('R. Radhakrishnan, W. W. Edmonson, F. Afghah, R. M. Rodriguez-Osorio, F. Pinto, and S. C. Burleigh,', 'R. Radhakrishnan et al.,'),
    ('X. Lin, S. Rommer, S. Euler, E. A. Yavuz, and R. S. Karlsson,', 'X. Lin et al.,'),
    ('V. Mnih, K. Kavukcuoglu, D. Silver, A. A. Rusu, J. Veness, M. G. Bellemare, A. Graves, M. Riedmiller, '
     'A. K. Fidjeland, G. Ostrovski, et al.,', 'V. Mnih et al.,'),
    ('H. Jang, J. Kim, I. Cho, M. Shin, J. G. Ryu, and S. Jung,', 'H. Jang et al.,'),
    ('Z. Xu, Y. Zhang, C. Sun, S. Lu, and C. Li,', 'Z. Xu et al.,'),
    ('D. Zhao, Y. Wang, B. Song, Y. Zhou, and P. Qin,', 'D. Zhao et al.,'),
]
n = 0
for old, new in AUTHORS:
    if old in t:
        t = t.replace(old, new, 1)
        n += 1
print("author lists shortened:", n)

# ---- body trims ---------------------------------------------------------
edits = []


def sub1(old, new, label):
    global t
    if t.count(old) != 1:
        print("  MISS", label, t.count(old))
        return
    t = t.replace(old, new, 1)
    edits.append(label)


# Prop 1 (iii): keep the claim, drop the restatement
i = t.find("(iii) *Location below the plateau is a quantitative question.*")
if i > 0:
    j = t.find("\n\n", i)
    t = t[:i] + ("(iii) *Location below the plateau is quantitative.* Where a*(λ) lands in the trade-off region "
                 "depends on λ, the cost increments and the shape of p there; (i) bounds it without determining it. "
                 "In particular (ii) does not say the reward optimum cannot reach the feasible band—a large enough "
                 "λ can place a*(λ) at ā − Δ or above, at the price of distorting the objective against its latency "
                 "and power terms. Whether trained policies reach the band is answered by the dose-response of "
                 "Section VI-C.") + t[j:]
    edits.append("Prop-1 (iii) shortened")

t = re.sub(r"\n{3,}", "\n\n", t)
p.write_text(t, encoding="utf-8")
print("edits:", edits)
print("words:", len(re.findall(r"[A-Za-z0-9']+", t)))
