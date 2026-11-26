# Render kit

Everything one person needs to turn an architect's elevation into a checked, photoreal render with Claude Code and Google's Nano Banana Pro.

## Start here

1. Read **SETUP.md**. It takes about an hour, start to finish.
2. Install: `powershell -ExecutionPolicy Bypass -File .\setup.ps1`
3. Check: `powershell -ExecutionPolicy Bypass -File .\check.ps1`
4. First job: `.\new-job.ps1 -Name "house-name"`

## What is in the folder

| File or folder | What it is |
|---|---|
| `SETUP.md` | The setup guide and daily cheat sheet, for people |
| `CLAUDE.md` | The method, for Claude. Claude Code reads it automatically in this folder |
| `setup.ps1` | Installs Git, VS Code, Python, GitHub CLI, the Python packages and the Claude Code extension |
| `check.ps1` | Confirms the PC is ready |
| `new-job.ps1` | Creates `jobs/<name>` with `inputs`, `outputs`, a prompts file and a starter message |
| `templates/` | Blank prompts file, the starter message, and four prompts that worked |
| `scripts/` | The measuring, cropping, merging and image-model scripts |
| `jobs/` | One folder per job. Never uploaded to GitHub |

## Cost

Claude Max $100 a month (Ultra $200 if the limit is hit). Images about $0.24 each at 4K; the first job used 12.
