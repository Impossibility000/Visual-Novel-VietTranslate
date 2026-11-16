import os
import sys
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
        self._current_mci_alias: Optional[str] = None
        self._lock = threading.Lock()

    def get_available_voices(self) -> Dict[str, str]:
        return dict(self.VOICE_LIST)

    def is_playing(self) -> bool:
        return self._is_playing

    def stop(self) -> None:
        self._is_playing = False
        if self._current_mci_alias and sys.platform == "win32":
            try:
                import ctypes
                alias = self._current_mci_alias
                ctypes.windll.winmm.mciSendStringW(f'stop {alias}', None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
                self._current_mci_alias = None
            except Exception:
                pass

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
                    self._play_audio_file(temp_path)
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

    def _play_audio_file(self, file_path: str) -> None:
        """Low-latency audio playback: uses native WinMM MCI (0ms delay) with PowerShell fallback."""
        if sys.platform == "win32":
            try:
                import ctypes
                winmm = ctypes.windll.winmm
                kernel32 = ctypes.windll.kernel32

                # Convert to short 8.3 path to prevent space/Unicode parsing issues in MCI
                buf = ctypes.create_unicode_buffer(500)
                kernel32.GetShortPathNameW(file_path, buf, 500)
                short_path = buf.value or file_path

                alias = f"tts_{os.getpid()}_{id(threading.current_thread())}"
                winmm.mciSendStringW(f'close {alias}', None, 0, None)
                open_cmd = f'open "{short_path}" type mpegvideo alias {alias}'
                res = winmm.mciSendStringW(open_cmd, None, 0, None)
                if res == 0:
                    self._current_mci_alias = alias
                    winmm.mciSendStringW(f'play {alias} wait', None, 0, None)
                    winmm.mciSendStringW(f'close {alias}', None, 0, None)
                    self._current_mci_alias = None
                    return
                else:
                    logger.warning(f"WinMM MCI open code {res}, falling back to PowerShell player.")
            except Exception as e:
                logger.warning(f"Native WinMM player error: {e}, falling back to PowerShell.")

        # Fallback to PowerShell WMPlayer
        try:
            import subprocess
            cmd = [
                "powershell", "-c",
                f"(New-Object Media.SoundPlayer '{file_path}').PlaySync()" if file_path.endswith(".wav") else
                f"$wm = New-Object -ComObject WMPlayer.OCX; $wm.URL = '{file_path}'; $wm.controls.play(); while($wm.playState -ne 1){{Start-Sleep -Milliseconds 100}}"
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error(f"Fallback audio player error: {e}")
