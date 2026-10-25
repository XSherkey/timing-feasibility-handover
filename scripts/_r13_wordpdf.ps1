$ErrorActionPreference = "Stop"
$dir = "D:\Desktop_Files\论文\1. LLM Satellite Reinforcement Learning\自己写\From Human Intent to In-Orbit Action\IEEE_Trans_新版本"
$src = Join-Path $dir "Paper_EN_v55.docx"
$pdf = Join-Path $dir "_word.pdf"
$out = Join-Path $dir "_word_text.txt"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($src, $false, $true)
    if (Test-Path $pdf) { Remove-Item $pdf -Force }
    $doc.SaveAs([ref]$pdf, [ref]17)
    $doc.Close([ref]0)

    $back = $word.Documents.Open($pdf, $false, $true)
    $text = $back.Content.Text
    $back.Close([ref]0)
    Set-Content -Path $out -Value $text -Encoding UTF8
    Write-Host "chars: $($text.Length)"
} finally {
    $word.Quit()
}
