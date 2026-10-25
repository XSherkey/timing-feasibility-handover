import sys, torch, numpy as np
sys.path.insert(0, r"D:\almond-repro")
from almond.policies.nets import GraphSpec, build_policy, inherit_weights
x = torch.randn(5, 9, 7); adj = torch.zeros(5,9,9); adj[:,:,0]=1; adj[:,0,:]=1
for i in range(9): adj[:,i,i]=1
for spec in (GraphSpec(kind="att",width=64,layers=2,heads=4), GraphSpec(kind="hybrid",width=96,layers=2,heads=2),
             GraphSpec(kind="gcn",width=64,layers=2), GraphSpec(kind="mlp",width=64,layers=2)):
    p = build_policy("graph", obs_dim=69, node_dim=7, n_targets=9, n_advance=11, spec=spec)
    o = torch.randn(5,69)
    lt, la, v = p(o, x, adj)
    print(spec.describe(), int(lt.shape[0]), lt.shape[1], la.shape[1], v.shape[0], "params", p.param_count())
