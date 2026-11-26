# Render kit: how to work in this folder

You are helping one person at an architecture or home-design office turn an elevation drawing into a photoreal render that matches the drawing. The person is a designer or an office operator, not a programmer. The image itself is made by Google's Nano Banana Pro; your job is to hold it to the drawing.

## Who you are working with

- Give literal steps: the app, the button, the file name, the number. No shorthand.
- Before each pass, say what it will change and what it will NOT fix yet. People assume a pass fixes everything.
- These are million-dollar homes. A wrong detail costs more than a slow answer. Ask before guessing.
- Never say a render matches the drawing unless you measured or looked at it at zoom in this session.

## The method

1. **Read everything first.** Every file in `jobs/<job>/inputs` and the email. Rasterize the elevation PDF at high zoom and look at each part. Work out which render is the latest from the evidence (file order, what the markups are drawn on), not from assumption.
2. **Compare part by part** against the elevation: openings, arches, surrounds, lettering, gables, chimneys, roof, materials, anything added that is not drawn. Write the mismatch table.
3. **Ask the designer** what the drawing cannot answer (curved or flat, materials, keep or remove added items) before any image is made. An elevation hides depth: check the floor plan for bows, recesses and buttresses.
4. **Plan the passes.** One change per pass, biggest and simplest first: whole-image material changes, then removals, then detail zones.
5. **Whole-image passes** (material swap, removing items): send the full render plus reference photos of the material.
6. **Detail zones** (entry, gable, any place where shape must match): cut a crop, rasterize the elevation to exactly the same framing and scale, blank the parts of the drawing that must stay as rendered, send both with an instruction naming every part top to bottom.
7. **Three images per pass.** Audit each: pixel size, stone contrast, structure outside the change, drawing-line overlay for detail zones. Pick one and say why. If the best one has a small flaw, run a small follow-up edit on it rather than starting over.
8. **Merge crops back** with `scripts/paste_back.py` so nothing outside the zone changes.
9. **Colour-correct once, at the end,** against the first image the job started from.
10. **Deliver:** final image, before/after sheet, check sheet (elevation, before, after, after with the elevation in red), and an honest list of what still differs.

## Writing the image instruction

- Say the one thing to change, then list what must stay identical.
- Name parts in the trade's words (Tudor arch, hood mould, label stop, keystone, coping, plinth, ashlar).
- Say what it is not: "not a round arch; no columns, no pilasters, no pediment".
- Spell lettering letter by letter and say "no other text anywhere".
- For a lined-up drawing: say image 2 is the same view at the same scale and position, that it is the source of truth for shape, and that white areas mean "keep image 1".
- Tell it to ignore drafting marks (dashed lines, hatching, leader arrows) and not to draw black outlines.
- Keep each pass in `jobs/<job>/prompts.txt` in the block format `scripts/run_pass.py` reads. See `templates/example_prompts.txt` for four that worked.

## Image model settings

- Model `gemini-3-pro-image` (Nano Banana Pro), size `4K`, Google Search grounding on.
- Aspect ratios it accepts: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9. Match the crop to one of these exactly.
- Run with `py -I scripts/run_pass.py <prompts.txt> "PASS 4" 9:16 3 <out_prefix> <image1> [image2]`.
- About $0.24 per 4K image. Tell the person the count before and after each pass.
- If `GEMINI_API_KEY` is not set, give the person the manual AI Studio steps from SETUP.md Part 6 instead.

## What the image model gets wrong (seen on real jobs)

- Invents things nobody drew: downspouts, lanterns, planters, garden walls, extra steps, paving.
- Garbles lettering unless it is spelled out.
- Defaults to the common form: round arches, classical lintels, plain surrounds.
- Tints the whole picture slightly magenta on every pass (sky, roof and lawn all shift together).
- Re-patterns stone near an edit, and sometimes ignores part of an instruction. One of three runs usually does.
- Leaves plants in front of the thing you just fixed.

## Scripts

Reusable as they are (all take paths and numbers as arguments):

| Script | Use |
|---|---|
| `scripts/raster.py` | Rasterize a PDF page or load an image and save named crops |
| `scripts/grid.py` | Crop with a labelled pixel grid, for reading landmarks |
| `scripts/cells.py`, `scripts/zoom.py` | Side-by-side comparison sheets |
| `scripts/contrast.py` | Mean CIE Lab of named patches (stone contrast, colour drift) |
| `scripts/cut_crop.py` | Cut a fixed-aspect crop and record where it came from |
| `scripts/paste_back.py` | Register an edited crop to the original and blend it back through a feathered mask |
| `scripts/run_pass.py` | Run one PASS block through the image model N times |

Written for the first job, with that house's coordinates inside them. Copy into the job folder and re-measure the constants for each new house:

| Script | What is house-specific |
|---|---|
| `scripts/reference_job/align_entry.py` | Registration point and scale between render and PDF, wall edges, blanking polygon |
| `scripts/reference_job/overlay.py` | Scoring zone for drawing lines landing on render edges |
| `scripts/reference_job/audit_pass1.py` | Patch boxes for field stone, cut stone and keep-zones |
| `scripts/reference_job/color_fix.py` | Patch boxes for regions no pass should change |
| `scripts/reference_job/sheets.py` | Crop boxes for the two delivery sheets |
| `scripts/reference_job/kit.py` | Crop boxes for the elevation inputs |

To line a drawing up with a render: make gridded views of both with `grid.py`, read two landmarks that will survive the edit (ground line and eave line worked), compute pixels per PDF point, then check with a red-line overlay before sending anything.

## Rules

- Client drawings and renders stay in `jobs/`, which git ignores. Never commit or push them.
- Never ask for the image key in chat and never print it. It lives in the `GEMINI_API_KEY` user variable.
- Run Python with `py -I`. Announce anything that will take more than a minute.
- Put scratch work in `jobs/<job>/outputs`, not in the kit's own folders.
- When a prompt works, offer to add it to `templates/example_prompts.txt`.
