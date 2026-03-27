@echo off
REM ================================================================
REM MoneyPrinterTurbo Fix Script — All 4 Issues (26/03/2026)
REM ================================================================
REM Run from: D:\Projects\MoneyPrinterTurbo\
REM Make sure venv is activated first: .\venv\Scripts\Activate
REM ================================================================

echo ============================================
echo  MoneyPrinterTurbo Fix Script
echo  Fixing: Edge TTS, CUDA, Gemini LLM
echo ============================================
echo.

REM ================================================================
REM FIX 2: Edge TTS 403 Forbidden
REM Root cause: edge-tts 6.1.19 (from requirements.txt) uses a
REM TrustedClientToken that Microsoft has revoked.
REM Older 6.1.10 may also be blocked.
REM Fix: Install latest edge-tts which has updated token.
REM ================================================================
echo [FIX 2] Fixing Edge TTS 403...
pip install edge-tts --upgrade --force-reinstall
echo.
echo Testing Edge TTS...
edge-tts --text "Hello testing one two three" --voice en-US-GuyNeural --write-media test_edge.mp3
if exist test_edge.mp3 (
    for %%A in (test_edge.mp3) do (
        if %%~zA GTR 1000 (
            echo [OK] Edge TTS working! File size: %%~zA bytes
        ) else (
            echo [WARN] Edge TTS file too small. May need alternative fix.
            echo        See MANUAL_FIXES.md for SiliconFlow TTS option.
        )
    )
) else (
    echo [FAIL] Edge TTS still broken. See MANUAL_FIXES.md
)
del test_edge.mp3 2>nul
echo.

REM ================================================================
REM FIX 2b: Fix mktimestamp import error (edge-tts version mismatch)
REM The repo imports from edge_tts.submaker which changed between versions
REM ================================================================
echo [FIX 2b] Checking mktimestamp compatibility...
python -c "from edge_tts.submaker import mktimestamp; print('[OK] mktimestamp import works')" 2>nul
if errorlevel 1 (
    echo [WARN] mktimestamp not found in current edge-tts version
    echo        Applying compatibility patch...
    python fix_edge_compat.py
)
echo.

REM ================================================================
REM FIX 3: Whisper CUDA missing cublas64_12.dll
REM Root cause: faster-whisper needs cuBLAS from NVIDIA
REM Fix: Install nvidia-cublas-cu12 via pip (no full CUDA Toolkit needed)
REM ================================================================
echo [FIX 3] Installing CUDA libraries for Whisper...
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
echo.
echo Testing Whisper CUDA...
python -c "from faster_whisper import WhisperModel; m = WhisperModel('tiny', device='cuda', compute_type='float16'); print('[OK] Whisper CUDA working!')" 2>nul
if errorlevel 1 (
    echo [WARN] Whisper CUDA still failing. Trying alternative...
    pip install ctranslate2 --upgrade --force-reinstall
    echo        If still failing, see MANUAL_FIXES.md for CUDA Toolkit install.
)
echo.

echo ============================================
echo  Fix script complete. Now:
echo  1. Edit config.toml (see below)
echo  2. Restart: .\webui.bat
echo ============================================
pause
