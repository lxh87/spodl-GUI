"""
Theme Module
Qt stylesheets for the SpotDL GUI
"""


def get_dark_theme_stylesheet() -> str:
    """
    Get the dark theme stylesheet for the application

    Returns:
        Qt stylesheet string
    """
    return """
        QMainWindow, QWidget {
            background-color: #1a1a1a;
            color: #e0e0e0;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }

        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #45a049; }
        QPushButton:pressed { background-color: #3d8b40; }
        QPushButton:disabled { background-color: #2b2b2b; color: #555; }

        QLineEdit, QTextEdit {
            background-color: #252525;
            color: #e0e0e0;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 5px;
            selection-background-color: #4CAF50;
        }
        QLineEdit:focus, QTextEdit:focus { border: 1px solid #4CAF50; }
        QLineEdit:read-only { background-color: #1e1e1e; color: #888; }

        QComboBox {
            background-color: #252525;
            color: #e0e0e0;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 4px 8px;
            min-height: 22px;
        }
        QComboBox:hover { border: 1px solid #4CAF50; }
        QComboBox::drop-down { border: none; width: 20px; }
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #888;
            margin-right: 6px;
        }
        QComboBox QAbstractItemView {
            background-color: #252525;
            color: #e0e0e0;
            selection-background-color: #4CAF50;
            border: 1px solid #333;
        }

        QCheckBox {
            color: #e0e0e0;
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 14px; height: 14px;
            border: 1px solid #444;
            border-radius: 3px;
            background-color: #252525;
        }
        QCheckBox::indicator:hover { border: 1px solid #4CAF50; }
        QCheckBox::indicator:checked {
            background-color: #4CAF50;
            border: 1px solid #4CAF50;
        }

        QSlider::groove:horizontal {
            background-color: #252525;
            height: 6px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background-color: #4CAF50;
            width: 14px; height: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }
        QSlider::sub-page:horizontal {
            background-color: #4CAF50;
            border-radius: 3px;
        }

        QScrollBar:vertical {
            background-color: #1a1a1a;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background-color: #444;
            border-radius: 4px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover { background-color: #4CAF50; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

        QScrollBar:horizontal {
            background-color: #1a1a1a;
            height: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:horizontal {
            background-color: #444;
            border-radius: 4px;
            min-width: 30px;
        }
        QScrollBar::handle:horizontal:hover { background-color: #4CAF50; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

        QSplitter::handle {
            background-color: #333;
        }
        QSplitter::handle:hover { background-color: #4CAF50; }
        QSplitter::handle:horizontal { width: 3px; }
        QSplitter::handle:vertical { height: 3px; }

        QFrame { background-color: transparent; }
        QLabel { color: #e0e0e0; background: transparent; }
    """
