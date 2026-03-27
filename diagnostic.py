#!/usr/bin/env python3
"""
Pipeline Diagnostic — Check all components in 30 seconds.
Run this BEFORE generating videos to confirm everything works.

Usage:
    cd D:\Projects\MoneyPrinterTurbo
    .\venv\Scripts\Activate
    python diagnostic.py
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.getcwd())

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
WARN = "\033[93m[WARN]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results = []

def check(name, fn):
    try:
        msg = fn()
        status = PASS
        results.append(("PASS", name))
    except Exception as e:
        msg = str(e)
        status = FAIL
        results.append(("FAIL", name))
    print(f"  {status} {name}: {msg}")


print("\n" + "="*60)
print("  MoneyPrinterTurbo — Pipeline Diagnostic")
print("="*60)

# --- 1. Config ---
print(f"\n{INFO} Checking config...")

def check_config():
    from app.config import config
    provider = config.app.get("llm_provider", "not set")
    pexels = config.app.get("pexels_api_keys", [])
    has_pexels = len(pexels) > 0 and pexels[0] != ""
    if not has_pexels:
        raise Exception("pexels_api_keys is empty")
    return f"llm_provider={provider}, pexels_keys={len(pexels)}"

check("Config loaded", check_config)

# --- 2. LLM ---
print(f"\n{INFO} Checking LLM (generating test script)...")

def check_llm():
    from app.services import llm
    script = llm.generate_script("3 facts about cats", "English", 1)
    if not script or len(script) < 30:
        raise Exception(f"Script too short ({len(script) if script else 0} chars): '{script[:80] if script else 'empty'}'")
    if "Error:" in script:
        raise Exception(f"LLM returned error: {script[:100]}")
    return f"{len(script)} chars — '{script[:60]}...'"

check("LLM script generation", check_llm)

# --- 3. Edge TTS ---
print(f"\n{INFO} Checking Edge TTS...")

def check_edge_tts():
    import edge_tts
    import tempfile

    async def _test():
        tmp = os.path.join(tempfile.gettempdir(), "diag_voice.mp3")
        communicate = edge_tts.Communicate("Hello this is a test", "en-US-GuyNeural")
        await communicate.save(tmp)
        size = os.path.getsize(tmp)
        os.remove(tmp)
        if size < 1000:
            raise Exception(f"Audio file too small: {size} bytes (probably 403 error)")
        return f"OK, {size} bytes"

    return asyncio.run(_test())

check("Edge TTS (en-US-GuyNeural)", check_edge_tts)

def check_edge_tts_vi():
    import edge_tts
    import tempfile

    async def _test():
        tmp = os.path.join(tempfile.gettempdir(), "diag_voice_vi.mp3")
        communicate = edge_tts.Communicate("Xin chao day la bai test", "vi-VN-HoaiMyNeural")
        await communicate.save(tmp)
        size = os.path.getsize(tmp)
        os.remove(tmp)
        if size < 1000:
            raise Exception(f"Audio too small: {size} bytes")
        return f"OK, {size} bytes"

    return asyncio.run(_test())

check("Edge TTS (vi-VN-HoaiMyNeural)", check_edge_tts_vi)

# --- 4. mktimestamp compatibility ---
print(f"\n{INFO} Checking edge-tts compatibility...")

def check_mktimestamp():
    try:
        from edge_tts.submaker import mktimestamp
        return "mktimestamp import OK"
    except ImportError:
        raise Exception("mktimestamp not found — run: python fix_edge_compat.py")

check("mktimestamp import", check_mktimestamp)

# --- 5. FFmpeg ---
print(f"\n{INFO} Checking FFmpeg...")

def check_ffmpeg():
    import subprocess
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
    first_line = result.stdout.split("\n")[0]
    return first_line

check("FFmpeg", check_ffmpeg)

# --- 6. ImageMagick ---
print(f"\n{INFO} Checking ImageMagick...")

def check_imagemagick():
    from app.config import config
    magick_path = config.app.get("imagemagick_path", "")
    if magick_path and os.path.exists(magick_path):
        return f"Found at {magick_path}"
    # Try system PATH
    import subprocess
    result = subprocess.run(["magick", "--version"], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        return result.stdout.split("\n")[0]
    raise Exception("ImageMagick not found. Set imagemagick_path in config.toml")

check("ImageMagick", check_imagemagick)

# --- 7. Whisper CUDA ---
print(f"\n{INFO} Checking Whisper + CUDA...")

def check_whisper_cuda():
    from faster_whisper import WhisperModel
    model = WhisperModel("tiny", device="cuda", compute_type="float16")
    return "CUDA OK (tested with tiny model)"

def check_whisper_cpu():
    from faster_whisper import WhisperModel
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return "CPU mode OK (GPU not available)"

try:
    check_whisper_cuda()
    print(f"  {PASS} Whisper CUDA: OK")
    results.append(("PASS", "Whisper CUDA"))
except Exception as e:
    print(f"  {WARN} Whisper CUDA: {e}")
    try:
        check_whisper_cpu()
        print(f"  {PASS} Whisper CPU fallback: OK")
        results.append(("PASS", "Whisper CPU"))
    except Exception as e2:
        print(f"  {FAIL} Whisper: {e2}")
        results.append(("FAIL", "Whisper"))

# --- 8. Pexels API ---
print(f"\n{INFO} Checking Pexels API...")

def check_pexels():
    import requests
    from app.config import config
    keys = config.app.get("pexels_api_keys", [])
    if not keys or keys[0] == "":
        raise Exception("No Pexels API key configured")
    headers = {"Authorization": keys[0]}
    r = requests.get(
        "https://api.pexels.com/videos/search?query=japan&per_page=1&orientation=portrait",
        headers=headers, timeout=15
    )
    if r.status_code == 200:
        data = r.json()
        total = data.get("total_results", 0)
        return f"API OK, {total} results for 'japan'"
    else:
        raise Exception(f"API returned {r.status_code}: {r.text[:100]}")

check("Pexels API", check_pexels)

# --- Summary ---
pass_count = sum(1 for s, _ in results if s == "PASS")
fail_count = sum(1 for s, _ in results if s == "FAIL")

print(f"\n{'='*60}")
print(f"  SUMMARY: {pass_count} PASS, {fail_count} FAIL")
if fail_count == 0:
    print(f"  {PASS} All systems go! Ready to generate videos.")
else:
    print(f"\n  Failed components:")
    for s, name in results:
        if s == "FAIL":
            print(f"    {FAIL} {name}")
    print(f"\n  See MANUAL_FIXES.md for solutions.")
print(f"{'='*60}\n")
