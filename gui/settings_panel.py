"""
Settings Panel Module
Settings tab containing download configuration and SpotDL installation
"""

import subprocess
import sys
import threading
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSlider, QFrame, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from typing import Dict, Any


class SettingsPanel(QWidget):
    """
    Panel for application settings
    Contains download folder, templates, threads, and SpotDL installation
    """

    # Signals
    settings_changed = Signal()  # Emitted when any setting changes
    save_settings_clicked = Signal()  # Emitted when save button is clicked

    def __init__(self, settings: Dict[str, Any], parent=None):
        """
        Initialize settings panel

        Args:
            settings: Dictionary of current settings
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings = settings
        self._setup_ui()

    def _setup_ui(self):
        """Setup the panel UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #1a1a1a; }")

        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        # Download folder
        folder_section = self._create_settings_section("Download Folder")
        folder_layout = folder_section.layout()

        folder_row = QHBoxLayout()
        self.folder_entry = QLineEdit()
        self.folder_entry.setText(self.settings.get("download_folder", str(Path.home() / "Music")))
        self.folder_entry.textChanged.connect(lambda: self.settings_changed.emit())
        folder_row.addWidget(self.folder_entry)

        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("background-color: #333; padding: 5px 10px;")
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(browse_btn)
        folder_layout.addLayout(folder_row)

        layout.addWidget(folder_section)

        # Song template
        song_section = self._create_settings_section("Song Template")
        song_layout = song_section.layout()

        song_help = QLabel("Use / to create folders. Click tags to insert.")
        song_help.setStyleSheet("color: #555; font-size: 8pt;")
        song_layout.addWidget(song_help)

        self.template_entry = QLineEdit()
        self.template_entry.setText(
            self.settings.get("output", "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}")
        )
        self.template_entry.textChanged.connect(lambda: self._update_template_example())
        self.template_entry.textChanged.connect(lambda: self.settings_changed.emit())
        song_layout.addWidget(self.template_entry)

        self.example_output_label = QLabel("Preview: The Weeknd/2020 - After Hours/03 - Blinding Lights.mp3")
        self.example_output_label.setStyleSheet("color: #4CAF50; font-size: 8pt;")
        song_layout.addWidget(self.example_output_label)

        # Song tags
        song_tags_row = QHBoxLayout()
        song_tags_row.setSpacing(2)
        for tag in ["{artist}", "{album}", "{title}", "{year}", "{track-number}", "{album-artist}", "{output-ext}"]:
            btn = self._create_tag_button(tag, self.template_entry, self._update_template_example)
            song_tags_row.addWidget(btn)
        song_tags_row.addStretch()
        song_layout.addLayout(song_tags_row)

        layout.addWidget(song_section)

        # Playlist template
        playlist_section = self._create_settings_section("Playlist Template")
        playlist_layout = playlist_section.layout()

        self.playlist_template_entry = QLineEdit()
        self.playlist_template_entry.setText(
            self.settings.get("playlist_output", "{list-name}/{list-position} - {artists} - {title}.{output-ext}")
        )
        self.playlist_template_entry.textChanged.connect(lambda: self._update_playlist_example())
        self.playlist_template_entry.textChanged.connect(lambda: self.settings_changed.emit())
        playlist_layout.addWidget(self.playlist_template_entry)

        self.playlist_example_label = QLabel("Preview: My Playlist/05 - The Weeknd - Blinding Lights.mp3")
        self.playlist_example_label.setStyleSheet("color: #4CAF50; font-size: 8pt;")
        playlist_layout.addWidget(self.playlist_example_label)

        # Playlist tags
        playlist_tags_row = QHBoxLayout()
        playlist_tags_row.setSpacing(2)
        for tag in ["{list-name}", "{list-position}", "{artists}", "{title}", "{year}", "{output-ext}"]:
            btn = self._create_tag_button(tag, self.playlist_template_entry, self._update_playlist_example)
            playlist_tags_row.addWidget(btn)
        playlist_tags_row.addStretch()
        playlist_layout.addLayout(playlist_tags_row)

        layout.addWidget(playlist_section)

        # Threads
        threads_section = self._create_settings_section("Concurrent Downloads")
        threads_layout = threads_section.layout()

        threads_row = QHBoxLayout()
        self.threads_slider = QSlider(Qt.Horizontal)
        self.threads_slider.setMinimum(1)
        self.threads_slider.setMaximum(16)
        self.threads_slider.setValue(int(self.settings.get("threads", "4")))
        self.threads_slider.valueChanged.connect(lambda v: self.threads_value_label.setText(str(v)))
        self.threads_slider.valueChanged.connect(lambda: self.settings_changed.emit())
        threads_row.addWidget(self.threads_slider)

        self.threads_value_label = QLabel(str(self.threads_slider.value()))
        self.threads_value_label.setStyleSheet("font-weight: bold; min-width: 20px;")
        threads_row.addWidget(self.threads_value_label)
        threads_layout.addLayout(threads_row)

        layout.addWidget(threads_section)

        # Save button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setFixedHeight(34)
        save_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        save_btn.clicked.connect(self.save_settings_clicked.emit)
        layout.addWidget(save_btn)

        # SpotDL status
        spotdl_section = self._create_settings_section("SpotDL Installation")
        spotdl_layout = spotdl_section.layout()

        self.spotdl_status_label = QLabel("Checking...")
        self.spotdl_status_label.setStyleSheet("color: #888;")
        spotdl_layout.addWidget(self.spotdl_status_label)

        btn_row = QHBoxLayout()
        check_btn = QPushButton("Check")
        check_btn.setStyleSheet("background-color: #333;")
        check_btn.clicked.connect(self.check_spotdl_installation)
        btn_row.addWidget(check_btn)

        install_btn = QPushButton("Install SpotDL")
        install_btn.clicked.connect(self._install_spotdl)
        btn_row.addWidget(install_btn)
        btn_row.addStretch()
        spotdl_layout.addLayout(btn_row)

        layout.addWidget(spotdl_section)
        layout.addStretch()

        scroll.setWidget(settings_widget)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Check SpotDL on init
        QTimer.singleShot(100, self.check_spotdl_installation)

    def _create_settings_section(self, title: str) -> QFrame:
        """Create a styled settings section"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border-radius: 5px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 8, 10, 8)

        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; font-size: 9pt;")
        layout.addWidget(label)

        return frame

    def _create_tag_button(self, tag: str, entry: QLineEdit, update_func) -> QPushButton:
        """Create a compact tag button"""
        btn = QPushButton(tag)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                font-size: 7pt;
                padding: 2px 4px;
                min-width: 30px;
            }
            QPushButton:hover { background-color: #4CAF50; }
        """)
        btn.setFixedHeight(18)
        btn.clicked.connect(lambda: self._insert_tag(entry, tag, update_func))
        return btn

    def _insert_tag(self, entry: QLineEdit, tag: str, update_func):
        """Insert tag at cursor position"""
        pos = entry.cursorPosition()
        text = entry.text()
        entry.setText(text[:pos] + tag + text[pos:])
        entry.setCursorPosition(pos + len(tag))
        update_func()

    def _update_template_example(self):
        """Update song template preview"""
        template = self.template_entry.text()
        replacements = {
            "{album-artist}": "The Weeknd", "{artist}": "The Weeknd", "{artists}": "The Weeknd",
            "{album}": "After Hours", "{title}": "Blinding Lights", "{year}": "2020",
            "{track-number}": "03", "{disc-number}": "1", "{output-ext}": "mp3",
            "{genre}": "Pop", "{isrc}": "USUG11902768", "{publisher}": "Republic"
        }
        for k, v in replacements.items():
            template = template.replace(k, v)
        self.example_output_label.setText(f"Preview: {template}")

    def _update_playlist_example(self):
        """Update playlist template preview"""
        template = self.playlist_template_entry.text()
        replacements = {
            "{list-name}": "My Playlist", "{list-position}": "05", "{list-length}": "50",
            "{artist}": "The Weeknd", "{artists}": "The Weeknd", "{album}": "After Hours",
            "{title}": "Blinding Lights", "{year}": "2020", "{output-ext}": "mp3"
        }
        for k, v in replacements.items():
            template = template.replace(k, v)
        self.playlist_example_label.setText(f"Preview: {template}")

    def _browse_folder(self):
        """Open folder browser dialog"""
        if folder := QFileDialog.getExistingDirectory(self, "Select Folder"):
            self.folder_entry.setText(folder)

    def check_spotdl_installation(self):
        """Check if SpotDL is installed and get version"""
        try:
            result = subprocess.run(["spotdl", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.spotdl_status_label.setText(f"✅ {result.stdout.strip()}")
                self.spotdl_status_label.setStyleSheet("color: #4CAF50;")
            else:
                self.spotdl_status_label.setText("❌ Not working")
                self.spotdl_status_label.setStyleSheet("color: #F44336;")
        except:
            self.spotdl_status_label.setText("❌ Not installed")
            self.spotdl_status_label.setStyleSheet("color: #F44336;")

    def _install_spotdl(self):
        """Install SpotDL using pip"""
        def run():
            subprocess.run([sys.executable, "-m", "pip", "install", "spotdl"])
            QTimer.singleShot(0, self.check_spotdl_installation)
        threading.Thread(target=run, daemon=True).start()

    def get_settings(self) -> Dict[str, Any]:
        """
        Get current settings from the panel

        Returns:
            Dictionary of settings
        """
        return {
            'download_folder': self.folder_entry.text(),
            'output': self.template_entry.text(),
            'playlist_output': self.playlist_template_entry.text(),
            'threads': str(self.threads_slider.value())
        }

    def get_download_folder(self) -> str:
        """Get download folder path"""
        return self.folder_entry.text()

    def get_song_template(self) -> str:
        """Get song template"""
        return self.template_entry.text()

    def get_playlist_template(self) -> str:
        """Get playlist template"""
        return self.playlist_template_entry.text()

    def get_threads(self) -> int:
        """Get thread count"""
        return self.threads_slider.value()

    def update_version_display(self, version: str):
        """
        Update SpotDL version display

        Args:
            version: Version string to display
        """
        self.spotdl_status_label.setText(f"✅ {version}")
        self.spotdl_status_label.setStyleSheet("color: #4CAF50;")
