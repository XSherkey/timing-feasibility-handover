# 环境搭建与复现指南（Windows 10/11 + Anaconda）

> 本文档对应 2026-10-23 在新硬盘 / 新装的 Windows 10 上重建环境的全过程。
> 目标：一条命令装好依赖，`python scripts/check_env.py` 全绿，然后按原来的协议跑实验。

---

## 1. 环境一览

| 项 | 值 |
|---|---|
| 环境名 | `almond`（conda） |
| 路径 | `C:\Users\xsher\.conda\envs\almond` |
| Python | 3.10.22（与原 `.venv` 的 3.10.0 同小版本线，代码按 3.10 写） |
| 关键包 | numpy 2.2.6 · scipy 1.15.3 · pandas 2.3.3 · matplotlib 3.10.9 · scikit-learn 1.7.2 · sgp4 2.27 · torch 2.5.1+cu124 · onnx 1.23.2 · onnxruntime 1.23.2 · python-docx 1.2.0 · lxml 6.1.3 · tqdm 4.70.1 |
| 完整依赖 | 见仓库根目录 `requirements.txt` |
| GPU | RTX 3070 8 GB，驱动 CUDA 13.5 → 可跑 cu124 运行时 |

依赖清单不是猜的：旧硬盘上的 `.venv\Lib\site-packages\*.dist-info` 完整保留，本环境的版本号是从那里逐个抄下来的。

---

## 2. 从零重建（三条命令）

```powershell
# 1) 建环境（Python 3.10）
conda create -n almond -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main python=3.10 pip -y

# 2) 装科学计算栈（清华 PyPI 镜像，很快）
conda activate almond
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple `
    numpy==2.2.6 scipy==1.15.3 pandas==2.3.3 matplotlib==3.10.9 `
    scikit-learn==1.7.2 sgp4==2.27 python-docx==1.2.0 lxml==6.1.3 `
    tqdm==4.70.1 onnx==1.23.2 onnxruntime==1.23.2

# 3) 装 GPU 版 torch（见下方“坑 1”，必须从 PyTorch 官方源装）
pip install --no-deps https://download.pytorch.org/whl/cu124/torch-2.5.1%2Bcu124-cp310-cp310-win_amd64.whl
```

验证：

```powershell
python scripts/check_env.py     # 依赖 / 本地模块 / CUDA / twin 缓存 四项自检
```

---

## 3. 三个已经踩过的坑

**坑 1：PyPI 上的 Windows torch 是 CPU 版。**
`pip install torch==2.5.1` 装出来的是 `2.5.1+cpu`（203 MB，`torch.cuda.is_available() == False`）。
旧环境是 `2.5.1+cu124`（2.5 GB），必须从 `https://download.pytorch.org/whl/cu124` 取。
Windows 版没有 `nvidia-*` 依赖，所以用 `--no-deps` 直接装 wheel 最稳。

**坑 2：阿里云镜像对大 wheel 会卡死在 0 字节。**
scipy（41 MB）和 torch（2.5 GB）从 `mirrors.aliyun.com` 下载时进程挂起、临时目录不增长；
实测同一文件 `download.pytorch.org` 约 4.7 MB/s，阿里云约 0.03 MB/s。
所以：PyPI 走清华镜像，torch 走官方源。下载大文件建议先 `curl -L -C -` 落盘再 `pip install <whl>`，断点可续。

**坑 3：`build_twin.py` 的 `--feeder-slots` 默认值与缓存不一致。**
脚本默认 4，但 `TwinConfig` 默认 10，而仓库里现成的 12 h 缓存（`data/cache/twin_ref_e85c26203e2a`，983 MB）
是按 10 建的。缓存键是除 `tag` 外所有物理参数的 SHA1，所以按原文档那条命令会白白重建一遍。
正确写法：

```powershell
python scripts/build_twin.py --tag ref --hours 12 --dt 10 --feeder-slots 10
# -> [twin] cache hit: ...\data\cache\twin_ref_e85c26203e2a   （0.5 s）
```

---

## 4. LLM 后端：默认不需要联网

`almond/llm/backend.py::_default_backend()` 的规则：

1. 设了 `ALMOND_LLM_BASE_URL` → 用真实的 OpenAI 兼容端点（DeepSeek 等）；
2. 没设 → 用 `SurrogateBackend`，确定性启发式，完全离线可跑。

另外 `ALMOND_LLM_BACKEND=surrogate` 可强制离线，即使配了 key。
仓库里 `results/llm_cache/`（数千条）保留了当年真实调用的应答，`compare_backends.py` 用它做 surrogate↔真模型对照。

需要复现“真模型”那一档时：

```powershell
$env:ALMOND_LLM_BASE_URL="https://api.deepseek.com"
$env:ALMOND_LLM_API_KEY="<你的 key>"
$env:ALMOND_LLM_MODEL="deepseek-flash"
$env:ALMOND_LLM_CONCURRENCY="4"
$env:ALMOND_LLM_CACHE_DIR="results/llm_cache"
```

