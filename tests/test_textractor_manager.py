import unittest
import os
from src.core.textractor_manager import TextractorManager

class TestTextractorManager(unittest.TestCase):
    def test_textractor_installed(self):
        manager = TextractorManager()
        # Should detect the downloaded binaries
        self.assertTrue(manager.is_installed())
        self.assertTrue(os.path.exists(manager.get_executable_path("x86")))
        self.assertTrue(os.path.exists(manager.get_executable_path("x64")))

    def test_list_processes(self):
        manager = TextractorManager()
        procs = manager.list_running_processes()
        self.assertIsInstance(procs, list)

if __name__ == "__main__":
    unittest.main()
