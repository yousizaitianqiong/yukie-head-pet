$ErrorActionPreference = "Stop"

$source = Join-Path $PSScriptRoot "yukie-head"
$target = Join-Path $HOME ".codex\pets\yukie-head"

if (-not (Test-Path -LiteralPath (Join-Path $source "pet.json"))) {
    throw "Pet package not found: $source"
}

New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $source "pet.json") -Destination $target -Force
Copy-Item -LiteralPath (Join-Path $source "spritesheet.webp") -Destination $target -Force

Write-Host "Yukie Head Pet updated: $target" -ForegroundColor Green
Write-Host "Return to the Codex pet panel and click Update."
