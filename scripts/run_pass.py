"""Run one pass of prompts.txt through the Gemini image model N times and save the results.

usage: run_pass.py <prompts.txt> <"PASS 4"> <aspect e.g. 9:16> <n_runs> <out_prefix> <image1> [image2 ...]
Key: read from the GEMINI_API_KEY user environment variable (never printed).
Images go first, in the order given, then the prompt text - the same order as the manual AI Studio runs.
"""
import base64
import os
import sys
import time
import winreg
from pathlib import Path

MODEL = "gemini-3-pro-image"  # Nano Banana Pro
SIZE = "4K"
PRICE_4K = 0.24  # USD per image, from Google's pricing page as summarized 2026-11-25 (not verified line by line)

prompts, pass_name, aspect, n, prefix = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
images = sys.argv[6:]


def get_key():
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    try:  # setx writes here; processes started before setx do not see it in os.environ
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
            return winreg.QueryValueEx(h, "GEMINI_API_KEY")[0]
    except OSError:
        return None


def get_prompt():
    lines = Path(prompts).read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(pass_name + " "))
    body_from = next(i for i in range(start, len(lines)) if lines[i].startswith("-----")) + 1
    body_to = next(i for i in range(body_from, len(lines)) if lines[i].startswith("====="))
    return "\n".join(lines[body_from:body_to]).strip()


text = get_prompt()
print(f"{pass_name}: prompt {len(text)} characters, starts: {text[:70]!r}")
print("images:", [Path(p).name for p in images], "| aspect", aspect, "| size", SIZE, "| runs", n, f"| est. cost ${n * PRICE_4K:.2f}")
if "--dry" in os.environ.get("RUN_PASS_FLAGS", ""):
    sys.exit(0)

key = get_key()
if not key:
    sys.exit("GEMINI_API_KEY is not set. Nothing was sent.")

from google import genai  # noqa: E402

client = genai.Client(api_key=key)
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
parts = [{"type": "image", "data": base64.b64encode(Path(p).read_bytes()).decode("ascii"), "mime_type": MIME[Path(p).suffix.lower()]} for p in images]
parts.append({"type": "text", "text": text})

start = int(os.environ.get("RUN_PASS_START", "1"))  # number of the first output file
for i in range(start, start + n):
    t0 = time.time()
    try:
        inter = client.interactions.create(
            model=MODEL,
            input=parts,
            tools=[{"type": "google_search"}],
            response_format={"type": "image", "aspect_ratio": aspect, "image_size": SIZE},
        )
    except Exception as e:  # report and stop: do not keep spending on a failing call
        sys.exit(f"run {i} failed: {type(e).__name__}: {str(e)[:500]}")
    last = None
    for step in inter.steps:
        if step.type != "model_output":
            continue  # skips interim 'thought' images
        for block in step.content:
            if block.type == "image":
                last = block
    if last is None:
        sys.exit(f"run {i}: the model returned no image")
    ext = ".png" if "png" in (getattr(last, "mime_type", "") or "") else ".jpg"
    out = Path(f"{prefix}{i}{ext}")
    out.write_bytes(base64.b64decode(last.data))
    print(f"run {i}: saved {out.name} ({out.stat().st_size // 1024} KB) in {time.time() - t0:.0f}s")
