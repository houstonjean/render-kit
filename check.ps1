# Checks that the render desk is ready. Every required line should say PASS.
# Run:  powershell -ExecutionPolicy Bypass -File .\check.ps1

$script:fail = 0

function Check($label, [scriptblock]$test, [switch]$Optional, $fix = '') {
    $ok = $false; $detail = ''
    try {
        $r = & $test
        if ($r) { $ok = $true; if ($r -is [string]) { $detail = $r } }
    } catch { $detail = '' }
    if ($ok) { Write-Host ("PASS  {0,-34} {1}" -f $label, $detail) -ForegroundColor Green }
    elseif ($Optional) { Write-Host ("SKIP  {0,-34} optional. {1}" -f $label, $fix) -ForegroundColor Yellow }
    else { Write-Host ("FAIL  {0,-34} {1}" -f $label, $fix) -ForegroundColor Red; $script:fail++ }
}

Check 'Git' { "$(git --version)" } -fix 'Run setup.ps1.'
Check 'VS Code' { "$(code --version | Select-Object -First 1)" } -fix 'Run setup.ps1.'
Check 'Claude Code extension' {
    $e = code --list-extensions --show-versions | Select-String 'anthropic.claude-code'
    if ($e) { "$e" }
} -fix 'Run: code --install-extension anthropic.claude-code'
Check 'Python' { "$(py -V)" } -fix 'Run setup.ps1.'
Check 'Python packages' {
    $o = py -I -c "import pymupdf, PIL, numpy, cv2; from google import genai; print('pymupdf', pymupdf.__version__, '| pillow', PIL.__version__, '| numpy', numpy.__version__, '| opencv', cv2.__version__)" 2>$null
    if ($LASTEXITCODE -eq 0) { "$o" }
} -fix 'Run: py -m pip install -r requirements.txt'
Check 'Image key saved (value not shown)' {
    [bool][Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User') -or [bool]$env:GEMINI_API_KEY
} -fix 'SETUP.md Part 4, steps 4 and 5.'
Check 'Kit files' {
    (Test-Path "$PSScriptRoot\CLAUDE.md") -and (Test-Path "$PSScriptRoot\scripts\run_pass.py") -and (Test-Path "$PSScriptRoot\templates\prompts.txt")
} -fix 'The kit folder is incomplete. Unzip or clone it again.'
Check 'Scripts load' {
    $bad = 0
    Get-ChildItem "$PSScriptRoot\scripts" -Recurse -Filter *.py | ForEach-Object {
        py -I -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" $_.FullName 2>$null
        if ($LASTEXITCODE -ne 0) { $bad++ }
    }
    $bad -eq 0
} -fix 'A script file is damaged. Unzip or clone the kit again.'
Check 'GitHub CLI' { "$(gh --version | Select-Object -First 1)" } -Optional -fix 'Needed only for SETUP.md Part 7.'
Check 'GitHub signed in' { gh auth status 2>&1 | Out-Null; $LASTEXITCODE -eq 0 } -Optional -fix 'Run: gh auth login'

Write-Host ""
Write-Host "Not checked by this script: signing in to Claude inside VS Code (SETUP.md Part 4, steps 2 and 3)."
if ($script:fail -eq 0) { Write-Host "Ready." -ForegroundColor Green; exit 0 }
else { Write-Host "$($script:fail) item(s) need fixing." -ForegroundColor Red; exit 1 }
