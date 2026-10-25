"""On-board inference benchmark for Table 6 of the manuscript.

Measures, for the largest discovered policy, the single-batch (batch = 1) latency
distribution, the policy-switch cost and the working-set footprint, in FP32 and
in the FP16 / INT8 quantised variants, on the hardware that is actually
available (the reference embedded platform of the paper, an NVIDIA Jetson Orin
NX-class module, is not present on this machine -- the measured board is named
in the output so that no claim in the paper depends on an unmeasured device).

Protocol (as in the manuscript): warm cache, ``--warmup`` inferences discarded,
then ``--iters`` timed inferences; the mean and the 99th percentile are
reported.  Quantised variants are additionally evaluated for handover-success
change and for action-switch stability (flaps per hour) against the FP32
baseline.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from almond.policies.nets import GraphSpec, build_policy
from almond.twin.env import EnvConfig, HandoverEnv
from almond.twin.twin import DigitalTwin, TwinConfig


def cpu_name() -> str:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Processor).Name"],
            capture_output=True, text=True, timeout=20,
        )
        return out.stdout.strip().splitlines()[0] if out.stdout.strip() else platform.processor()
    except Exception:  # pragma: no cover
        return platform.processor()


def load_policy(path: str, env, device: str = "cpu"):
    blob = torch.load(path, map_location="cpu", weights_only=False)
    spec = GraphSpec.from_dict(blob["spec"])
    x, adj = env.candidate_graph()
    pol = build_policy("graph", obs_dim=env.obs_dim, node_dim=x.shape[-1],
                       n_targets=env.K + 1, n_advance=env.n_advance, spec=spec)
    pol.load_state_dict(blob["policy"])
    pol.eval()
    return pol.to(device), blob


def time_fn(fn, warmup: int, iters: int) -> dict:
    for _ in range(warmup):
        fn()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    lat = np.empty(iters, dtype=np.float64)
    for i in range(iters):
        t0 = time.perf_counter()
        fn()
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        lat[i] = (time.perf_counter() - t0) * 1e3
    return dict(
        mean_ms=float(lat.mean()),
        p50_ms=float(np.percentile(lat, 50)),
        p95_ms=float(np.percentile(lat, 95)),
        p99_ms=float(np.percentile(lat, 99)),
        max_ms=float(lat.max()),
    )


def export_onnx(pol, obs_dim, node_dim, n_nodes, path: str, batch: int = 1):
    o = torch.zeros(batch, obs_dim)
    x = torch.zeros(batch, n_nodes, node_dim)
    adj = torch.eye(n_nodes).unsqueeze(0).repeat(batch, 1, 1)
    torch.onnx.export(
        pol, (o, x, adj), path,
        input_names=["obs", "x", "adj"],
        output_names=["target_logits", "advance_logits", "value"],
        opset_version=17, dynamo=False,
    )
    return path


def quantise(path: str, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    import onnx
    from onnxruntime.quantization import QuantType, quantize_dynamic

    outs = {}
    try:
        from onnxruntime.transformers.float16 import convert_float_to_float16

        m = onnx.load(path)
        m16 = convert_float_to_float16(m, keep_io_types=True)
        p16 = str(out_dir / "policy_fp16.onnx")
        onnx.save(m16, p16)
        outs["fp16"] = p16
    except Exception as exc:  # pragma: no cover
        outs["fp16_error"] = str(exc)
    try:
        p8 = str(out_dir / "policy_int8.onnx")
        quantize_dynamic(path, p8, weight_type=QuantType.QInt8)
        outs["int8"] = p8
    except Exception as exc:  # pragma: no cover
        outs["int8_error"] = str(exc)
    return outs


def ort_session(path: str, providers):
    import onnxruntime as ort

    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(path, so, providers=providers)


def eval_with_ort(env, sess, episodes=2, traffic=1.0):
    """Roll out the quantised policy through ONNX Runtime."""
    rows, attempts = [], []
    env.cfg.traffic_scale = traffic
    names = [i.name for i in sess.get_inputs()]
    for _ in range(episodes):
        env.reset()
        for _s in range(env.cfg.episode_steps):
            x, adj = env.candidate_graph()
            obs = env.obs().astype(np.float32)
            feat = {"obs": obs, "x": x, "adj": adj}
            out = sess.run(None, {k: feat[k] for k in names})
            lt, la = out[0], out[1]
            cand = env.cand_idx[env.site, env.t_idx]
            m = np.concatenate([np.ones((env.batch, 1), bool), cand >= 0], axis=1)
            lt = np.where(m, lt, -1e9)
            env.step(lt.argmax(-1), la.argmax(-1), record=True)
        st = env.episode_stats()
        lat = env.site_lat[env.site]
        for i in range(env.batch):
            rows.append(dict(lat=float(lat[i]), hsr=float(st["hsr"][i]),
                             attempts=int(st["attempts"][i]), successes=int(st["successes"][i]),
                             handovers=int(st["handovers"][i])))
        attempts.extend(env.attempt_log)
    env.cfg.traffic_scale = 1.0
    return rows, attempts


def hsr(rows, pred=lambda x: True):
    sel = [r for r in rows if pred(abs(r["lat"]))]
    att = sum(r["attempts"] for r in sel)
    return float(sum(r["successes"] for r in sel) / att * 100) if att else float("nan")


def flaps_per_hour(attempts, episode_s: float, batch: int):
    """Handover 'flaps': a new handover within 60 s of the previous one on the
    same instance.  Reported per hour of service."""
    by_inst: dict[tuple, list[int]] = {}
    for a in attempts:
        if not a["success"]:
            continue
        key = (a["site"], a["step"] // 1000)
        by_inst.setdefault(key, []).append(a["step"])
    flaps = 0
    total = 0
    for steps in by_inst.values():
        steps = sorted(steps)
        total += len(steps)
        for i in range(1, len(steps)):
            if (steps[i] - steps[i - 1]) * 10.0 < 60.0:
                flaps += 1
    hours = max(episode_s * batch / 3600.0, 1e-9)
    return float(flaps / hours), float(total / hours)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="results/campaign/almond_seed0/policy.pt")
    ap.add_argument("--tag", default="ref")
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--iters", type=int, default=10000)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--out", default="results/latency_benchmark.json")
    ap.add_argument("--episodes", type=int, default=2)
    args = ap.parse_args()

    twin = DigitalTwin(TwinConfig(tag=args.tag, horizon_s=args.hours * 3600)).build(verbose=False)
    env = HandoverEnv(twin, EnvConfig(episode_steps=240), batch=16, seed=11)
    pol, blob = load_policy(args.policy, env, "cpu")
    x, adj = env.candidate_graph()
    env.reset()
    obs1 = torch.as_tensor(env.obs()[:1])
    x1 = torch.as_tensor(x[:1])
    adj1 = torch.as_tensor(adj[:1])
    params = pol.param_count()

    out_dir = Path(args.out).with_suffix("")
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict = dict(
        board=dict(
            cpu=cpu_name(),
            gpu=(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none"),
            python=platform.python_version(),
            torch=torch.__version__,
        ),
        policy_file=args.policy,
        params=params,
        spec=blob.get("spec"),
        weight_bytes_fp32=params * 4,
        protocol=dict(batch=1, warmup=args.warmup, iters=args.iters),
        variants={},
    )

    # --- FP32 torch CPU / GPU ------------------------------------------ #
    p_cpu = pol.to("cpu")
    with torch.no_grad():
        results["variants"]["torch_cpu_fp32"] = time_fn(
            lambda: p_cpu(obs1, x1, adj1), args.warmup, args.iters)
    if torch.cuda.is_available():
        p_gpu = pol.to("cuda")
        o, xx, aa = obs1.cuda(), x1.cuda(), adj1.cuda()
        torch.cuda.reset_peak_memory_stats()
        with torch.no_grad():
            results["variants"]["torch_gpu_fp32"] = time_fn(
                lambda: p_gpu(o, xx, aa), args.warmup, args.iters)
        results["variants"]["torch_gpu_fp32"]["peak_alloc_mb"] = float(
            torch.cuda.max_memory_allocated() / 1e6)
        pol.to("cpu")

    # --- ONNX ----------------------------------------------------------- #
    onnx_path = str(out_dir / "policy_fp32.onnx")
    export_onnx(pol, env.obs_dim, x.shape[-1], x.shape[1], onnx_path, batch=1)
    # a separate fixed-batch export is used for the accuracy/stability runs
    eval_path = str(out_dir / f"policy_fp32_b{env.batch}.onnx")
    export_onnx(pol, env.obs_dim, x.shape[-1], x.shape[1], eval_path, batch=env.batch)
    feeds = dict(obs=env.obs()[:1].astype(np.float32), x=x[:1].astype(np.float32),
                 adj=adj[:1].astype(np.float32))
    providers = ["CPUExecutionProvider"]
    sess_cpu = ort_session(onnx_path, providers)
    names = [i.name for i in sess_cpu.get_inputs()]
    results["variants"]["ort_cpu_fp32"] = time_fn(
        lambda: sess_cpu.run(None, {k: feeds[k] for k in names}), min(args.warmup, 500), args.iters)
    results["onnx_bytes_fp32"] = Path(onnx_path).stat().st_size
    if torch.cuda.is_available():
        try:
            sess_gpu = ort_session(onnx_path, ["CUDAExecutionProvider", "CPUExecutionProvider"])
            results["variants"]["ort_cuda_fp32"] = time_fn(
                lambda: sess_gpu.run(None, {k: feeds[k] for k in names}), min(args.warmup, 500), args.iters)
        except Exception as exc:  # pragma: no cover
            results["variants"]["ort_cuda_fp32"] = dict(error=str(exc))

    # --- quantised ------------------------------------------------------ #
    # batch-1 models for the latency measurement, batch-N for the effect study
    q1 = quantise(onnx_path, out_dir / "q1")
    qn = quantise(eval_path, out_dir / "qn")
    eval_sess = ort_session(eval_path, providers)
    base_rows, base_att = eval_with_ort(env, eval_sess, episodes=args.episodes)
    for tag in ("fp16", "int8"):
        if tag not in q1:
            results["variants"][f"ort_cpu_{tag}"] = dict(error=q1.get(f"{tag}_error", "n/a"))
            continue
        s = ort_session(q1[tag], providers)
        nm = [i.name for i in s.get_inputs()]
        results["variants"][f"ort_cpu_{tag}"] = time_fn(
            lambda s=s, nm=nm: s.run(None, {k: feeds[k] for k in nm}), min(args.warmup, 500), args.iters)
        results["variants"][f"ort_cpu_{tag}"]["model_bytes"] = Path(q1[tag]).stat().st_size

        # accuracy / stability effect, measured on the batch-N export
        if tag not in qn:
            continue
        s_eval = ort_session(qn[tag], providers)
        rows, att = eval_with_ort(env, s_eval, episodes=args.episodes)
        fph_base, hp_base = flaps_per_hour(base_att, env.cfg.episode_steps * 10, env.batch)
        fph, hp = flaps_per_hour(att, env.cfg.episode_steps * 10, env.batch)
        results.setdefault("quantisation_effect", {})[tag] = dict(
            hsr_all_fp32=hsr(base_rows), hsr_all_quant=hsr(rows),
            hsr_arctic_fp32=hsr(base_rows, lambda x: x > 70),
            hsr_arctic_quant=hsr(rows, lambda x: x > 70),
            flaps_per_hour_fp32=fph_base, flaps_per_hour_quant=fph,
            handovers_per_hour_fp32=hp_base, handovers_per_hour_quant=hp,
        )

    # --- policy switch cost --------------------------------------------- #
    buf = io_bytes = None
    import io

    buf = io.BytesIO()
    torch.save(pol.state_dict(), buf)
    io_bytes = buf.getbuffer().nbytes
    sd = pol.state_dict()
    t0 = time.perf_counter()
    for _ in range(100):
        fresh = {k: v.clone() for k, v in sd.items()}
    t_load = (time.perf_counter() - t0) / 100 * 1e3
    t0 = time.perf_counter()
    for _ in range(100):
        pol.load_state_dict(sd)
    t_restore = (time.perf_counter() - t0) / 100 * 1e3
    results["policy_switch"] = dict(
        serialized_bytes=int(io_bytes),
        restore_from_memory_objects_ms=float(t_load),
        load_state_dict_ms=float(t_restore),
    )
    Path(args.out).write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"board: {results['board']['cpu']} | {results['board']['gpu']}")
    print(f"policy: {params} params, {results['weight_bytes_fp32'] / 1024:.0f} KB FP32 weights")
    for k, v in results["variants"].items():
        if "mean_ms" in v:
            print(f"  {k:<20} mean {v['mean_ms']:7.3f} ms   p99 {v['p99_ms']:7.3f} ms")
        else:
            print(f"  {k:<20} {v}")
    if "quantisation_effect" in results:
        for k, v in results["quantisation_effect"].items():
            print(f"  {k}: HSR {v['hsr_all_fp32']:.1f} -> {v['hsr_all_quant']:.1f} | "
                  f"arctic {v['hsr_arctic_fp32']:.1f} -> {v['hsr_arctic_quant']:.1f} | "
                  f"flaps/h {v['flaps_per_hour_fp32']:.2f} -> {v['flaps_per_hour_quant']:.2f}")
    print(f"  policy switch: {results['policy_switch']}")
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
