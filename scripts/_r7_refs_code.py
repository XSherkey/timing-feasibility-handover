"""R7 (v9): complete verifiable references in both manuscripts, add the D1 verification note,
and remove the shell continuation backslashes from Appendix A (they extract as stray ticks)."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

REFS = [
    ('[2] N. Shinn, F. Cassano, A. Gopinath, K. Narasimhan, and S. Yao, "Reflexion: Language agents with verbal reinforcement learning," in *Proc. NeurIPS*, 2023.',
     '[2] N. Shinn, F. Cassano, E. Berman, A. Gopinath, K. Narasimhan, and S. Yao, "Reflexion: Language agents with verbal reinforcement learning," in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 36, 2023.'),
    ('[3] H. Ma, C. Liu, et al., "Eureka: Human-level reward design via coding large language models," in *Proc. ICLR*, 2024.',
     '[3] H. Ma, Y. Liang, W. Wang, D.-A. Huang, O. Bastani, D. Jayaraman, Y. Zhu, L. Fan, and A. Anandkumar, "Eureka: Human-level reward design via coding large language models," in *Proc. ICLR*, 2024.'),
    ('[4] T. Xie, D. Zhao, et al., "Text2Reward: Reward shaping with language models for reinforcement learning," in *Proc. ICLR*, 2024.',
     '[4] T. Xie, S. Zhao, C. H. Wu, Y. Liu, Q. Liu, V. Zhong, Y. Yang, and T. Yu, "Text2Reward: Reward shaping with language models for reinforcement learning," in *Proc. ICLR*, 2024.'),
    ('[7] E. Lira et al., "Zero-touch configuration management with large language models," 2025.',
     '[7] G. Lira, O. M. Caicedo, and N. L. S. da Fonseca, "Large language models for zero touch network configuration management," *IEEE Commun. Mag.*, vol. 63, no. 6, pp. 146–153, 2025.'),
    ('[8] Y. Huang et al., "Large language models for networking: A survey," 2024.',
     '[8] Y. Huang, H. Du, X. Zhang, F. R. Yu, and Z. Han, "Large language models for networking: Applications, enabling techniques, and challenges," *IEEE Network*, vol. 38, no. 3, pp. 208–216, 2024.'),
    ('[9] W. Kou et al., "Generative intent abstraction for intent-driven networks," 2025.',
     '[9] S. Kou, C. Yang, and M. Gurusamy, "GIA: LLM-enabled generative intent abstraction to enhance adaptability for intent-driven networks," *IEEE Trans. Cogn. Commun. Netw.* (early access), 2025.'),
    ('[17] S. Paul, A. De, et al., "Digital twins in non-terrestrial networks," 2024.',
     '[17] S. Paul, K. Singh, M. H. T. Nguyen, T. Q. Duong, H. Shu, and H. Yu, "Digital twin-assisted space-air-ground integrated networks for vehicular edge computing," *IEEE J. Sel. Topics Signal Process.*, vol. 18, no. 1, pp. 66–82, 2024.'),
    ('[22] H. Cai, C. Gan, et al., "Once-for-all network (EG-NAS: efficient evolutionary NAS)," 2024.',
     '[22] Z. Cai, L. Chen, P. Liu, Y. Wang, and S. Han, "EG-NAS: Neural architecture search with fast evolutionary exploration," in *Proc. AAAI Conf. Artificial Intelligence*, vol. 38, pp. 11159–11167, 2024.'),
    ('[23] G. Dalac-Arnold, D. Mankowitz, and T. Hester, "Challenges of real-world reinforcement learning," 2019.',
     '[23] G. Dulac-Arnold, D. Mankowitz, and T. Hester, "Challenges of real-world reinforcement learning," arXiv:1904.12901, 2019.'),
    ('[25] D. Amodei et al., "Concrete problems in AI safety," 2016.',
     '[25] D. Amodei, C. Olah, J. Steinhardt, P. Christiano, J. Schulman, and D. Mané, "Concrete problems in AI safety," arXiv:1606.06565, 2016.'),
    ('[35] M. Giordani and M. Zorzi, "Non-terrestrial networks in the 6G era: Challenges and opportunities," 2021.',
     '[35] M. Giordani and M. Zorzi, "Non-terrestrial networks in the 6G era: Challenges and opportunities," *IEEE Network*, vol. 35, no. 2, pp. 244–251, 2021.'),
    ('[39] V. Mnih et al., "Human-level control through deep reinforcement learning," *Nature*, vol. 518, 2015.',
     '[39] V. Mnih, K. Kavukcuoglu, D. Silver, A. A. Rusu, J. Veness, M. G. Bellemare, A. Graves, M. Riedmiller, A. K. Fidjeland, G. Ostrovski, et al., "Human-level control through deep reinforcement learning," *Nature*, vol. 518, no. 7540, pp. 529–533, 2015.'),
    ('[43] Z. Xu, Y. Zhang, C. Sun, S. Lu, and C. Li, "From human intent to in-orbit action: A self-learning large language model agent for 6G satellite networks," submitted to *Eng. Appl. Artif. Intell.* (under review).（本文复现并审计的 ALMOND 流水线的前作报道。）',
     '[43] Z. Xu, Y. Zhang, C. Sun, S. Lu, and C. Li, "From human intent to in-orbit action: A self-learning large language model agent for 6G satellite networks," submitted for publication, 2026.（本文复现并审计的 ALMOND 流水线的前作报道。）'),
]

D1_NOTE_EN = ("*Verification.* Each row satisfies attempts = exact events + right-censored + competing risk; "
              "the attempts column sums to the stated total; and every share equals that row's attempts divided "
              "by the total, to one decimal place.")
D1_NOTE_ZH = ("*核对。* 每行满足「尝试数 = 精确事件 + 右删失 + 竞争风险」；尝试数列之和等于表中申明的合计；"
              "每个占比等于该行尝试数除以总数（保留一位小数）。")

CODE_EN_OLD = """python scripts/run_campaign.py --methods almond --seeds 0-9 \\
       --episodes 9600 --eval-every 1200 --device cpu \\
       --spec-file results/nas/llm_spec.json --out results/campaign_1023"""
CODE_EN_NEW = """python scripts/run_campaign.py --methods almond --seeds 0-9 --episodes 9600 --eval-every 1200 --device cpu --spec-file results/nas/llm_spec.json --out results/campaign_1023"""

PAIRS_EN = [
    CODE_EN_OLD, CODE_EN_NEW,
    """python scripts/eval_shield.py --run results/campaign_1023/almond_seed0 \\
       --rule "min_advance:16@latitude_abs_deg>=68"             # frozen-policy factorial""",
    """python scripts/eval_shield.py --run results/campaign_1023/almond_seed0 --rule "min_advance:16@latitude_abs_deg>=68"   # frozen-policy factorial""",
    """python scripts/probe_feasibility.py --run results/campaign_1023/almond_seed0 \\
       --regime polar --episodes 8                              # active probe""",
    """python scripts/probe_feasibility.py --run results/campaign_1023/almond_seed0 --regime polar --episodes 8   # active probe""",
    """python scripts/run_campaign.py --methods no_forensics --seeds 0-9 \\
       --late-risk-tau 16 --late-risk-weight 8.0 --out results/routeA_f3/lam8.0""",
    """python scripts/run_campaign.py --methods no_forensics --seeds 0-9 --late-risk-tau 16 --late-risk-weight 8.0 --out results/routeA_f3/lam8.0""",
    """python scripts/probe_gate.py --run results/campaign_1023/almond_seed0 \\
       --episodes 8                                           # six-candidate audit gate""",
    """python scripts/probe_gate.py --run results/campaign_1023/almond_seed0 --episodes 8   # six-candidate audit gate""",
]

