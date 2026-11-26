# Creates a folder for one render job.
# Run:  .\new-job.ps1 -Name "smith-front-elevation"
param([Parameter(Mandatory)][string]$Name)

$safe = ($Name.Trim() -replace '[^A-Za-z0-9_-]+', '-').Trim('-').ToLower()
if (-not $safe) { Write-Host "Give the job a name with letters or numbers." -ForegroundColor Red; exit 1 }

$job = Join-Path $PSScriptRoot "jobs\$safe"
if (Test-Path $job) { Write-Host "That job already exists: $job" -ForegroundColor Red; exit 1 }

New-Item -ItemType Directory -Force (Join-Path $job 'inputs'), (Join-Path $job 'outputs') | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'templates\prompts.txt') (Join-Path $job 'prompts.txt')
$msg = (Get-Content (Join-Path $PSScriptRoot 'templates\starter_message.txt') -Raw).Replace('{JOB}', $safe)
Set-Content -Path (Join-Path $job 'START_HERE.txt') -Value $msg -Encoding utf8

Write-Host "Created $job" -ForegroundColor Green
Write-Host "1. Copy the elevation PDF, any render, markups, floor plan and material photos into:  $job\inputs"
Write-Host "2. In VS Code, open the Claude panel and start a new chat."
Write-Host "3. Open $job\START_HERE.txt, copy all of it, paste it into Claude, add the designer's email underneath, press Enter."