> 注意：旧启动脚本 `.tmp\llm_run_*.cmd` 里明文写着当年的 API key。若仓库要外发（投稿附件 / 公开仓库），
> 请先吊销该 key 并清掉 `.tmp`。

---

## 5. 实验命令（与原协议一致）

```powershell
# 数字孪生缓存（12 h / 10 s，命中仓库内现成缓存）
python scripts/build_twin.py --tag ref --hours 12 --dt 10 --feeder-slots 10

# 架构搜索（可复用 results/nas/*.json，不必重跑）
python scripts/run_nas.py --mode llm    --out results/nas/llm_spec.json
python scripts/run_nas.py --mode random --out results/nas/random_spec.json

# 主 campaign：8 方法 x 10 seeds，9600 episodes（原协议用 CPU）
# 推荐用分臂启动器：它会自动给 almond->llm_spec、unseeded_evonas->random_spec 配好 spec 文件，
# 并复刻原启动脚本的全部环境变量，每臂一个日志写到 <out>/logs/。
python scripts/run_campaign_shard.py --method almond --seeds 0-9 --out results/campaign_1023
python scripts/run_campaign_shard.py --method ppomlp --seeds 0-9 --out results/campaign_1023
# …其余 6 臂同理；8 个进程并行在 12 核机器上约 20 min

# 汇总 / 出图 / 出表
python scripts/analyse_campaign.py --campaign results/campaign_1023 --out results/analysis_1023
python scripts/make_figures.py --analysis results/analysis_1023 --out results/figures_1023
python scripts/make_report.py --out docs
```

原启动脚本里还设了 `ALMOND_HC_PENALTY=0.05`、`OMP_NUM_THREADS=1`、`MKL_NUM_THREADS=1`、
`PYTHONIOENCODING=utf-8`，为保持逐位可比，建议一并保留（`run_campaign_shard.py` 已内置）。

**CPU 还是 GPU？** 原论文所有数字都是 `--device cpu`（单线程、`use_deterministic_algorithms(True)`）跑出来的，
CPU 路径才是“逐位复现”的那条。GPU 只适合快速试跑 / 调参；换 device 后 PPO 的浮点归约顺序变了，
末位差异会被采集噪声放大，别拿 GPU 的数字去对论文表。（实测：同样 60 episodes，GPU 45 s、CPU 52 s——
这个策略只有 39 K 参数，kernel launch 反而更贵。）

---

## 5b. 2026-10-23 的验证结果

| 检查 | 结果 |
|---|---|
| `scripts/check_env.py` | 14 个库版本齐、17 个模块 import 通过、GPU matmul 通过 |
| `scripts/smoke_twin.py` | 350 星 × 361 历元 0.06 s，Longyearbyen 可见 16.8，ISL 平均 3.93 跳 |
| `scripts/build_twin.py … --feeder-slots 10` | 缓存命中，0.5 s |
| campaign 8 臂 × 10 seeds | 80/80 完成，其中 7 臂与论文存档**逐位一致**（ALMOND 93.6±0.7、Oracle 71.8±13.6、PPO-MLP 72.6±16.1、Static-LLM 71.8±13.6、Unseeded 90.3±9.9；FixedArch/Eureka 差 0.06–0.5 pp）；`no_forensics` 因 round-4 的架构搜索重设计得到 78.9±11.0（存档 65.5±14.1），用存档架构回放可逐位复现 |
| 同配置双进程 | 极区 HSR 都是 `0.923900118906`，浮点相等 |
| `bench_latency.py` | ort_cpu_fp32 0.054 ms 均值 / 0.083 ms p99，ONNX 导出与推理链路正常 |
| `run_fidelity.py` | 链路预算 p95 误差 0.665 dB（与论文一致），规则复现 6/6 |
| `run_auditor_stress.py` | 5 类 × 20 例跑通（总假接受 52.5%） |
| `run_sensitivity.py` | θ_ρ / δ_min 扫描跑通 |

结果文件在 `results/campaign_1023/`、`results/analysis_1023/`、`results/figures_1023/`、`results/verify_1023/`；
完整对照见 `From Human Intent to In-Orbit Action/EAAI/复现结果/环境重建与复现验证_2026-10-23.md`。

---

## 6. 目录里那些历史残留

| 目录 | 大小 | 说明 |
|---|---|---|
| `almond-repro\.venv\` | 4.9 GB | 旧硬盘的 venv，`pyvenv.cfg` 指向已不存在的 `C:\Program Files\Python310`，**已失效**，可删 |
| `almond-repro\.tmp\` | 4.3 GB | 当年启动脚本、日志、pip 临时目录的残留，含明文 API key |
| `almond-repro\data\cache\` | 1.27 GB | 数字孪生缓存，**保留**（省掉每次重建） |
| `almond-repro\results\llm_cache\` | — | 真实 LLM 应答缓存，**保留** |

本机新环境不在仓库里（`C:\Users\xsher\.conda\envs\almond`），所以 `.venv` 可以安全删除以省 4.9 GB。
