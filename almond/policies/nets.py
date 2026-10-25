"""Policy networks for the handover controller.

Two families are implemented and share one actor-critic interface:

``FlatPolicy``
    The multi-layer-perceptron policy used by every baseline (PPO-MLP,
    PPO-Tuned, Eureka-style, Static-LLM, Oracle-PPO, distilled PPO-MLP).  It
    consumes the flat 68-dimensional observation of the twin.

``GraphPolicy``
    The policy produced by ALMOND's graph-grammar search.  It consumes the local
    handover subgraph ``(x, adj)`` exposed by
    :meth:`almond.twin.env.HandoverEnv.candidate_graph` and applies a sequence of
    GCN and/or multi-head-attention layers before pooling.  The search space,
    the parameter budget and the weight-inheritance rules are described in the
    manuscript (Sec. 3.3.1 and 3.3.3).

Both policies emit two categorical heads -- target selection ``(K + 1)`` and
preparation-advance bucket ``(M)`` -- plus a scalar value estimate.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Literal

import torch
import torch.nn as nn
import torch.nn.functional as F


# --------------------------------------------------------------------------- #
# building blocks
# --------------------------------------------------------------------------- #
class GCNLayer(nn.Module):
    """Dense graph convolution with symmetric normalisation and a residual term."""

    def __init__(self, width: int, dropout: float = 0.0):
        super().__init__()
        self.lin = nn.Linear(width, width)
        self.dropout = dropout

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        deg = adj.sum(-1, keepdim=True).clamp(min=1.0)
        norm = adj / torch.sqrt(deg * deg.transpose(-1, -2))
        h = torch.bmm(norm, x)
        h = self.lin(h)
        if self.dropout:
            h = F.dropout(h, self.dropout, self.training)
        return F.relu(h + x)


class EdgeTypeGCNLayer(nn.Module):
    """Graph convolution that separates the serving anchor from candidate edges.

    In the handover subgraph node 0 is the serving satellite and nodes 1..K are
    candidates.  A single weight matrix treats "serving -> candidate" and
    "candidate ~ candidate (same plane)" as the same relation, although the two
    carry different meaning: the first is the link that may be kept or replaced,
    the second is similarity inside the shortlist.  This layer aggregates the two
    edge populations with separate projections, so the grammar can express that
    distinction (grammar switch ``edge_types=1``).
    """

    def __init__(self, width: int, dropout: float = 0.0):
        super().__init__()
        self.lin_anchor = nn.Linear(width, width)
        self.lin_inner = nn.Linear(width, width)
        self.lin_self = nn.Linear(width, width)
        self.dropout = dropout

    @staticmethod
    def _agg(weights: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        deg = weights.sum(-1, keepdim=True).clamp(min=1.0)
        norm = weights / torch.sqrt(deg * deg.transpose(-1, -2))
        return torch.bmm(norm, x)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        n = adj.shape[-1]
        idx = torch.arange(n, device=adj.device)
        anchor_sel = ((idx[None, :] == 0) | (idx[:, None] == 0)).to(adj.dtype)
        eye = torch.eye(n, device=adj.device, dtype=adj.dtype)
        w_anchor = anchor_sel * (1.0 - eye) * adj
        w_inner = (1.0 - anchor_sel) * (1.0 - eye) * adj
        h = (
            self.lin_anchor(self._agg(w_anchor, x))
            + self.lin_inner(self._agg(w_inner, x))
            + self.lin_self(x)
        )
        if self.dropout:
            h = F.dropout(h, self.dropout, self.training)
        return F.relu(h)


class GraphAttentionLayer(nn.Module):
    """Multi-head self-attention over the local subgraph."""
    def __init__(self, width: int, heads: int, dropout: float = 0.0):
        super().__init__()
        self.heads = heads
        self.mha = nn.MultiheadAttention(width, heads, dropout=dropout, batch_first=True)
        self.norm = nn.LayerNorm(width)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        # nn.MultiheadAttention expects a (batch * n_heads, L, S) additive mask
        B, N, _ = x.shape
        mask = (adj <= 0.0).repeat_interleave(self.heads, dim=0)
        h, _ = self.mha(x, x, x, key_padding_mask=None, attn_mask=mask)
        return self.norm(F.relu(h + x))


class MLPBlock(nn.Module):
    def __init__(self, width: int, dropout: float = 0.0):
        super().__init__()
        self.lin = nn.Linear(width, width)
        self.dropout = dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.lin(x)
        if self.dropout:
            h = F.dropout(h, self.dropout, self.training)
        return F.relu(h + x)


# --------------------------------------------------------------------------- #
# graph-grammar specification
# --------------------------------------------------------------------------- #
@dataclass
class GraphSpec:
    """A policy topology drawn from the graph grammar of Sec. 3.3.1."""

    kind: Literal["mlp", "gcn", "att", "hybrid"] = "gcn"
    width: int = 64
    width_in: int = 64
    layers: int = 2
    heads: int = 2
    pool: Literal["mean", "max"] = "mean"
    dropout: float = 0.0
    #: global context encoder (the 14 validated telemetry fields)
    ctx_width: int = 64
    ctx_layers: int = 1
    # ---- structural switches added after the round-3 diagnosis ---------- #
    #: hidden width of the decision trunk/heads; 0 means "same as ctx_width"
    head_width: int = 0
    #: 0 = one weight matrix for all edges; 1 = serving-anchor edges and
    #: candidate-candidate edges get separate projections
    edge_types: int = 0
    #: free-form provenance for the knowledge graph / evolution log
    provenance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "GraphSpec":
        keys = {f for f in GraphSpec.__dataclass_fields__}
        return GraphSpec(**{k: v for k, v in d.items() if k in keys})

    def describe(self) -> str:
        extra = ""
        if self.head_width:
            extra += f" headw={self.head_width}"
        if self.edge_types:
            extra += " edgeTypes"
        if self.kind == "mlp":
            return f"MLP[{self.ctx_width}]x{self.ctx_layers}+MLP[{self.width}]x{self.layers}{extra}"
        if self.kind == "gcn":
            return f"GCN[{self.width}]x{self.layers}+{self.pool}{extra}"
        if self.kind == "att":
            return f"ATT[{self.width},h={self.heads}]x{self.layers}+{self.pool}{extra}"
        return (
            f"HYB[{self.width}] GCNx{self.layers//2}+ATT(h={self.heads})x{self.layers - self.layers//2}"
            f"+{self.pool}{extra}"
        )


# --------------------------------------------------------------------------- #
# policies
# --------------------------------------------------------------------------- #
class _Heads(nn.Module):
    def __init__(self, feat_dim: int, n_targets: int, n_advance: int, hidden: int = 64):
        super().__init__()
        self.trunk = nn.Sequential(nn.Linear(feat_dim, hidden), nn.ReLU())
        self.target = nn.Linear(hidden, n_targets)
        self.advance = nn.Linear(hidden, n_advance)
        self.value = nn.Linear(hidden, 1)

    def forward(self, z: torch.Tensor):
        h = self.trunk(z)
        return self.target(h), self.advance(h), self.value(h).squeeze(-1)


class FlatPolicy(nn.Module):
    """MLP actor-critic over the flat observation vector."""

    def __init__(self, obs_dim: int, n_targets: int, n_advance: int, hidden: int = 128):
        super().__init__()
        self.obs_dim = obs_dim
        self.n_targets = n_targets
        self.n_advance = n_advance
        self.body = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
        )
        self.heads = _Heads(hidden, n_targets, n_advance, hidden)

    def forward(self, obs, x=None, adj=None):
        z = self.body(obs)
        return self.heads(z)

    def param_count(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class GraphPolicy(nn.Module):
    """Graph-grammar policy over the local handover subgraph."""

    def __init__(self, spec: GraphSpec, obs_dim: int, node_dim: int, n_targets: int, n_advance: int):
        super().__init__()
        self.spec = spec
        self.obs_dim = obs_dim
        self.node_dim = node_dim
        self.n_targets = n_targets
        self.n_advance = n_advance
        w = spec.width
        self.embed = nn.Sequential(nn.Linear(node_dim, w), nn.ReLU())
        layers = []
        n_gcn = spec.layers if spec.kind in ("gcn",) else (
            spec.layers // 2 if spec.kind == "hybrid" else 0
        )
        n_att = spec.layers if spec.kind in ("att",) else (
            spec.layers - spec.layers // 2 if spec.kind == "hybrid" else 0
        )
        for _ in range(n_gcn):
            if spec.edge_types:
                layers.append(("gcn", EdgeTypeGCNLayer(w, spec.dropout)))
            else:
                layers.append(("gcn", GCNLayer(w, spec.dropout)))
        for _ in range(n_att):
            heads = spec.heads if w % max(spec.heads, 1) == 0 else 1
            layers.append(("att", GraphAttentionLayer(w, heads, spec.dropout)))
        if spec.kind == "mlp":
            layers = [("mlp", MLPBlock(w, spec.dropout)) for _ in range(max(spec.layers, 1))]
        self.layers = nn.ModuleList([m for _, m in layers])
        self.layer_kinds = [k for k, _ in layers]

        ctx_layers = []
        cw = spec.ctx_width
        prev = obs_dim
        for _ in range(max(spec.ctx_layers, 1)):
            ctx_layers += [nn.Linear(prev, cw), nn.ReLU()]
            prev = cw
        self.ctx = nn.Sequential(*ctx_layers)
        self.heads = _Heads(w * 2 + cw, n_targets, n_advance, spec.head_width or spec.ctx_width)

    def forward(self, obs, x=None, adj=None):
        h = self.embed(x)
        for kind, layer in zip(self.layer_kinds, self.layers):
            if kind in ("gcn", "att"):
                h = layer(h, adj)
            else:
                h = layer(h)
        if self.spec.pool == "max":
            g = h.amax(dim=1)
        else:
            g = h.mean(dim=1)
        serving = h[:, 0, :]
        c = self.ctx(obs)
        z = torch.cat([g, serving, c], dim=-1)
        return self.heads(z)

    def param_count(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def build_policy(
    kind: str,
    *,
    obs_dim: int,
    node_dim: int,
    n_targets: int,
    n_advance: int,
    spec: GraphSpec | None = None,
    hidden: int = 128,
):
    if kind in ("flat", "mlp", "ppo_mlp", "distilled", "heuristic_net"):
        return FlatPolicy(obs_dim, n_targets, n_advance, hidden)
    if spec is None:
        spec = GraphSpec()
    return GraphPolicy(spec, obs_dim, node_dim, n_targets, n_advance)


# --------------------------------------------------------------------------- #
# weight inheritance (Sec. 3.3.3)
# --------------------------------------------------------------------------- #
def function_preserving_expand(src: torch.Tensor, dst: torch.Tensor) -> bool:
    """Function-preserving expansion between two weight tensors.

    Row doubling copies every parent unit with halved outgoing weights; column
    doubling replicates the incoming fan-in.  Either way the child reproduces
    the parent's function at generation time (Sec. 3.3.3, rule ii).
    """
    if src.dim() != 2 or dst.dim() != 2:
        return False
    with torch.no_grad():
        if dst.shape[0] == 2 * src.shape[0] and dst.shape[1] == src.shape[1]:
            dst[:] = src.repeat(2, 1) * 0.5
            return True
        if dst.shape[0] == src.shape[0] and dst.shape[1] == 2 * src.shape[1]:
            dst[:, : src.shape[1]] = src
            dst[:, src.shape[1]:] = src
            return True
    return False


def inherit_weights(child: nn.Module, parent: nn.Module) -> float:
    """Copy every parameter whose name and shape match.

    Returns the fraction of child parameters that were inherited.
    """
    p_state = dict(parent) if isinstance(parent, dict) else dict(parent.named_parameters())
    total = 0
    copied = 0
    with torch.no_grad():
        for name, param in child.named_parameters():
            total += param.numel()
            src = p_state.get(name)
            if src is None:
                continue
            if src.shape == param.shape:
                param.copy_(src)
                copied += param.numel()
            elif src.dim() == param.dim() == 2:
                if function_preserving_expand(src, param):
                    copied += param.numel()
    return copied / max(total, 1)
