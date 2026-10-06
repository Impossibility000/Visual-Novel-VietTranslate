import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.app_controller import AppController

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s"
    )
    
    # Enable High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("AetherVN Realtime AI Translator")
    app.setOrganizationName("AetherVN")
    
    controller = AppController(settings_path="config/settings.json")
    controller.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
