#requires -Version 7.0

param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

if ($PSEdition -ne 'Core' -or $PSVersionTable.PSVersion.Major -ne 7) {
    throw 'validate-bundle.ps1 requires PowerShell 7 (Core).'
}

$ErrorActionPreference = 'Stop'
$skillDirs = @(
    (Join-Path $Root 'skills/campus-recruitment'),
    (Join-Path $Root 'skills/job-application-form-filling'),
    (Join-Path $Root 'skills/offernotes-sync')
)

foreach ($skillDir in $skillDirs) {
    $skillFile = Join-Path $skillDir 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
        throw "Missing skill entrypoint: $skillFile"
    }
    $content = Get-Content -Raw -LiteralPath $skillFile
    if (-not $content.StartsWith('---')) { throw "Missing YAML frontmatter: $skillFile" }
    if ($content -notmatch '(?m)^name:\s*[a-z0-9-]+') { throw "Missing valid name: $skillFile" }
    if ($content -notmatch '(?m)^description:\s*\S+') { throw "Missing description: $skillFile" }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'Python is required for the validation scripts.' }

& $python.Source (Join-Path $Root 'scripts/public-safety-check.py') $Root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python.Source -m unittest discover -s (Join-Path $Root 'skills/campus-recruitment/scripts') -p 'test_*.py'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output 'validate-bundle: passed'
