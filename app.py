"""Main application logic for YouTube Downloader."""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from ui import YTDLP_Qt, DARK_THEME_STYLESHEET


def main():
    """Entry point for the application."""
    
    # Set application style (optional)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_THEME_STYLESHEET)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_candidates = [
        os.path.join(base_dir, "icon.ico"),
        os.path.join(base_dir, "icon.png"),
    ]
    for icon_path in icon_candidates:
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            break
    
    # Create and show main window
    window = YTDLP_Qt()
    window.show()
    
    # Run application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
