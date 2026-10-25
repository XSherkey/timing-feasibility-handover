# Rebuilding the two large artefacts

Nothing in the paper needs these two rebuilds in order to be *checked*: every reported number is in
`code/results/routeA_r3/**/*.json`. They are needed only to *re-run* an experiment from scratch.

## 1. The SGP4 twin cache (8.5 GB, generated)

```bash
python code/experiments/build_twin.py --tag ref --hours 12 --dt 10
```

* reads `code/data/tle/` (the shipped snapshot) and writes `data/cache/twin_ref_<sha>`
* one-off cost: tens of minutes on 8 CPU cores; later runs read the cache
* campaign epoch: `TwinConfig(epoch_year=2026, epoch_doy=292.25)`; the three lockbox instances shift
  `epoch_doy` by +7, +14 and −2 days

## 2. The campaign checkpoints

The frozen policies travel with the code: `code/results/campaign_1023/<run>/policy.pt`, one per run
(twenty campaign runs plus ten fixed-architecture runs, 2.7 MB in total). `eval_shield.py` loads exactly
that file, so every frozen-weight number in the paper can be re-evaluated offline with no training.

What is *not* shipped is the training bookkeeping of those runs (`run_summary.json`, `llm_calls.jsonl`,
about 300 MB). It is only needed to reconstruct the training curves, not to re-evaluate a policy; the
seed list, episode budget and intent profile are pinned in `code/experiments/manifest_r3.json` and the
campaign report is `code/results/analysis_1023/`.

## 3. Per-table reproduction commands

Each row is one script; each rewrites the JSON that the corresponding table is built from. All of them
are deterministic given the shipped artefacts and the checkpoints.

| paper element | script | output |
|---|---|---|
| Table II (failure attribution) | `experiments/run_headline_consistent.py` | `results/routeA_r3/headline_consistent/` |
| Table III (cross-intent) | `experiments/run_c3.py` | `results/routeA_r3/cross_intent/` |
| Table IV (isolation) | `experiments/run_factorial_consistent.py` | `results/routeA_r3/factorial_consistent/` |
| Table V (second constraint) | `experiments/run_window_case2.py` | `results/routeA_r3/window_case2/` |
| Table VI (closed loop) | `experiments/run_closed_loop.py` | `results/routeA_r3/closed_loop/` |
| Table VII (lockbox) | `experiments/run_lockbox_consistent.py` | `results/routeA_r3/lockbox_consistent/` |
| Tables VIII / IXb (traffic seeds) | `experiments/run_traffic_seeds.py`, `run_lockbox_traffic.py` | `results/routeA_r3/{traffic_seeds,lockbox_traffic}/` |
| Table G1 (threshold ledger) | transcribed from `results/routeA_r3/gate_systematic/summary.json`; the table is printed verbatim in Appendix G | — |
| Table G2 (block structure) | `experiments/run_precision.py` | `results/routeA_r3/precision/` |
| Table G3 (lockbox traffic cells) | `experiments/run_lockbox_traffic.py` | `results/routeA_r3/lockbox_traffic/` |
| Tables D2 / K1 (gate bank) | `experiments/run_gate_systematic.py` | `results/routeA_r3/gate_systematic/` |
| Tables H1 / H2 (drift) | `experiments/run_ladder_consistent.py` | `results/routeA_r3/ladder_consistent/` |
| Fig. 2 (policy independence) | `experiments/run_headline_consistent.py` + `experiments/make_fig2.py` | `figures/` |
| Fig. 4 (passive support) | `experiments/run_budget_curves.py` + `experiments/make_fig5.py` | `figures/` |
| Fig. 6 (λ dose-response) | `experiments/run_ladder_consistent.py` + `experiments/make_fig8.py` | `figures/` |

Single evaluation of any arm, the smallest reproducible unit (about 8 s on CPU):

```bash
python code/scripts/eval_shield.py --run <checkpoint> \
    --rule "min_advance:18@latitude_abs_deg>=68" --window test --out one.json
```

Files whose names begin with `_` in `code/experiments/` and `code/scripts/` are working scripts used
during the study (document assembly, one-off repairs); they are included for completeness and are not
needed to reproduce any table.

## 4. Verifying the shipped files

`MANIFEST.sha256` lists every file in `code/` and `paper/`:

```bash
cd code && sha256sum -c ../MANIFEST.sha256     # Linux / macOS
certutil -hashfile <file> SHA256               # Windows, per file
```

## 5. Environment

Python 3.10, PyTorch 2.5 (CPU is sufficient for every published number; a GPU only shortens training),
NumPy, SciPy, python-docx, and LibreOffice for the document build. The exact package set is
`code/requirements.txt`; the machine used for the reported numbers is described in
`code/docs/ENVIRONMENT_SETUP.md`.

**The language-model calls need a key of your own.** Set `ALMOND_LLM_BASE_URL`, `ALMOND_LLM_API_KEY` and
optionally `ALMOND_LLM_MODEL` (see `README.md`); no key is shipped with this archive. Two consequences:
with `ALMOND_LLM_BASE_URL` unset the client falls back to a *surrogate* stub rather than a model, which is
why the mining script refuses to start without a key; and because the recorded calls ship in
`results/routeA_r3/llm_proposals/`, the study can be inspected or replayed (`ReplayBackend`) without any
API access.