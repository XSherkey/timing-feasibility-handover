$ErrorActionPreference = 'Continue'
$py = 'C:\Users\xsher\.conda\envs\almond\python.exe'
Set-Location 'D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro'
$env:PYTHONPATH = 'D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\almond-repro'
$env:OMP_NUM_THREADS = '2'
$env:MKL_NUM_THREADS = '2'
$env:PYTHONIOENCODING = 'utf-8'
$env:ALMOND_LLM_BASE_URL = 'https://api.deepseek.com'
$env:ALMOND_LLM_MODEL = 'deepseek-flash'
if (-not $env:ALMOND_LLM_API_KEY) { throw 'set ALMOND_LLM_API_KEY in the environment first' }

foreach ($mode in @('shared', 'fresh')) {
    foreach ($s in 6, 7, 8, 9) {
        $out = "results/multi_${mode}_s$s"
        if (Test-Path "$out/summary.json") { Write-Host "skip $mode $s"; continue }
        Write-Host "== $mode seed $s"
        & $py scripts/run_multi_intent.py --mode $mode --seed $s --out $out 2>&1 |
            Select-String -Pattern 'arctic' | ForEach-Object { $_.Line }
    }
}
Write-Host 'DONE'
