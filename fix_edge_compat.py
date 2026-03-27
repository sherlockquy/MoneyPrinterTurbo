"""
Fix edge-tts mktimestamp import compatibility.
Newer edge-tts versions moved/removed mktimestamp from submaker.
This patches voice.py to handle both old and new versions.
"""
import re
from pathlib import Path

voice_file = Path("app/services/voice.py")
content = voice_file.read_text(encoding="utf-8")

# Replace the import line with a try/except
old_import = "from edge_tts.submaker import mktimestamp"
new_import = """try:
    from edge_tts.submaker import mktimestamp
except ImportError:
    # Newer edge-tts versions: mktimestamp moved or removed
    def mktimestamp(time_unit):
        hour = int(time_unit / 10000000 / 3600)
        minute = int((time_unit / 10000000 / 60) % 60)
        seconds = (time_unit / 10000000) % 60
        return f"{hour:02d}:{minute:02d}:{seconds:06.3f}\""""

if old_import in content:
    content = content.replace(old_import, new_import)
    voice_file.write_text(content, encoding="utf-8")
    print("[OK] Patched voice.py — mktimestamp compatibility fix applied")
else:
    print("[SKIP] voice.py already patched or import not found")
