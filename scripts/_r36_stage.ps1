param(
    [string]$Repo = (Get-Location).Path,
    [string]$Paper = ""
)
$ErrorActionPreference = "Stop"

if (-not $Paper) { $Paper = Join-Path (Split-Path $Repo -Parent) "From Human Intent to In-Orbit Action\IEEE_Trans_新版本" }
$pkg = Join-Path (Split-Path $Repo -Parent) "IEEE_Submission_Package"

Write-Host "repo:  $Repo"
Write-Host "paper: $Paper"
Write-Host "pkg:   $pkg"

Remove-Item $pkg -Recurse -Force -ErrorAction SilentlyContinue
foreach ($d in @("paper", "paper\figures", "code", "code\almond", "code\experiments", "code\scripts",
                 "code\configs", "code\docs", "code\results", "code\data")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $pkg $d) | Out-Null
}

function Copy-Tree($src, $dst) {
    if (-not (Test-Path $src)) { Write-Host "  skip (missing): $src"; return }
    robocopy $src $dst /E /NFL /NDL /NJH /NJS /NP /XD __pycache__ .pytest_cache /XF *.pyc *.pyo | Out-Null
}

# ---- code ----
Copy-Tree (Join-Path $Repo "almond")      (Join-Path $pkg "code\almond")
Copy-Tree (Join-Path $Repo "experiments") (Join-Path $pkg "code\experiments")
Copy-Tree (Join-Path $Repo "scripts")     (Join-Path $pkg "code\scripts")
Copy-Tree (Join-Path $Repo "configs")     (Join-Path $pkg "code\configs")
Copy-Tree (Join-Path $Repo "docs")        (Join-Path $pkg "code\docs")
Copy-Tree (Join-Path $Repo "results\routeA_r3") (Join-Path $pkg "code\results\routeA_r3")
Copy-Tree (Join-Path $Repo "data\tle")    (Join-Path $pkg "code\data\tle")
Copy-Item (Join-Path $Repo "requirements.txt") (Join-Path $pkg "code\requirements.txt") -ErrorAction SilentlyContinue
Copy-Item (Join-Path $Repo "README.md") (Join-Path $pkg "code\README_ORIGINAL.md") -ErrorAction SilentlyContinue

# ---- paper ----
Copy-Item (Join-Path $Paper "Paper_EN_IEEE_v88_FINAL.docx") (Join-Path $pkg "paper\Paper_EN_IEEE_v88_FINAL.docx") -ErrorAction SilentlyContinue
Copy-Item (Join-Path $Paper "supplementary\supp_en_FINAL.docx") (Join-Path $pkg "paper\supp_en_FINAL.docx") -ErrorAction SilentlyContinue
Copy-Item (Join-Path $Paper "COVER_LETTER.docx") (Join-Path $pkg "paper\COVER_LETTER.docx") -ErrorAction SilentlyContinue
Copy-Item (Join-Path $Paper "COVER_LETTER.pdf")  (Join-Path $pkg "paper\COVER_LETTER.pdf") -ErrorAction SilentlyContinue
Copy-Tree (Join-Path $Paper "figures") (Join-Path $pkg "paper\figures")

Get-ChildItem $pkg -Recurse -File | Measure-Object Length -Sum |
    ForEach-Object { Write-Host ("package: {0} files, {1:N1} MB" -f $_.Count, ($_.Sum / 1MB)) }
