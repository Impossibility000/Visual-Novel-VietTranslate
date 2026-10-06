import os
import subprocess
import logging
from typing import Optional, List, Dict, Tuple, Any

logger = logging.getLogger("TextractorManager")

class TextractorManager:
    """Manages built-in portable Textractor binaries and game attachment."""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.join(os.getcwd(), "tools", "Textractor", "Textractor")
        self._process: Optional[subprocess.Popen] = None

    def get_executable_path(self, arch: str = "x86") -> Optional[str]:
        """Get path to Textractor.exe for the specified architecture ('x86' or 'x64')."""
        target_dir = os.path.join(self.base_dir, arch)
        exe_path = os.path.join(target_dir, "Textractor.exe")
        if os.path.exists(exe_path):
            return exe_path
        
        # Fallback search
        for root, dirs, files in os.walk(os.path.join(os.getcwd(), "tools")):
            if "Textractor.exe" in files and arch in root:
                return os.path.join(root, "Textractor.exe")
        return None

    def is_installed(self) -> bool:
        """Check if Textractor executable exists."""
        return self.get_executable_path("x86") is not None or self.get_executable_path("x64") is not None

    def launch_gui(self, arch: str = "x86") -> bool:
        """Launch the integrated Textractor graphical application."""
        exe = self.get_executable_path(arch)
        if not exe or not os.path.exists(exe):
            logger.error(f"Textractor executable not found for arch {arch}")
            return False
        
        try:
            cwd = os.path.dirname(exe)
            self._process = subprocess.Popen([exe], cwd=cwd)
            logger.info(f"Launched Textractor from {exe}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch Textractor: {e}")
            return False

    def list_running_processes(self) -> List[Dict[str, Any]]:
        """List running Windows applications that could be Visual Novel games."""
        procs = []
        try:
            import ctypes
            # Run tasklist via subprocess
            output = subprocess.check_output(
                ["tasklist", "/FO", "CSV", "/NH"],
                text=True, encoding="utf-8", errors="ignore"
            )
            for line in output.splitlines():
                parts = [p.strip(' "') for p in line.split('","')]
                if len(parts) >= 2:
                    name, pid_str = parts[0], parts[1]
                    if pid_str.isdigit():
                        pid = int(pid_str)
                        # Filter system processes
                        if not name.lower().startswith(("svchost", "system", "registry", "smss", "csrss", "wininit", "services", "lsass", "conhost", "python", "code", "explorer")):
                            procs.append({"pid": pid, "name": name})
        except Exception as e:
            logger.error(f"Error listing processes: {e}")
        return procs
