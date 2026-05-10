param(
    [string]$Source = "C:\Users\a1921\Desktop\testbooks",
    [string]$Destination = "C:\Users\a1921\Desktop\Agent4Study\data\textbooks"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "Dataset source directory not found: $Source"
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null

$files = Get-ChildItem -LiteralPath $Source -File -Include *.pdf,*.md,*.txt,*.docx,*.xlsx
if (-not $files) {
    throw "No supported textbook files found in: $Source"
}

$manifest = foreach ($file in $files) {
    $target = Join-Path $Destination $file.Name
    Copy-Item -LiteralPath $file.FullName -Destination $target -Force
    [PSCustomObject]@{
        filename = $file.Name
        bytes = $file.Length
        source = $file.FullName
        destination = $target
        imported_at = (Get-Date).ToString("s")
    }
}

$manifestPath = Join-Path $Destination "testbooks_manifest.json"
$manifest | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

Write-Host "Imported $($files.Count) textbook files into $Destination"
Write-Host "Manifest written to $manifestPath"
