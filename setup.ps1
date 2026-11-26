# Installs everything the render desk needs. Installs only what is missing.
# Run:      powershell -ExecutionPolicy Bypass -File .\setup.ps1
# Preview:  powershell -ExecutionPolicy Bypass -File .\setup.ps1 -DryRun
param([switch]$DryRun)

$kit = $PSScriptRoot

function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

function Step($what, [scriptblock]$action) {
    if ($DryRun) { Write-Host "WOULD  $what" -ForegroundColor Yellow }
    else { Write-Host "DOING  $what" -ForegroundColor Cyan; & $action }
}

function Update-SessionPath {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}

if (-not (Have winget)) {
    Write-Host "winget is missing. Install 'App Installer' from the Microsoft Store, then run this again." -ForegroundColor Red
    exit 1
}

$apps = @(
    @{ cmd = 'git';  id = 'Git.Git';                    name = 'Git' },
    @{ cmd = 'code'; id = 'Microsoft.VisualStudioCode'; name = 'VS Code' },
    @{ cmd = 'py';   id = 'Python.Python.3.14';         name = 'Python 3.14' },
    @{ cmd = 'gh';   id = 'GitHub.cli';                 name = 'GitHub CLI' }
)

foreach ($a in $apps) {
    if (Have $a.cmd) {
        Write-Host "OK     $($a.name) is already installed" -ForegroundColor Green
    } else {
        Step "install $($a.name)  (winget install -e --id $($a.id))" {
            winget install -e --id $a.id --accept-package-agreements --accept-source-agreements
        }
        Update-SessionPath
    }
}

Step "install Python packages from requirements.txt" {
    py -m pip install --disable-pip-version-check -r (Join-Path $kit 'requirements.txt')
}

Step "install the Claude Code extension for VS Code" {
    code --install-extension anthropic.claude-code
}

Write-Host ""
if ($DryRun) {
    Write-Host "Dry run only. Nothing was installed." -ForegroundColor Yellow
} else {
    Write-Host "Done. Next: SETUP.md Part 4 (sign in to Claude, save the image key), then run check.ps1." -ForegroundColor Green
    Write-Host "If a command above was 'not recognized', close PowerShell, open it again and run this script once more."
}
