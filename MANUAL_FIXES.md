# Manual Fixes Guide — MoneyPrinterTurbo Issues (26/03/2026)

## Issue 1: LLM only returns subject, not full script

### Root cause
TTS correctly reads whatever text it receives. The problem is UPSTREAM —
the LLM (Ollama) failed to generate a full script, so `video_script` only
contains the subject line like "5 interesting things in Japan".

This happens because:
- Ollama is slow/timing out (qwen2.5:7b sometimes takes 30s+ for long prompts)
- `_generate_response()` strips all newlines with `content.replace("\n", "")`
  which can break formatting
- Error responses get passed through as the "script"

### Fix A: Use Gemini Flash for script generation (RECOMMENDED)
```toml
# config.toml
llm_provider = "gemini"
gemini_api_key = "AIzaSy..."
gemini_model_name = "gemini-2.0-flash"
```
Gemini Flash: free (1500 requests/day), fast (2-3s), high quality scripts.
Get key: https://aistudio.google.com/apikey

### Fix B: Test LLM is working before generating video
Open PowerShell, activate venv, run:
```powershell
cd D:\Projects\MoneyPrinterTurbo
.\venv\Scripts\Activate
python -c "
from app.services import llm
script = llm.generate_script('5 interesting facts about Japan', 'English', 1)
print('Script length:', len(script))
print('---')
print(script[:500])
"
```
If script length < 50 characters → LLM is broken.
If script length > 200 characters → LLM is fine, issue is elsewhere.

### Fix C: Paste script manually (workaround)
In WebUI, the "Video Script" textarea — paste your own script directly.
When this field has text, the tool skips LLM and uses your script as-is.
You can generate scripts with Claude or ChatGPT, then paste.

### Fix D: Check WebUI log for actual error
The terminal running webui.bat shows ALL logs. Look for:
  "failed to generate script"
  "Error:"
  "timeout"
These tell you exactly why the LLM failed.


## Issue 2: Edge TTS 403 Forbidden

### Root cause
Microsoft periodically revokes the TrustedClientToken used by edge-tts.
This affects all versions — it's a cat-and-mouse game between the
edge-tts maintainers and Microsoft's auth servers.

### Fix A: Upgrade edge-tts to latest
```powershell
pip install edge-tts --upgrade --force-reinstall
edge-tts --text "Hello test" --voice en-US-GuyNeural --write-media test.mp3
```
Check if test.mp3 has audio (should be 50-100KB for this short text).

### Fix B: Pin working version
If latest is broken but an older version worked:
```powershell
pip install edge-tts==6.1.10
```
Or try the version right before the one that broke.

### Fix C: Fix mktimestamp ImportError
If upgrading edge-tts causes ImportError on mktimestamp:
```powershell
python fix_edge_compat.py
```
This patches voice.py to handle both old and new edge-tts versions.

### Fix D: Use SiliconFlow TTS (free alternative, stable in Asia)
If Edge TTS is completely blocked:
1. Register at https://siliconflow.cn → get free API key
2. In config.toml:
   ```toml
   [siliconflow]
   api_key = "sk-..."
   ```
3. In WebUI voice dropdown, select voices starting with "siliconflow:"
   e.g., "siliconflow:FunAudioLLM/CosyVoice2-0.5B:alex-Male"

### Fix E: Use Gemini TTS
If you already have a Gemini API key:
1. In WebUI voice dropdown, select voices starting with "gemini:"
   e.g., "gemini:Kore-Female", "gemini:Puck-Male"
2. Note: Gemini TTS creates ONE subtitle entry for entire audio
   (word-level subtitle timing not available). Use Whisper for subtitles:
   ```toml
   subtitle_provider = "whisper"
   ```


## Issue 3: Whisper CUDA missing cublas64_12.dll

### Root cause
faster-whisper uses CTranslate2 which needs NVIDIA cuBLAS libraries.
These are NOT included with the NVIDIA display driver — need separate install.

### Fix A: pip install NVIDIA libraries (easiest, no CUDA Toolkit needed)
```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```
Then test:
```powershell
python -c "from faster_whisper import WhisperModel; m = WhisperModel('tiny', device='cuda', compute_type='float16'); print('OK')"
```

### Fix B: If Fix A fails — install cuBLAS manually
```powershell
pip install ctranslate2 --upgrade --force-reinstall
```

### Fix C: If still failing — install CUDA Toolkit 12
Download from: https://developer.nvidia.com/cuda-12-0-0-download-archive
Install: Custom → check only "CUDA Runtime" and "cuBLAS"
(Don't need full toolkit — just these 2 components, ~1GB)

After install, verify:
```powershell
where cublas64_12.dll
```
Should show path in CUDA install directory.

### Fix D: Fall back to CPU (no fix needed, just slower)
```toml
# config.toml
[whisper]
model_size = "medium"     # Use medium instead of large-v3 for CPU
device = "cpu"            # Skip GPU entirely
compute_type = "int8"     # Fastest CPU mode

### Fix E: Skip Whisper entirely
If using Edge TTS (not Gemini TTS), subtitles come from Edge TTS
WordBoundary events — no Whisper needed:
```toml
subtitle_provider = "edge"
```
Whisper is only needed when:
- Using Gemini TTS or SiliconFlow TTS (no built-in word timing)
- Using custom audio (your own voice recording)


## Issue 4: Hallucination (AI makes up wrong facts)

### Root cause
7B models hallucinate more than larger models, especially on specific
geographic/historical facts. The default prompt has no factual constraints.

### Fix A: Add factual constraint to prompt
Edit app/services/llm.py, in generate_script() prompt, add:
```
9. IMPORTANT: Only include facts you are confident about. Do not invent
   specific names, dates, locations, or statistics. If unsure about a
   specific detail, use general language instead.
```

### Fix B: Use larger/better model
- Gemini Flash (recommended): much less hallucination than 7B local
- Ollama qwen2.5:14b: better than 7b but needs ~10GB VRAM
- DeepSeek via API: strong factual accuracy

### Fix C: Human review step
For factual content (Japan life tips, tech facts):
1. Generate script first (stop_at="script" in API, or just read the
   Script textarea in WebUI)
2. Review facts manually (30 seconds)
3. Fix any errors in the textarea
4. Then generate video

This is the most reliable approach. AI-generated factual content should
ALWAYS be reviewed before publishing — regardless of model size.


## Recommended config.toml after all fixes

```toml
[app]
video_source = "pexels"
pexels_api_keys = ["YOUR_PEXELS_KEY"]

# LLM: Gemini Flash (free, fast, good quality)
llm_provider = "gemini"
gemini_api_key = "YOUR_GEMINI_KEY"
gemini_model_name = "gemini-2.0-flash"

# Subtitle: edge (if Edge TTS works) or whisper (if using Gemini TTS)
subtitle_provider = "edge"

# ImageMagick
imagemagick_path = "C:/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"

[whisper]
model_size = "large-v3"
device = "cuda"
compute_type = "float16"
```

Voice selection in WebUI:
- If Edge TTS works: choose "vi-VN-HoaiMyNeural" or "en-US-GuyNeural"
- If Edge TTS 403: choose "gemini:Kore-Female" or SiliconFlow voices


## Priority order for tonight

1. Set Gemini as LLM provider → fixes Issue 1 + Issue 4 (better scripts)
2. Test Edge TTS → if still 403, use Gemini TTS voices
3. Fix CUDA → nice to have, not blocking (use subtitle_provider="edge")
4. Generate first complete video with working pipeline
