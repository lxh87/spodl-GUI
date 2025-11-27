#!/usr/bin/env python3
"""
SpotDL Desktop GUI v2.4.1
A modern desktop interface for SpotDL - PySide6 version
Refactored modular architecture
"""

import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("SpotDL GUI")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# Legacy compatibility - redirect old class name to new one
SpotDLGUI = MainWindow
