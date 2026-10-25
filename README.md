# almond-repro — code and artefacts for **Timing-Feasibility Constraints for LEO Handover: Attribution, Calibration and Audit in a Digital Twin**

This archive reproduces every number in the paper and its supplementary material. It is organised in
three layers:

```
code/                     the pipeline, the experiments and the analysis
  almond/                 twin, policies, forensics, shield, auditor
  experiments/            one script per table/figure in the paper
  scripts/                evaluation entry points, figure builders, checkers
  configs/  docs/         configuration snapshots and environment notes
  results/routeA_r3/      the sealed artefacts: one JSON per reported number
  data/tle/               the TLE snapshot the twin is propagated from
paper/                    the manuscript, the supplement and the cover letter
  Paper_EN_IEEE_v88_FINAL.docx
  supp_en_FINAL.docx
  COVER_LETTER.docx / .pdf
  figures/                the nine figures at their final resolution
REPRODUCE.md              how to rebuild the two large artefacts
MANIFEST.sha256           per-file hashes of code/ and paper/
```

## What is shipped and what is not

| artefact | size | shipped | why |
|---|---|---|---|
| code, configs, docs | ~2 MB | yes | — |
| `results/routeA_r3/**` | 3.8 MB | yes | the sealed JSON that every number comes from |
| `data/tle/` | 0.1 MB | yes | public TLE snapshot; the twin cache is rebuilt from it |
| SGP4 twin cache | 8.5 GB | **no** | rebuilt on first run (`REPRODUCE.md`) |
| frozen policies: `policy.pt` of the 20 campaign runs and the 10 fixed-architecture runs | 2.7 MB | yes | every frozen-weight evaluation in the paper can be re-run offline |
| the same runs' training logs (`run_summary.json`, `llm_calls.jsonl`) | 300 MB | **no** | training records; not needed to re-evaluate |
| virtual environment | 4.9 GB | **no** | `requirements.txt` plus `docs/ENVIRONMENT_SETUP.md` |

## Quick start

```bash
python -m pip install -r code/requirements.txt
export PYTHONPATH=$PWD/code            # Windows: set PYTHONPATH=%CD%\code
python code/scripts/eval_shield.py --run code/results/campaign_1023/almond_seed0 \
    --rule "min_advance:18@latitude_abs_deg>=68" --window test --out one.json
```

The first run builds the twin cache from `data/tle/`; later runs are cached. See `REPRODUCE.md` for the
per-table commands and the expected wall-clock time.

## Configuration (only needed to re-run the mining stage)

Everything that touches the language model reads its endpoint from the environment. There is **no key in
this archive**, and none is needed to reproduce any number in the paper — the frozen-weight experiments,
the probe, the gate, the lockbox and every figure read only the shipped JSON and the checkpoints.

| variable | meaning | needed for |
|---|---|---|
| `ALMOND_LLM_BASE_URL` | OpenAI-compatible endpoint, e.g. `https://api.deepseek.com` | re-running the mining stage |
| `ALMOND_LLM_API_KEY` | bearer token for that endpoint | re-running the mining stage |
| `ALMOND_LLM_MODEL` | served model name (default `deepseek-flash`) | optional |
| `ALMOND_LLM_CACHE` | `1` (default) caches responses by call, payload, seed and model | optional |
| `ALMOND_LLM_CONCURRENCY` | parallel in-flight calls (default 3) | optional |

```bash
export ALMOND_LLM_BASE_URL=https://api.deepseek.com
export ALMOND_LLM_API_KEY=<your key>
export ALMOND_LLM_MODEL=deepseek-flash
python code/experiments/run_llm_proposals.py
```

**Two traps worth knowing about.**

1. If `ALMOND_LLM_BASE_URL` is unset, the client silently falls back to a *surrogate* backend — a
   deterministic stub, not a model. Code runs, but nothing you get back is a language-model answer. The
   mining script now refuses to start in that state rather than produce stub output.
2. The recorded calls behind the proposal study (Section VI-N, Table J1 of the supplement) are shipped in `code/results/routeA_r3/llm_proposals/`
   (`train_attempts.json`, `proposals.csv`), so the study can be inspected — and replayed through
   `almond.llm.backend.ReplayBackend` for bit-exact reproduction — without any key at all.

## Licence

MIT — see `LICENSE`. The TLE data in `data/tle/` is redistributed under its original public terms.
