#!/usr/bin/env python3
"""
SpotDL Desktop GUI v2.4.3
A modern desktop interface for SpotDL - PySide6 version
Refactored modular architecture
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from gui.main_window import MainWindow


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("SpotDL GUI")
    
    # Set application icon for window and taskbar
    app_icon = QIcon("icon.png")
    app.setWindowIcon(app_icon)
    
    # Set taskbar-specific icon (Windows taskbar)
    if sys.platform == "win32":
        import ctypes
        # Load the icon for taskbar display
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SpotDL.GUI.v2.4.3")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# Legacy compatibility - redirect old class name to new one
SpotDLGUI = MainWindow
