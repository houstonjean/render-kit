# Render desk setup

How to set up one Windows PC and one person to turn an architect's elevation into a checked, photoreal render, using Claude Code and Google's Nano Banana Pro image model.

This is the setup that produced the first job (a front elevation, about 2.5 hours, about $28). Everything below was either used on that job or checked the same day. Where something is untested, it says so.

**Time to set up:** about 1 hour.
**Running cost:** $100 to $200 a month for Claude, plus about $0.24 per image.

---

## What you end up with

| Piece | What it does | Cost |
|---|---|---|
| **Claude Code** (inside VS Code) | Reads the drawings, writes the image instructions, measures every result against the elevation, cuts and merges crops, drafts the client email | Claude Max $100/mo, or Ultra $200/mo |
| **Nano Banana Pro** (Google's image model) | Makes and edits the picture | $0.24 per 4K image, no subscription |
| **This kit** (the `render-kit` folder) | Claude's playbook, the working scripts, prompt examples, one folder per job | free |
| **GitHub** | Keeps the kit backed up and lets one person update every office PC | free plan is enough |

No VS Code plugins are needed beyond the Claude Code extension. The first job used none.

---

## Part 1. Accounts (20 minutes, do these first)

Create all three with a company email, not a personal one, so the firm keeps them if the person changes.

1. **Claude.** Go to claude.ai and sign up. Subscribe to **Max ($100/month)**. Move to **Ultra ($200/month)** only if the weekly limit is hit.
   - Both include Claude Code and the top model, Fable, up to half the weekly allowance.
   - For a firm that will keep using it: the **Team** plan needs 2 seats (premium seat $125 + standard seat $25 = $150/month) and states "No model training on your content by default". On Max and Ultra that is a setting you turn off yourself: in claude.ai open Settings, then Privacy, and switch off the option that lets your chats be used to improve the model.
2. **Google AI Studio.** Go to aistudio.google.com and sign in with a Google account. Open the API keys page (key icon, bottom left) and set up billing when asked. The paid tier is what makes 4K images available, and Google states paid-tier content is not used to improve its products.
3. **GitHub (optional).** Downloading the kit and getting updates needs no account. Create a free account at github.com only if you will send improvements back to the kit (Part 7).

---

## Part 2. Get the kit onto the PC (5 minutes)

Pick one.

**A. From the zip file (fastest).** Copy `render-kit.zip` to the PC and unzip it so the folder is exactly `C:\render-kit`.

**B. From GitHub (best if someone will keep the kit updated for you).** Press the Windows key, type `PowerShell`, press Enter, then run these one at a time:

```powershell
winget install -e --id Git.Git
```

Close PowerShell, open it again, then:

```powershell
git clone https://github.com/houstonjean/render-kit C:\render-kit
```

The repository is public, so this needs no GitHub account and no sign-in.

---

## Part 3. Install the software (15 minutes)

In PowerShell:

```powershell
cd C:\render-kit
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The script installs only what is missing:

| Software | Why |
|---|---|
| Git | version history and updates for the kit |
| VS Code | the window you work in |
| Python 3.14 | runs the measuring and merging scripts |
| GitHub CLI | signs in to GitHub from the command line |
| Python packages: pymupdf, pillow, numpy, opencv-python, google-genai | read the PDF, handle images, line images up, call Google's image model |
| Claude Code extension for VS Code | Claude itself |

To see what it would do without installing anything, add `-DryRun` to the end of the second line.

If `winget` is not recognized, install "App Installer" from the Microsoft Store and run the script again.

---

## Part 4. Sign in and set the image key (10 minutes)

1. **Open the kit in VS Code.** Start VS Code, choose File, then Open Folder, and pick `C:\render-kit`.
2. **Sign in to Claude.** Click the Claude icon (an orange spark) in the VS Code sidebar or the top right of the editor. Sign in with the Claude account from Part 1.
3. **Pick the top model.** In the Claude panel type `/model` and choose **Fable**.
4. **Create the Google image key.** In aistudio.google.com open the API keys page, click Create API key, and copy it.
5. **Save the key on the PC.** In PowerShell type `setx GEMINI_API_KEY "`, paste the key, type a closing `"`, and press Enter. It should answer `SUCCESS: Specified value was saved.`

> Never paste the key into a chat with Claude or into an email. If that happens, delete the key in AI Studio and create a new one.

---

## Part 5. Check that everything works (2 minutes)

```powershell
cd C:\render-kit
powershell -ExecutionPolicy Bypass -File .\check.ps1
```

Every line should say `PASS`. The two GitHub lines may say `SKIP` if you started from the zip. Fix any `FAIL` before going on; the line says what is missing.

---

## Part 6. Run a job

1. **Create the job folder.** In PowerShell:

   ```powershell
   cd C:\render-kit
   .\new-job.ps1 -Name "smith-front-elevation"
   ```

2. **Put the files in.** Copy everything for the job into `C:\render-kit\jobs\smith-front-elevation\inputs`:
   - the elevation as a PDF exported from CAD (not a scan or a photo: Claude re-cuts it at any scale only if it is a true vector PDF)
   - any existing render to start from
   - any markup sheets
   - the floor plan, if anything on the front is curved or recessed
   - photos or a web link for each material
3. **Start Claude.** In VS Code, open the Claude panel and start a new chat. Open `jobs\smith-front-elevation\START_HERE.txt`, copy all of it, paste it into Claude, add the client's or designer's email underneath, and press Enter.
4. **Answer Claude's questions.** It reads everything first and comes back with what does not match the elevation and a short list of questions. Send those to the designer before any image is made.
5. **Follow the passes.** Claude runs one change per pass, three images each, checks them against the drawing, and tells you which one it kept and why. You approve each pass.
6. **Review the result.** Claude finishes with the final image, a before/after sheet, and a check sheet with the elevation laid over the render in red.

### The same thing by hand, without the key

If the image key is not set up, Claude gives you the instruction and the files, and you run the image model yourself:

1. Open aistudio.google.com and choose the model **Nano Banana Pro**.
2. Set resolution **4K**, set the aspect ratio Claude names, and leave **Grounding with Google Search** on.
3. Drag in the files Claude lists, in the order it lists them.
4. Paste the instruction and press Run. Download the picture.
5. Click **+** for a new chat and repeat twice more. Do not type "do it again" in the same chat.
6. Tell Claude the three pictures are in your Downloads folder.

---

## Part 7. GitHub: backup and updates

The kit is the part worth protecting: the playbook, the scripts and the prompt library improve with every job.

**Client files never go to GitHub.** The `jobs` folder is excluded by the kit's `.gitignore`. Back that folder up the way the firm backs up its other project files.

The kit lives at https://github.com/houstonjean/render-kit and is public: anyone can download it, only invited accounts can change it.

**Each office PC, to get improvements (no account needed):**

```powershell
cd C:\render-kit
git pull
```

**To send improvements back, once:** create a free GitHub account, send the username to the owner (`houstonjean`) to be added as a collaborator, accept the invitation GitHub emails you, then run `gh auth login` in PowerShell (choose GitHub.com, HTTPS, and "Login with a web browser").

**After a job, to save a prompt that worked:** copy it into `templates\example_prompts.txt`, then:

```powershell
git add templates
git commit -m "Add prompt: slate roof swap"
git push
```

If the PC was set up from the zip and you now want it on GitHub: rename `C:\render-kit` to `C:\render-kit-old`, do Part 2 option B, then move `C:\render-kit-old\jobs` into `C:\render-kit`.

---

## Part 8. Daily cheat sheet

| Step | Who | What |
|---|---|---|
| 1 | You | `.\new-job.ps1 -Name "..."`, files into `inputs` |
| 2 | Claude | Reads everything, lists mismatches, asks questions |
| 3 | Designer | Answers the questions |
| 4 | Claude | One change per pass, three images, picks one, says why |
| 5 | You | Approve or redirect each pass |
| 6 | Claude | Detail areas (entry, gables): cuts a crop, lines the elevation up to it, merges the result back |
| 7 | Claude | Colour correction once at the end, then the check sheets |
| 8 | Designer | Reviews, marks up in plain words |

Rules that held on the first job:

- One change per pass. Say what changes, then what must stay the same.
- Name parts the way a mason would. Say what it is not ("not a round arch").
- Spell lettering out letter by letter.
- Three images per pass. Never send the first one unchecked.
- The elevation is the source of truth. The render is a presentation picture, not a construction document.

---

## Part 9. Problems that actually came up

| Problem | Fix |
|---|---|
| `python` is not recognized | Use `py` instead. The kit's scripts already do. |
| Claude panel does not offer the newest model | In PowerShell run `code --install-extension anthropic.claude-code --force`, then reload the VS Code window. |
| Image key was just set but a script says it is missing | The kit reads the saved key directly, so this should not happen. If it does, close and reopen VS Code. |
| The key was pasted into a chat | Delete it in AI Studio, create a new one, run the `setx` line again. |
| AI Studio has no "rerun" button | Click **+** for a new chat and upload again. |
| Downloaded file is named `something.png.jpg` | Harmless. Claude renames it. |
| Picture came back zoomed or reframed | Grounding with Google Search was off. Turn it on and run again. Seen once, so treat it as a lead, not a rule. |
| The image model added things nobody drew | Normal. One pass to remove them, naming each item. |
| Whole picture looks slightly pink after several passes | Normal: each pass adds a small cast. Claude corrects it once at the end against the first image. |
| Stone or lettering near the edit changed too | Claude redoes that area as a crop and merges it back, so nothing outside the crop can change. |

---

## Part 10. What the first job ran on

| Item | Version |
|---|---|
| Windows | 11 Pro |
| VS Code | 1.147.0 |
| Claude Code extension (`anthropic.claude-code`) | 2.1.332 |
| Claude model | Fable 5.2 |
| Python | 3.14.6 |
| pymupdf | 1.28.2 |
| pillow | 12.3.0 |
| numpy | 2.5.1 |
| opencv (cv2) | 4.14.0 |
| google-genai | 3.6.1 |
| Image model | `gemini-3-pro-image` (Nano Banana Pro), 4K, Google Search grounding on |
| Git / GitHub CLI | 2.54.0 / 2.94.0 |

Also used, optional: the Gmail connector in claude.ai (Settings, then Connectors), which let Claude read the designer's email and attachments and leave a reply in Drafts. Without it, save the attachments into `inputs` by hand and paste the email text into the chat.

## Not yet tested

- `setup.ps1` has been dry-run and its package names confirmed, but it has not been run on a brand-new PC.
- Every job so far started from an existing render. Going from a bare elevation to a first render is untested.
- A connector for Outlook or Microsoft 365 mail has not been tried.
- How many jobs a month fit inside the Max plan's limits is unknown. The first month answers that.
