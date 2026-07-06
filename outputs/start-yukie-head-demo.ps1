$ErrorActionPreference = "Stop"

$demo = Join-Path $PSScriptRoot "yukie-head-demo.html"
if (-not (Test-Path -LiteralPath $demo)) {
    throw "Demo file not found: $demo"
}

Start-Process -FilePath $demo
