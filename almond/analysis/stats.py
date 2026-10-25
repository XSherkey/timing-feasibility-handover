"""Statistical protocol of the manuscript (Sec. 4.1).

Every configuration is summarised with mean +- standard deviation over
independent seeds, a 95% confidence interval from the t distribution, and
pairwise comparisons against ALMOND using a paired test on per-seed values
(Wilcoxon signed-rank, with Student's t as a sensitivity check), Holm correction
across the baseline family, and effect sizes (Cohen's d for t, rank-biserial r
for Wilcoxon).  Convergence comparisons use per-seed episode counts with a
bootstrap CI on the ratio of medians.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats as sps


@dataclass
class Summary:
    n: int
    mean: float
    std: float
    ci_low: float
    ci_high: float
    median: float

    def as_dict(self) -> dict:
        return dict(
            n=self.n, mean=self.mean, std=self.std,
            ci_low=self.ci_low, ci_high=self.ci_high, median=self.median,
        )

    def __str__(self) -> str:
        return f"{self.mean:.2f} +- {self.std:.2f} (95% CI [{self.ci_low:.2f}, {self.ci_high:.2f}])"


def summarise(x, ci: float = 0.95) -> Summary:
    x = np.asarray([v for v in np.ravel(x) if np.isfinite(v)], dtype=float)
    n = x.size
    if n == 0:
        return Summary(0, np.nan, np.nan, np.nan, np.nan, np.nan)
    m = float(x.mean())
    sd = float(x.std(ddof=1)) if n > 1 else 0.0
    if n > 1:
        se = sd / np.sqrt(n)
        tcrit = float(sps.t.ppf(0.5 + ci / 2, n - 1))
        lo, hi = m - tcrit * se, m + tcrit * se
    else:
        lo = hi = m
    return Summary(n, m, sd, lo, hi, float(np.median(x)))


def cohen_d(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    na, nb = a.size, b.size
    if na < 2 or nb < 2:
        return float("nan")
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return float((a.mean() - b.mean()) / sp) if sp > 0 else float("nan")


def rank_biserial(a, b) -> float:
    """Matched-pairs rank-biserial correlation from the Wilcoxon statistic."""
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    d = d[np.isfinite(d) & (d != 0)]
    if d.size == 0:
        return 0.0
    ranks = sps.rankdata(np.abs(d))
    r_plus = ranks[d > 0].sum()
    r_minus = ranks[d < 0].sum()
    tot = r_plus + r_minus
    return float((r_plus - r_minus) / tot) if tot else 0.0


@dataclass
class PairedTest:
    name: str
    n: int
    median_diff: float
    w_stat: float
    p_wilcoxon: float
    p_ttest: float
    cohen_d: float
    rank_biserial: float
    p_holm: float = float("nan")

    def as_dict(self) -> dict:
        return dict(
            name=self.name, n=self.n, median_diff=self.median_diff,
            w_stat=self.w_stat, p_wilcoxon=self.p_wilcoxon, p_ttest=self.p_ttest,
            cohen_d=self.cohen_d, rank_biserial=self.rank_biserial, p_holm=self.p_holm,
        )


def paired_test(name: str, treatment, control) -> PairedTest:
    a = np.asarray(treatment, dtype=float)
    b = np.asarray(control, dtype=float)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    n = a.size
    if n == 0:
        return PairedTest(name, 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)
    diff = a - b
    if n >= 6 and np.any(diff != 0):
        try:
            w, pw = sps.wilcoxon(a, b, zero_method="wilcox")
        except ValueError:
            w, pw = np.nan, np.nan
        pt = float(sps.ttest_rel(a, b).pvalue)
    else:
        w, pw = np.nan, float(sps.ttest_rel(a, b).pvalue) if n > 1 else np.nan
        pt = pw
    return PairedTest(
        name=name,
        n=int(n),
        median_diff=float(np.median(diff)),
        w_stat=float(w) if np.isfinite(w) else float("nan"),
        p_wilcoxon=float(pw) if np.isfinite(pw) else float("nan"),
        p_ttest=float(pt) if np.isfinite(pt) else float("nan"),
        cohen_d=cohen_d(a, b),
        rank_biserial=rank_biserial(a, b),
    )


def holm(tests: list[PairedTest]) -> list[PairedTest]:
    """Holm-Bonferroni correction across the baseline family."""
    idx = [i for i, t in enumerate(tests) if np.isfinite(t.p_wilcoxon)]
    order = sorted(idx, key=lambda i: tests[i].p_wilcoxon)
    m = len(order)
    running = 0.0
    for rank, i in enumerate(order):
        adj = (m - rank) * tests[i].p_wilcoxon
        running = max(running, min(1.0, adj))
        tests[i].p_holm = running
    for i, t in enumerate(tests):
        if not np.isfinite(t.p_wilcoxon):
            t.p_holm = float("nan")
    return tests


def bootstrap_ratio_ci(a, b, n_boot: int = 4000, ci: float = 0.95, seed: int = 0):
    """Ratio of medians with a percentile bootstrap CI (convergence comparisons)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if a.size < 2 or b.size < 2:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    ratios = []
    for _ in range(n_boot):
        ra = rng.choice(a, size=a.size, replace=True)
        rb = rng.choice(b, size=b.size, replace=True)
        ma, mb = np.median(ra), np.median(rb)
        if mb > 0:
            ratios.append(ma / mb)
    if not ratios:
        return np.median(a) / np.median(b), float("nan"), float("nan")
    lo = float(np.percentile(ratios, (1 - ci) / 2 * 100))
    hi = float(np.percentile(ratios, (1 + ci) / 2 * 100))
    return float(np.median(a) / np.median(b)), lo, hi


def episodes_to_fraction(curve_x, curve_y, frac: float = 0.9, absolute: float | None = None) -> float:
    """Episodes to reach ``frac`` of the asymptote (or an absolute target).

    ``curve_x`` is the episode index, ``curve_y`` the satisfaction trajectory of
    one seed.  The asymptote is the mean of the last 20% of the curve.
    """
    x = np.asarray(curve_x, dtype=float)
    y = np.asarray(curve_y, dtype=float)
    ok = np.isfinite(y)
    x, y = x[ok], y[ok]
    if x.size < 3:
        return float("nan")
    if absolute is not None:
        target = absolute
    else:
        tail = max(1, int(np.ceil(0.2 * y.size)))
        target = frac * float(np.mean(y[-tail:]))
    idx = np.flatnonzero(y >= target)
    if idx.size == 0:
        return float(x[-1])
    return float(x[idx[0]])
