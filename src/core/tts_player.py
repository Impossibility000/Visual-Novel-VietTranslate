import os
import asyncio
import tempfile
import threading
import logging
from typing import Optional, List, Dict

logger = logging.getLogger("TTSPlayer")

class TTSPlayer:
    """High-quality voice player using Microsoft Edge-TTS."""
    
    VOICE_LIST = {
        "vi-VN-HoaiMyNeural": "Tiếng Việt (Nữ - Hoài My)",
        "vi-VN-NamMinhNeural": "Tiếng Việt (Nam - Nam Minh)",
        "ja-JP-NanamiNeural": "Tiếng Nhật (Nữ - Nanami)",
        "ja-JP-KeitaNeural": "Tiếng Nhật (Nam - Keita)",
        "ja-JP-AoiNeural": "Tiếng Nhật (Nữ - Aoi)",
        "en-US-JennyNeural": "English (Female - Jenny)",
        "en-US-GuyNeural": "English (Male - Guy)"
    }

    def __init__(self, default_voice: str = "vi-VN-HoaiMyNeural"):
        self.default_voice = default_voice
        self._is_playing = False
        self._current_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()

    def get_available_voices(self) -> Dict[str, str]:
        return dict(self.VOICE_LIST)

    def is_playing(self) -> bool:
        return self._is_playing

    def stop(self) -> None:
        self._is_playing = False

    def play_async(self, text: str, voice: Optional[str] = None, rate: str = "+0%") -> None:
        """Spawn background thread to generate and play TTS audio."""
        if not text or not text.strip():
            return
        
        target_voice = voice or self.default_voice
        thread = threading.Thread(
            target=self._run_tts,
            args=(text.strip(), target_voice, rate),
            daemon=True
        )
        thread.start()

    def _run_tts(self, text: str, voice: str, rate: str) -> None:
        try:
            import edge_tts
            
            async def _generate_and_play():
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
                    temp_path = tf.name
                
                try:
                    communicate = edge_tts.Communicate(text, voice, rate=rate)
                    await communicate.save(temp_path)
                    
                    self._is_playing = True
                    # Play using native Windows PowerShell / MediaPlayer command to avoid C++ sound driver dependencies
                    import subprocess
                    cmd = [
                        "powershell", "-c",
                        f"(New-Object Media.SoundPlayer '{temp_path}').PlaySync()" if temp_path.endswith(".wav") else
                        f"$wm = New-Object -ComObject WMPlayer.OCX; $wm.URL = '{temp_path}'; $wm.controls.play(); while($wm.playState -ne 1){{Start-Sleep -Milliseconds 100}}"
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                finally:
                    self._is_playing = False
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass

            asyncio.run(_generate_and_play())
        except Exception as e:
            logger.error(f"TTS playback error: {e}")
            self._is_playing = False