for name, note in (("paper_en.md", D1_NOTE_EN), ("paper_zh.md", D1_NOTE_ZH)):
    p = D / name
    t = p.read_text(encoding="utf-8")
    n_ref = 0
    for old, new in REFS:
        if t.count(old) == 1:
            t = t.replace(old, new, 1)
            n_ref += 1
    if name == "paper_en.md":
        pairs = list(zip(PAIRS_EN[::2], PAIRS_EN[1::2]))
    else:
        pairs = []
        for a, b in zip(PAIRS_EN[::2], PAIRS_EN[1::2]):
            if t.count(a) == 1:
                pairs.append((a, b))
    n_code = 0
    for a, b in pairs:
        if t.count(a) == 1:
            t = t.replace(a, b, 1)
            n_code += 1
    # append the verification note to both D1 captions
    anchor_en = "**Table D1B. Rule-applied logs (deployed arms, ten seeds; the 16 s mined rule executed at evaluation; |lat| ≥ 68°; 22,807 attempts).**"
    anchor_zh = "**表 D1B. 规则生效日志（部署各臂，十个种子；评测时执行 16 s 挖掘规则；|lat| ≥ 68°；22,807 次尝试）。**"
    anchor = anchor_en if name == "paper_en.md" else anchor_zh
    note_ok = False
    if t.count(anchor) == 1 and note not in t:
        t = t.replace(anchor, anchor + "\n\n" + note, 1)
        note_ok = True
    p.write_text(t, encoding="utf-8")
    print(name, "| refs updated", n_ref, "| code blocks joined", n_code, "| D1 note", note_ok)
