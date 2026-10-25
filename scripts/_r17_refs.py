"""R17: replace the references that could not be verified, and fix the ones with wrong metadata."""
from __future__ import annotations

from pathlib import Path

D = Path(__file__).resolve().parents[2] / "From Human Intent to In-Orbit Action" / "IEEE_Trans_新版本"

REPL = {
    "[5]": ('W. Xie et al., "Evolutionary reward function search with large language models for '
            'multi-objective reinforcement learning," 2025.',
            'M. Kwon, S. M. Xie, K. Bullard, and D. Sadigh, "Reward design with language models," in '
            '*Proc. Int. Conf. Learning Representations (ICLR)*, 2023.'),
    "[6]": ('Z. Zhou et al., "Large language models as policy teachers for reinforcement learning agents," 2024.',
            'Y. Du, O. Watkins, Z. Wang, C. Colas, T. Darrell, P. Abbeel, A. Gupta, and J. Andreas, "Guiding '
            'pretraining in reinforcement learning with large language models," in *Proc. Int. Conf. Machine '
            'Learning (ICML)*, 2023.'),
    "[17]": ('S. Paul, K. Singh, M. H. T. Nguyen, T. Q. Duong, H. Shu, and H. Yu, "Digital twin-assisted '
             'space-air-ground integrated networks for vehicular edge computing," *IEEE J. Sel. Topics Signal '
             'Process.*, vol. 18, no. 1, pp. 66–82, 2024.',
             'Y. Wu, K. Zhang, and Y. Zhang, "Digital twin networks: A survey," *IEEE Internet Things J.*, '
             'vol. 8, no. 18, pp. 13789–13804, 2021.'),
    "[18]": ('Y. Zhou et al., "Digital twin-empowered satellite-terrestrial integrated networks," *IEEE Network*, 2023.',
             'L. U. Khan, W. Saad, D. Niyato, Z. Han, and C. S. Hong, "Digital-twin-enabled 6G: Vision, '
             'architectural trends, and future directions," *IEEE Commun. Mag.*, vol. 60, no. 1, pp. 74–80, 2022.'),
    "[20]": ('X. Zhu et al., "AI for non-terrestrial networks: A survey," 2025.',
             'S. Mahboob and L. Liu, "Revolutionizing future connectivity: A contemporary survey on '
             'AI-empowered satellite-based non-terrestrial networks in 6G," *IEEE Commun. Surveys Tuts.*, '
             'vol. 26, no. 2, 2024.'),
    "[24]": ('A. Corso, R. Moss, M. Koren, R. Lee, and M. Kochenderfer, "A survey of algorithms for constrained '
             'MDPs," 2021.',
             'E. Altman, *Constrained Markov Decision Processes*. Boca Raton, FL, USA: Chapman & Hall/CRC, 1999.'),
    "[26]": ('M. Hasan, H. Boostanimehr, and S. Bhargava, "Handover management in LEO satellite constellations: '
             'A survey," *IEEE Access*, 2023.',
             'S. Park and J. Kim, "Trends in LEO satellite handover algorithms," arXiv:2107.08619, 2021.'),
    "[27]": ('X. Wang et al., "Deep reinforcement learning for satellite handover," *IEEE Trans. Cogn. Commun. '
             'Netw.*, 2022.',
             'N. C. Luong, D. T. Hoang, S. Gong, D. Niyato, P. Wang, Y.-C. Liang, and D. I. Kim, "Applications '
             'of deep reinforcement learning in communications and networking: A survey," *IEEE Commun. Surveys '
             'Tuts.*, vol. 21, no. 4, pp. 3133–3174, 2019.'),
    "[28]": ('T. de Moortel, "Runtime assurance for autonomous systems," 2020.',
             'P. Koopman and M. Wagner, "Challenges in autonomous vehicle testing and validation," *SAE Int. J. '
             'Transp. Safety*, vol. 4, no. 1, pp. 15–24, 2016.'),
    "[29]": ('N. Fulton and A. Platzer, "Safe reinforcement learning via formal methods," 2019.',
             'N. Fulton and A. Platzer, "Safe reinforcement learning via formal methods: Toward safe control '
             'through proof and learning," in *Proc. AAAI Conf. Artificial Intelligence*, 2018.'),
    "[31]": ('J. García and A. Fernández, "Isotonic regression: A review," 2020.',
             'J. de Leeuw, "Monotonic regression: Basic," in *Wiley StatsRef: Statistics Reference Online*. '
             'Hoboken, NJ, USA: Wiley, 2014.'),
    "[33]": ('ITU-R, "Characteristics for inter-satellite links," Recommendation, 2022.',
             'R. Radhakrishnan, W. W. Edmonson, F. Afghah, R. M. Rodriguez-Osorio, F. Pinto, and S. C. Burleigh, '
             '"Survey of inter-satellite communication for small satellite systems: Physical layer to network '
             'layer view," *IEEE Commun. Surveys Tuts.*, vol. 18, no. 4, pp. 2442–2473, 2016.'),
    "[34]": ('N. Cheng et al., "6G non-terrestrial networks: Vision and challenges," *IEEE Veh. Technol. Mag.*, 2023.',
             'X. Lin, S. Rommer, S. Euler, E. A. Yavuz, and R. S. Karlsson, "5G from space: An overview of 3GPP '
             'non-terrestrial networks," *IEEE Commun. Standards Mag.*, vol. 5, no. 3, pp. 147–153, 2021.'),
    "[41]": ('D. Zhao, Y. Wang, B. Song, Y. Zhou, and P. Qin, "Learning when and where to handover: A hierarchical '
             'reinforcement learning framework for dense LEO satellite constellations," *IEEE Trans. Wireless '
             'Commun.*, vol. 25, pp. 12787–12801, Mar. 2026.',
             'D. Zhao, Y. Wang, B. Song, Y. Zhou, and P. Qin, "Learning when and where to handover: A hierarchical '
             'reinforcement learning framework for dense LEO satellite constellations," *IEEE Trans. Wireless '
             'Commun.*, early access, 2026.'),
    "[42]": ('H. Jang, J. Kim, I. Cho, M. Shin, J. G. Ryu, and S. Jung, "Proactive handover optimization via '
             'multi-agent deep reinforcement learning in integrated LEO satellite–terrestrial networks for '
             'high-mobility terminals," *ETRI J.*, 2026.',
             'H. Jang, J. Kim, I. Cho, M. Shin, J. G. Ryu, and S. Jung, "Proactive handover optimization via '
             'multi-agent deep reinforcement learning in integrated LEO satellite–terrestrial networks for '
             'high-mobility terminals," *ETRI J.*, 2026, doi: 10.4218/etrij.2025-0240.'),
    "[43]": ('Z. Xu, Y. Zhang, C. Sun, S. Lu, and C. Li, "From human intent to in-orbit action: A self-learning '
             'large language model agent for 6G satellite networks," submitted for publication, 2026.',
             'Z. Xu, Y. Zhang, C. Sun, S. Lu, and C. Li, "From human intent to in-orbit action: A self-learning '
             'large language model agent for 6G satellite networks," 2026, submitted for publication. '
             '(Prior report of the ALMOND pipeline reproduced and audited here; its published configuration and '
             'sealed artefacts are the basis of the reproduction in Section VI-A.)'),
}

for name in ("paper_en.md", "paper_zh.md"):
    p = D / name
    t = p.read_text(encoding="utf-8")
    n = 0
    for tag, (old, new) in REPL.items():
        if old in t:
            t = t.replace(old, new, 1)
            n += 1
        elif new in t:
            pass
        else:
            print(f"  {name}: {tag} text not found")
    p.write_text(t, encoding="utf-8")
    print(name, "references replaced:", n)

# keep the [27] sentence consistent with its new reference
p = D / "paper_en.md"
t = p.read_text(encoding="utf-8")
old = "Handover management with deep RL has its own literature [26], [27]"
if old in t:
    t = t.replace(old, "Handover management with deep RL, and DRL for network control more broadly, has its own "
                       "literature [26], [27]", 1)
    p.write_text(t, encoding="utf-8")
    print("EN [27] sentence updated")
