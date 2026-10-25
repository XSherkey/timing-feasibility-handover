set -e
cd /home/u22/almond-repro
/usr/bin/python3.10 -c "import sys; sys.path.insert(0,'.'); from almond.twin.twin import DigitalTwin, TwinConfig; from almond.framework.system import AlmondSystem; from almond.framework.auditor import Auditor; from almond.llm.backend import LLMClient, SurrogateBackend; print('imports OK on VM')"
/usr/bin/python3.10 scripts/build_twin.py --tag vmprobe --hours 1.5 --dt 10 2>&1 | tail -6
/usr/bin/python3.10 scripts/run_auditor_stress.py 2>&1 | tail -8
/usr/bin/python3.10 scripts/run_llm_stability.py --repeats 8 2>&1 | tail -8
