#!/usr/bin/env python3
"""
SpotDL Desktop GUI
A modern desktop interface for SpotDL - PySide6 version
"""

import subprocess
import threading
import os
import json
from pathlib import Path
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLineEdit, QTextEdit, QLabel,
    QComboBox, QCheckBox, QSlider, QFrame, QFileDialog, QMessageBox,
    QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont, QTextCursor

# Lazy import metadata handler - only when needed
_metadata_handler = None

def get_metadata_handler():
    global _metadata_handler
    if _metadata_handler is None:
        from metadata_handler import SpotifyMetadataHandler
        _metadata_handler = SpotifyMetadataHandler()
    return _metadata_handler


class ThreadSafeLogger(QObject):
    """Thread-safe logger using Qt signals"""
    log_signal = Signal(str)

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.log_signal.connect(self._append_text)

    def _append_text(self, text):
        """Append text to widget (runs in main thread)"""
        self.text_widget.moveCursor(QTextCursor.End)
        self.text_widget.insertPlainText(text)
        self.text_widget.moveCursor(QTextCursor.End)

    def log(self, message):
        """Thread-safe logging"""
        self.log_signal.emit(message)


class SpotDLGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Config file location
        self.config_file = Path.home() / ".spotdl_gui_config.json"

        # Window setup
        self.setWindowTitle("SpotDL GUI")
        self.resize(1100, 1200)

        # Load settings first
        self.load_settings()

        # Apply dark theme
        self.apply_dark_theme()

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar with logo (no navigation buttons)
        self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Create tab widget for main content
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3d3d3d;
            }
        """)
        main_layout.addWidget(self.tab_widget, 1)

        # Initialize tabs
        self.create_download_tab()
        self.create_queue_tab()
        self.create_settings_tab()

        # Download queue
        self.download_queue = []
        self.current_process = None

        # Initialize command preview
        self.update_command_preview()

        # Defer non-critical startup tasks
        QTimer.singleShot(100, self.check_spotdl)

    def apply_dark_theme(self):
        """Apply comprehensive dark theme using QSS"""
        dark_stylesheet = """
            QMainWindow, QWidget {
                background-color: #1a1a1a;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
            }

            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 30px;
                min-width: 80px;
            }

            QPushButton:hover {
                background-color: #45a049;
            }

            QPushButton:pressed {
                background-color: #3d8b40;
            }

            QPushButton:disabled {
                background-color: #2b2b2b;
                color: #666666;
            }

            QPushButton.secondary {
                background-color: #424242;
            }

            QPushButton.secondary:hover {
                background-color: #4a4a4a;
            }

            QPushButton.danger {
                background-color: #f44336;
            }

            QPushButton.danger:hover {
                background-color: #da190b;
            }

            QLineEdit, QTextEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
                selection-background-color: #4CAF50;
            }

            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #4CAF50;
            }

            QLineEdit:read-only {
                background-color: #242424;
                color: #cccccc;
            }

            QComboBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 6px 10px;
                min-height: 30px;
            }

            QComboBox:hover {
                border: 1px solid #4CAF50;
            }

            QComboBox::drop-down {
                border: none;
                width: 30px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 10px;
            }

            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: white;
                selection-background-color: #4CAF50;
                border: 1px solid #3d3d3d;
            }

            QCheckBox {
                color: white;
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3d3d3d;
                border-radius: 4px;
                background-color: #2b2b2b;
            }

            QCheckBox::indicator:hover {
                border: 2px solid #4CAF50;
            }

            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 2px solid #4CAF50;
                image: none;
            }

            QSlider::groove:horizontal {
                background-color: #2b2b2b;
                height: 8px;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background-color: #4CAF50;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }

            QSlider::handle:horizontal:hover {
                background-color: #45a049;
            }

            QSlider::sub-page:horizontal {
                background-color: #4CAF50;
                border-radius: 4px;
            }

            QFrame {
                background-color: #242424;
                border-radius: 5px;
            }

            QLabel {
                color: white;
                background-color: transparent;
            }

            QLabel.title {
                font-size: 24pt;
                font-weight: bold;
            }

            QLabel.subtitle {
                font-weight: bold;
                font-size: 12pt;
            }

            QLabel.help {
                color: #999999;
                font-size: 9pt;
            }

            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #4CAF50;
                border-radius: 6px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #45a049;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar:horizontal {
                background-color: #1a1a1a;
                height: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:horizontal {
                background-color: #4CAF50;
                border-radius: 6px;
                min-width: 30px;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #45a049;
            }

            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """
        self.setStyleSheet(dark_stylesheet)

    def create_sidebar(self):
        """Create sidebar with logo (no navigation buttons)"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #242424;
                border-radius: 0px;
            }
        """)

        layout = QVBoxLayout(self.sidebar)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Logo
        self.logo_label = QLabel("🎵 SpotDL GUI")
        logo_font = QFont()
        logo_font.setPointSize(16)
        logo_font.setBold(True)
        self.logo_label.setFont(logo_font)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setWordWrap(True)
        layout.addWidget(self.logo_label)

        layout.addStretch()

    def load_settings(self):
        """Load settings from config file"""
        default_settings = {
            "format": "mp3",
            "bitrate": "320k",
            "playlist_output": "{list-name}/{list-position} - {artists} - {title}.{output-ext}",
            "threads": "4",
            "output": "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}",
            "audio_providers": ["youtube-music", "youtube"],
            "lyrics_providers": ["genius", "musixmatch"],
            "download_folder": str(Path.home() / "Music"),
            "theme": "dark",
            "create_folder_per_url": True,
            "playlist_folder_name": ""
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.settings = {**default_settings, **json.load(f)}
            except:
                self.settings = default_settings
        else:
            self.settings = default_settings

    def save_settings(self):
        """Save settings to config file"""
        try:
            # Update settings from UI
            self.settings["format"] = self.format_combo.currentText()
            self.settings["bitrate"] = self.bitrate_combo.currentText()
            self.settings["threads"] = str(self.threads_slider.value())
            self.settings["output"] = self.template_entry.text()
            self.settings["playlist_output"] = self.playlist_template_entry.text()
            self.settings["download_folder"] = self.folder_entry.text()
            self.settings["theme"] = "dark"  # Always dark in this version
            self.settings["create_folder_per_url"] = self.folder_per_url_check.isChecked()

            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)

            self.log_to_queue(f"✅ Settings saved to {self.config_file}\n")

            # Update command preview with new settings
            self.update_command_preview()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def closeEvent(self, event):
        """Handle window close event"""
        self.save_settings()
        event.accept()

    def check_spotdl(self):
        """Check if SpotDL is installed (initial check)"""
        try:
            result = subprocess.run(
                ["spotdl", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.logo_label.setText(f"🎵 SpotDL GUI\n{version}")
        except:
            QMessageBox.warning(
                self,
                "SpotDL Not Found",
                "SpotDL is not installed or not in PATH.\n\n"
                "Install it with: pip install spotdl\n"
                "Or use the Install button in Settings."
            )

    def check_spotdl_installation(self):
        """Check SpotDL installation status"""
        try:
            result = subprocess.run(
                ["spotdl", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.spotdl_status_label.setText(f"✅ SpotDL is installed: {version}")
                self.spotdl_status_label.setStyleSheet("color: #4CAF50;")
                self.logo_label.setText(f"🎵 SpotDL GUI\n{version}")
                return True
            else:
                self.spotdl_status_label.setText("❌ SpotDL is not working correctly")
                self.spotdl_status_label.setStyleSheet("color: #f44336;")
                return False
        except FileNotFoundError:
            self.spotdl_status_label.setText("❌ SpotDL is not installed")
            self.spotdl_status_label.setStyleSheet("color: #f44336;")
            return False
        except Exception as e:
            self.spotdl_status_label.setText(f"❌ Error checking SpotDL: {str(e)}")
            self.spotdl_status_label.setStyleSheet("color: #f44336;")
            return False

    def install_spotdl(self):
        """Install SpotDL using pip"""
        def install_thread():
            try:
                QTimer.singleShot(0, lambda: self.spotdl_status_label.setText("⏳ Installing SpotDL..."))
                QTimer.singleShot(0, lambda: self.spotdl_status_label.setStyleSheet("color: #FF9800;"))

                # Run pip install
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "spotdl"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    QTimer.singleShot(0, lambda: self.spotdl_status_label.setText("✅ SpotDL installed successfully!"))
                    QTimer.singleShot(0, lambda: self.spotdl_status_label.setStyleSheet("color: #4CAF50;"))
                    # Recheck installation
                    QTimer.singleShot(1000, self.check_spotdl_installation)
                else:
                    error_msg = result.stderr[:100] if result.stderr else "Unknown error"
                    QTimer.singleShot(0, lambda: self.spotdl_status_label.setText(f"❌ Installation failed: {error_msg}"))
                    QTimer.singleShot(0, lambda: self.spotdl_status_label.setStyleSheet("color: #f44336;"))
            except subprocess.TimeoutExpired:
                QTimer.singleShot(0, lambda: self.spotdl_status_label.setText("❌ Installation timed out"))
                QTimer.singleShot(0, lambda: self.spotdl_status_label.setStyleSheet("color: #f44336;"))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.spotdl_status_label.setText(f"❌ Installation error: {str(e)}"))
                QTimer.singleShot(0, lambda: self.spotdl_status_label.setStyleSheet("color: #f44336;"))

        # Run installation in a thread
        threading.Thread(target=install_thread, daemon=True).start()

    def is_playlist(self, url_or_query):
        """Detect if the URL/query is a playlist"""
        url_lower = url_or_query.lower()

        # Spotify playlists (handle international URLs like intl-de)
        if "spotify.com" in url_lower and "/playlist/" in url_lower:
            return True

        # YouTube playlists
        if "youtube.com/playlist" in url_lower or "list=" in url_lower:
            return True

        # Special Spotify queries that are playlists
        playlist_queries = [
            "all-user-playlists",
            "all-saved-playlists"
        ]
        if url_or_query.strip() in playlist_queries:
            return True

        return False

    def is_album(self, url_or_query):
        """Detect if the URL/query is an album"""
        url_lower = url_or_query.lower()

        # Spotify albums (handle international URLs like intl-de)
        if "spotify.com" in url_lower and "/album/" in url_lower:
            return True

        # Special Spotify query for saved albums
        if url_or_query.strip() == "all-user-saved-albums":
            return True

        return False

    def get_content_type(self, url_or_query):
        """Determine the content type (playlist, album, track, etc.)"""
        url_lower = url_or_query.lower()

        if self.is_playlist(url_or_query):
            return "playlist"
        elif self.is_album(url_or_query):
            return "album"
        elif "spotify.com" in url_lower and "/track/" in url_lower:
            return "track"
        elif "spotify.com" in url_lower and "/artist/" in url_lower:
            return "artist"
        elif "all-user-followed-artists" in url_or_query:
            return "artists"
        elif url_or_query.strip() == "saved":
            return "liked_songs"
        elif "youtube.com/watch" in url_or_query.lower() or "youtu.be" in url_or_query.lower():
            return "video"
        else:
            return "unknown"

    def generate_example_output(self, template):
        """Generate example output from template using consistent example data"""
        # Consistent example data (always the same)
        example_data = {
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "artists": "The Weeknd",
            "album": "After Hours",
            "album-artist": "The Weeknd",
            "genre": "Synth-pop",
            "year": "2020",
            "track-number": "03",
            "disc-number": "1",
            "isrc": "USUG11902768",
            "publisher": "Republic Records",
            "output-ext": "mp3"
        }

        try:
            # Replace all variables with example data
            result = template
            for key, value in example_data.items():
                result = result.replace(f"{{{key}}}", value)
            return result
        except:
            return template

    def update_template_example(self):
        """Update the example output when template changes"""
        template = self.template_entry.text()
        example = self.generate_example_output(template)
        self.example_output_label.setText(f"Preview: {example}")

    def generate_playlist_example_output(self, template):
        """Generate example output for playlist template using consistent example data"""
        # Consistent playlist example data
        example_data = {
            "list-name": "My Awesome Playlist",
            "list-position": "05",
            "list-length": "50",
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "artists": "The Weeknd",
            "album": "After Hours",
            "album-artist": "The Weeknd",
            "genre": "Synth-pop",
            "year": "2020",
            "track-number": "03",
            "disc-number": "1",
            "output-ext": "mp3"
        }

        try:
            # Replace all variables with example data
            result = template
            for key, value in example_data.items():
                result = result.replace(f"{{{key}}}", value)
            return result
        except:
            return template

    def update_playlist_template_example(self):
        """Update the playlist template example output when template changes"""
        template = self.playlist_template_entry.text()
        example = self.generate_playlist_example_output(template)
        self.playlist_example_output_label.setText(f"Preview: {example}")

    def insert_tag_template(self, tag):
        """Insert tag at cursor position in template entry"""
        cursor_pos = self.template_entry.cursorPosition()
        current_text = self.template_entry.text()
        new_text = current_text[:cursor_pos] + tag + current_text[cursor_pos:]
        self.template_entry.setText(new_text)
        self.template_entry.setCursorPosition(cursor_pos + len(tag))
        self.update_template_example()

    def insert_tag_playlist_template(self, tag):
        """Insert tag at cursor position in playlist template entry"""
        cursor_pos = self.playlist_template_entry.cursorPosition()
        current_text = self.playlist_template_entry.text()
        new_text = current_text[:cursor_pos] + tag + current_text[cursor_pos:]
        self.playlist_template_entry.setText(new_text)
        self.playlist_template_entry.setCursorPosition(cursor_pos + len(tag))
        self.update_playlist_template_example()

    def create_download_tab(self):
        """Create the download tab"""
        download_widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(download_widget)
        self.tab_widget.addTab(scroll, "Download")

        layout = QVBoxLayout(download_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Download Music")
        title.setProperty("class", "title")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # URL Input
        url_label = QLabel("Spotify/YouTube URL or Query:")
        layout.addWidget(url_label)

        # URL input frame with paste button
        url_layout = QHBoxLayout()
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("https://open.spotify.com/track/...")
        self.url_entry.setMinimumHeight(40)
        self.url_entry.textChanged.connect(self.update_command_preview)
        url_layout.addWidget(self.url_entry)

        paste_btn = QPushButton("📋")
        paste_btn.setFixedSize(40, 40)
        paste_btn.setStyleSheet("""
            QPushButton {
                font-size: 16pt;
                padding: 0px;
            }
        """)
        paste_btn.setToolTip("Paste from clipboard")
        paste_btn.clicked.connect(self.paste_url)
        url_layout.addWidget(paste_btn)

        layout.addLayout(url_layout)

        # Quick buttons
        quick_frame = QFrame()
        quick_layout = QHBoxLayout(quick_frame)

        quick_label = QLabel("Quick select:")
        quick_layout.addWidget(quick_label)

        quick_options = [
            ("Liked Songs", "saved"),
            ("All Playlists", "all-user-playlists"),
            ("Followed Artists", "all-user-followed-artists"),
        ]

        for label_text, value in quick_options:
            btn = QPushButton(label_text)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, v=value: self.url_entry.setText(v))
            quick_layout.addWidget(btn)

        quick_layout.addStretch()
        layout.addWidget(quick_frame)

        # Options frame
        options_frame = QFrame()
        options_layout = QGridLayout(options_frame)

        # Format
        format_label = QLabel("Format:")
        options_layout.addWidget(format_label, 0, 0)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "flac", "ogg", "opus", "m4a", "wav"])
        self.format_combo.setCurrentText(self.settings.get("format", "mp3"))
        self.format_combo.currentTextChanged.connect(self.update_command_preview)
        options_layout.addWidget(self.format_combo, 1, 0)

        # Bitrate
        bitrate_label = QLabel("Bitrate:")
        options_layout.addWidget(bitrate_label, 0, 1)

        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["auto", "320k", "256k", "192k", "128k", "96k"])
        self.bitrate_combo.setCurrentText(self.settings.get("bitrate", "320k"))
        self.bitrate_combo.currentTextChanged.connect(self.update_command_preview)
        options_layout.addWidget(self.bitrate_combo, 1, 1)

        layout.addWidget(options_frame)

        # Advanced options
        advanced_frame = QFrame()
        advanced_layout = QVBoxLayout(advanced_frame)

        adv_label = QLabel("Advanced Options:")
        adv_label_font = QFont()
        adv_label_font.setBold(True)
        adv_label.setFont(adv_label_font)
        advanced_layout.addWidget(adv_label)

        # Checkboxes in grid
        check_grid = QGridLayout()

        self.preload_check = QCheckBox("Preload URLs")
        self.preload_check.setToolTip("Preload download URLs before starting. Helps catch errors early.")
        self.preload_check.stateChanged.connect(self.update_command_preview)
        check_grid.addWidget(self.preload_check, 0, 0)

        self.sponsor_block_check = QCheckBox("Skip Sponsors")
        self.sponsor_block_check.setToolTip("Use SponsorBlock to skip sponsor segments in videos (YouTube only)")
        self.sponsor_block_check.stateChanged.connect(self.update_command_preview)
        check_grid.addWidget(self.sponsor_block_check, 0, 1)

        self.skip_explicit_check = QCheckBox("Skip Explicit")
        self.skip_explicit_check.setToolTip("Skip songs marked as explicit content")
        self.skip_explicit_check.stateChanged.connect(self.update_command_preview)
        check_grid.addWidget(self.skip_explicit_check, 0, 2)

        self.generate_lrc_check = QCheckBox("Generate LRC")
        self.generate_lrc_check.setToolTip("Generate .lrc lyric files alongside audio files")
        self.generate_lrc_check.stateChanged.connect(self.update_command_preview)
        check_grid.addWidget(self.generate_lrc_check, 1, 0)

        self.playlist_numbering_check = QCheckBox("Playlist Numbering")
        self.playlist_numbering_check.setToolTip("Set track numbers in metadata to playlist position (affects ID3 tags, not filenames)")
        self.playlist_numbering_check.stateChanged.connect(self.update_command_preview)
        check_grid.addWidget(self.playlist_numbering_check, 1, 1)

        self.folder_per_url_check = QCheckBox("Create Folder per URL")
        self.folder_per_url_check.setToolTip("Create a separate folder for each URL/query (useful for batch downloads)")
        self.folder_per_url_check.setChecked(self.settings.get("create_folder_per_url", True))
        self.folder_per_url_check.stateChanged.connect(self.update_command_preview)
        check_grid.addWidget(self.folder_per_url_check, 1, 2)

        advanced_layout.addLayout(check_grid)
        layout.addWidget(advanced_frame)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.download_btn = QPushButton("⬇️ Download")
        self.download_btn.setMinimumHeight(50)
        download_font = QFont()
        download_font.setPointSize(14)
        download_font.setBold(True)
        self.download_btn.setFont(download_font)
        self.download_btn.clicked.connect(self.start_download)
        buttons_layout.addWidget(self.download_btn, 3)

        self.open_folder_btn = QPushButton("📁 Open Folder")
        self.open_folder_btn.setMinimumHeight(50)
        self.open_folder_btn.setFont(download_font)
        self.open_folder_btn.setSizePolicy(self.open_folder_btn.sizePolicy().horizontalPolicy(),
                                           self.open_folder_btn.sizePolicy().verticalPolicy())
        self.open_folder_btn.setProperty("class", "secondary")
        self.open_folder_btn.setStyleSheet("background-color: #424242;")
        self.open_folder_btn.clicked.connect(self.open_download_folder)
        buttons_layout.addWidget(self.open_folder_btn, 1)

        layout.addLayout(buttons_layout)

        # Command preview
        command_preview_label = QLabel("Command Preview:")
        command_font = QFont()
        command_font.setPointSize(10)
        command_font.setBold(True)
        command_preview_label.setFont(command_font)
        layout.addWidget(command_preview_label)

        command_layout = QHBoxLayout()

        self.command_entry = QLineEdit()
        self.command_entry.setPlaceholderText("Command will appear here...")
        self.command_entry.setReadOnly(True)
        command_entry_font = QFont("Consolas", 9)
        self.command_entry.setFont(command_entry_font)
        self.command_entry.setMinimumHeight(35)
        command_layout.addWidget(self.command_entry)

        copy_btn = QPushButton("📄")
        copy_btn.setFixedSize(40, 40)
        copy_btn.setStyleSheet("""
            QPushButton {
                font-size: 16pt;
                padding: 0px;
            }
        """)
        copy_btn.setToolTip("Copy command to clipboard")
        copy_btn.clicked.connect(self.copy_command)
        command_layout.addWidget(copy_btn)

        layout.addLayout(command_layout)

        layout.addStretch()

    def create_queue_tab(self):
        """Create the queue tab"""
        queue_widget = QWidget()
        layout = QVBoxLayout(queue_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Download Queue & Output")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        clear_btn = QPushButton("Clear Queue")
        clear_btn.setFixedWidth(120)
        clear_btn.clicked.connect(self.clear_queue)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Queue textbox
        self.queue_textbox = QTextEdit()
        self.queue_textbox.setReadOnly(True)
        queue_font = QFont("Consolas", 10)
        self.queue_textbox.setFont(queue_font)
        layout.addWidget(self.queue_textbox)

        # Setup thread-safe logger
        self.logger = ThreadSafeLogger(self.queue_textbox)

        self.tab_widget.addTab(queue_widget, "Queue")

    def create_settings_tab(self):
        """Create the settings tab"""
        settings_widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(settings_widget)
        self.tab_widget.addTab(scroll, "Settings")

        layout = QVBoxLayout(settings_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Download folder
        folder_frame = QFrame()
        folder_layout = QVBoxLayout(folder_frame)

        folder_label = QLabel("Base Download Folder:")
        folder_label_font = QFont()
        folder_label_font.setBold(True)
        folder_label.setFont(folder_label_font)
        folder_layout.addWidget(folder_label)

        folder_input_layout = QHBoxLayout()

        folder_label2 = QLabel("Folder:")
        folder_input_layout.addWidget(folder_label2)

        self.folder_entry = QLineEdit()
        self.folder_entry.setText(self.settings.get("download_folder", str(Path.home() / "Music")))
        folder_input_layout.addWidget(self.folder_entry)

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self.browse_folder)
        folder_input_layout.addWidget(browse_btn)

        open_folder_btn = QPushButton("📁 Open Folder")
        open_folder_btn.setMinimumWidth(130)
        open_folder_btn.setStyleSheet("background-color: #424242; padding: 8px 12px;")
        open_folder_btn.clicked.connect(self.open_download_folder)
        folder_input_layout.addWidget(open_folder_btn)

        folder_layout.addLayout(folder_input_layout)
        layout.addWidget(folder_frame)

        # Output template (Song File Template)
        template_frame = QFrame()
        template_layout = QVBoxLayout(template_frame)

        template_label = QLabel("Song File Template (folders + filename):")
        template_label_font = QFont()
        template_label_font.setBold(True)
        template_label.setFont(template_label_font)
        template_layout.addWidget(template_label)

        template_help = QLabel("Controls the folder structure AND song filenames. Use / to create folders.")
        template_help.setStyleSheet("color: #999999; font-size: 9pt;")
        template_layout.addWidget(template_help)

        self.template_entry = QLineEdit()
        self.template_entry.setText(self.settings.get("output", "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}"))
        self.template_entry.textChanged.connect(self.update_template_example)
        self.template_entry.textChanged.connect(self.update_command_preview)
        template_layout.addWidget(self.template_entry)

        # Example output
        initial_example = self.generate_example_output(self.template_entry.text())
        self.example_output_label = QLabel(f"Preview: {initial_example}")
        self.example_output_label.setStyleSheet("color: #4CAF50; font-size: 9pt;")
        template_layout.addWidget(self.example_output_label)

        # Clickable tags
        template_tags_label = QLabel("Click to insert:")
        template_tags_label.setStyleSheet("color: #999999; font-size: 9pt;")
        template_layout.addWidget(template_tags_label)

        template_tags_widget = QWidget()
        template_tags_layout = QGridLayout(template_tags_widget)
        template_tags_layout.setSpacing(4)

        song_tags = sorted([
            "{album}", "{album-artist}", "{artist}", "{artists}",
            "{disc-number}", "{genre}", "{isrc}", "{output-ext}",
            "{publisher}", "{title}", "{track-number}", "{year}"
        ])

        for i, tag in enumerate(song_tags):
            tag_btn = QPushButton(tag)
            tag_btn.setFixedHeight(24)
            tag_btn.setStyleSheet("background-color: #2b2b2b; font-size: 9pt;")
            tag_btn.clicked.connect(lambda checked, t=tag: self.insert_tag_template(t))
            template_tags_layout.addWidget(tag_btn, i // 6, i % 6)

        template_layout.addWidget(template_tags_widget)
        layout.addWidget(template_frame)

        # Playlist template
        playlist_template_frame = QFrame()
        playlist_template_layout = QVBoxLayout(playlist_template_frame)

        playlist_template_label = QLabel("Playlist Template (for playlists only):")
        playlist_template_label_font = QFont()
        playlist_template_label_font.setBold(True)
        playlist_template_label.setFont(playlist_template_label_font)
        playlist_template_layout.addWidget(playlist_template_label)

        playlist_template_help = QLabel("Used automatically when downloading playlists. Use {list-name}, {list-position} for playlist-specific variables.")
        playlist_template_help.setStyleSheet("color: #999999; font-size: 9pt;")
        playlist_template_layout.addWidget(playlist_template_help)

        self.playlist_template_entry = QLineEdit()
        self.playlist_template_entry.setText(self.settings.get("playlist_output", "{list-name}/{list-position} - {artists} - {title}.{output-ext}"))
        self.playlist_template_entry.textChanged.connect(self.update_playlist_template_example)
        self.playlist_template_entry.textChanged.connect(self.update_command_preview)
        playlist_template_layout.addWidget(self.playlist_template_entry)

        # Example output
        initial_playlist_example = self.generate_playlist_example_output(self.playlist_template_entry.text())
        self.playlist_example_output_label = QLabel(f"Preview: {initial_playlist_example}")
        self.playlist_example_output_label.setStyleSheet("color: #4CAF50; font-size: 9pt;")
        playlist_template_layout.addWidget(self.playlist_example_output_label)

        # Clickable tags
        playlist_tags_label = QLabel("Click to insert:")
        playlist_tags_label.setStyleSheet("color: #999999; font-size: 9pt;")
        playlist_template_layout.addWidget(playlist_tags_label)

        playlist_tags_widget = QWidget()
        playlist_tags_layout = QGridLayout(playlist_tags_widget)
        playlist_tags_layout.setSpacing(4)

        playlist_tags = sorted([
            "{album}", "{artist}", "{artists}", "{genre}",
            "{list-length}", "{list-name}", "{list-position}",
            "{output-ext}", "{title}", "{year}"
        ])

        for i, tag in enumerate(playlist_tags):
            tag_btn = QPushButton(tag)
            tag_btn.setFixedHeight(24)
            tag_btn.setStyleSheet("background-color: #2b2b2b; font-size: 9pt;")
            tag_btn.clicked.connect(lambda checked, t=tag: self.insert_tag_playlist_template(t))
            playlist_tags_layout.addWidget(tag_btn, i // 6, i % 6)

        playlist_template_layout.addWidget(playlist_tags_widget)
        layout.addWidget(playlist_template_frame)

        # Threads
        threads_frame = QFrame()
        threads_layout = QHBoxLayout(threads_frame)

        threads_label = QLabel("Concurrent Downloads:")
        threads_layout.addWidget(threads_label)

        self.threads_slider = QSlider(Qt.Horizontal)
        self.threads_slider.setMinimum(1)
        self.threads_slider.setMaximum(16)
        self.threads_slider.setValue(int(self.settings.get("threads", "4")))
        self.threads_slider.valueChanged.connect(self.update_threads_label)
        self.threads_slider.valueChanged.connect(self.update_command_preview)
        threads_layout.addWidget(self.threads_slider)

        self.threads_value_label = QLabel(str(self.threads_slider.value()))
        threads_layout.addWidget(self.threads_value_label)

        layout.addWidget(threads_frame)

        # Save settings button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setMinimumHeight(40)
        save_font = QFont()
        save_font.setPointSize(12)
        save_font.setBold(True)
        save_btn.setFont(save_font)
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        # Config file location
        config_label = QLabel(f"Config saved to: {self.config_file}")
        config_label.setStyleSheet("color: #999999; font-size: 9pt;")
        layout.addWidget(config_label)

        # SpotDL installation check
        spotdl_frame = QFrame()
        spotdl_layout = QVBoxLayout(spotdl_frame)

        spotdl_label = QLabel("SpotDL Installation:")
        spotdl_label_font = QFont()
        spotdl_label_font.setBold(True)
        spotdl_label.setFont(spotdl_label_font)
        spotdl_layout.addWidget(spotdl_label)

        # Status label
        self.spotdl_status_label = QLabel("Checking...")
        self.spotdl_status_label.setStyleSheet("color: #999999; font-size: 10pt;")
        spotdl_layout.addWidget(self.spotdl_status_label)

        # Buttons
        spotdl_buttons_layout = QHBoxLayout()

        check_spotdl_btn = QPushButton("Check Installation")
        check_spotdl_btn.setFixedWidth(150)
        check_spotdl_btn.clicked.connect(self.check_spotdl_installation)
        spotdl_buttons_layout.addWidget(check_spotdl_btn)

        install_spotdl_btn = QPushButton("Install SpotDL")
        install_spotdl_btn.setFixedWidth(150)
        install_spotdl_btn.setStyleSheet("background-color: #4CAF50;")
        install_spotdl_btn.clicked.connect(self.install_spotdl)
        spotdl_buttons_layout.addWidget(install_spotdl_btn)

        spotdl_buttons_layout.addStretch()

        spotdl_layout.addLayout(spotdl_buttons_layout)
        layout.addWidget(spotdl_frame)

        # Initial check
        self.check_spotdl_installation()

        layout.addStretch()

    def update_threads_label(self, value):
        """Update threads value label"""
        self.threads_value_label.setText(str(value))

    def browse_folder(self):
        """Browse for download folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.folder_entry.setText(folder)

    def open_download_folder(self):
        """Open the download folder in system file explorer"""
        folder = self.folder_entry.text()

        if not os.path.exists(folder):
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"The folder doesn't exist yet:\n{folder}\n\nIt will be created when you download something."
            )
            return

        try:
            # Windows
            if sys.platform == "win32":
                os.startfile(folder)
            # macOS
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            # Linux
            else:
                subprocess.run(["xdg-open", folder])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open folder:\n{str(e)}")

    def paste_url(self):
        """Paste from clipboard into URL entry"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.url_entry.setText(text)
            self.update_command_preview()

    def copy_command(self):
        """Copy command preview to clipboard"""
        command = self.command_entry.text()
        if command and command != "Command will appear here...":
            try:
                clipboard = QApplication.clipboard()
                clipboard.setText(command)

                # Visual feedback
                original_text = command
                self.command_entry.setText(command + " ✓")

                # Reset after 1 second
                QTimer.singleShot(1000, lambda: self.command_entry.setText(original_text))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to copy to clipboard:\n{str(e)}")

    def update_command_preview(self):
        """Update the command preview field with current settings"""
        query = self.url_entry.text().strip()

        if not query:
            self.command_entry.setText("")
            self.command_entry.setPlaceholderText("Command will appear here...")
            return

        # Build command exactly as it will be executed
        cmd_parts = ["spotdl", query]

        # Add options
        cmd_parts.extend(["--format", self.format_combo.currentText()])
        cmd_parts.extend(["--bitrate", self.bitrate_combo.currentText()])
        cmd_parts.extend(["--threads", str(self.threads_slider.value())])

        # Automatically select the correct template based on URL type
        is_playlist_url = self.is_playlist(query)
        if is_playlist_url:
            template = self.playlist_template_entry.text()
        else:
            template = self.template_entry.text()

        cmd_parts.extend(["--output", template])

        # Add flags
        if self.preload_check.isChecked():
            cmd_parts.append("--preload")
        if self.sponsor_block_check.isChecked():
            cmd_parts.append("--sponsor-block")
        if self.skip_explicit_check.isChecked():
            cmd_parts.append("--skip-explicit")
        if self.generate_lrc_check.isChecked():
            cmd_parts.append("--generate-lrc")
        if self.playlist_numbering_check.isChecked():
            cmd_parts.append("--playlist-numbering")

        # Build command string
        command = " ".join(cmd_parts)

        # Update entry
        self.command_entry.setText(command)

    def log_to_queue(self, message):
        """Thread-safe logging to queue"""
        self.logger.log(message)

    def start_download(self):
        """Start a download"""
        query = self.url_entry.text().strip()

        if not query:
            QMessageBox.warning(self, "No URL", "Please enter a Spotify or YouTube URL")
            return

        # Get settings (before switching to queue tab)
        format_val = self.format_combo.currentText()
        bitrate_val = self.bitrate_combo.currentText()
        threads_val = str(self.threads_slider.value())
        download_folder = self.folder_entry.text()
        folder_per_url = self.folder_per_url_check.isChecked()

        # Get flags
        preload = self.preload_check.isChecked()
        sponsor_block = self.sponsor_block_check.isChecked()
        skip_explicit = self.skip_explicit_check.isChecked()
        generate_lrc = self.generate_lrc_check.isChecked()
        playlist_numbering = self.playlist_numbering_check.isChecked()

        # Check content type quickly (doesn't require network)
        is_playlist_url = self.is_playlist(query)
        is_album_url = self.is_album(query)
        content_type = self.get_content_type(query)

        # Automatically select the correct template based on URL type
        if is_playlist_url:
            template_val = self.playlist_template_entry.text()
            self.log_to_queue(f"🎼 Using playlist template\n")
        else:
            template_val = self.template_entry.text()
            if is_album_url:
                self.log_to_queue(f"💿 Using album/track template\n")

        # Log initial message
        timestamp = datetime.now().strftime("%H:%M:%S")
        type_icons = {
            "playlist": "📃",
            "album": "💿",
            "track": "🎵",
            "artist": "🎤",
            "artists": "🎤",
            "liked_songs": "❤️",
            "video": "📹",
            "unknown": "📥"
        }
        icon = type_icons.get(content_type, "📥")

        self.log_to_queue(f"\n{'='*60}\n")
        self.log_to_queue(f"[{timestamp}] {icon} Starting download ({content_type})\n")
        self.log_to_queue(f"Query: {query}\n")

        # Clear URL input
        self.url_entry.clear()

        # Switch to queue tab immediately (no UI freeze!)
        self.tab_widget.setCurrentIndex(1)

        # Start download preparation and execution in background thread
        threading.Thread(
            target=self.prepare_and_download,
            args=(query, format_val, bitrate_val, threads_val, template_val,
                  download_folder, folder_per_url,
                  is_playlist_url, is_album_url,
                  preload, sponsor_block, skip_explicit, generate_lrc, playlist_numbering),
            daemon=True
        ).start()

    def prepare_and_download(self, query, format_val, bitrate_val, threads_val,
                            template_val, download_folder, folder_per_url,
                            is_playlist_url, is_album_url,
                            preload, sponsor_block, skip_explicit, generate_lrc,
                            playlist_numbering):
        """Prepare download folder (fetch metadata if needed) and start download - runs in background thread"""

        # Handle folder per URL organization
        if folder_per_url:
            # For albums and playlists, try to get real names
            if is_playlist_url or is_album_url:
                content_type_name = "album" if is_album_url else "playlist"

                # Fetch metadata from Spotify (this is the slow part, now in background thread)
                self.log_to_queue(f"🔍 Fetching {content_type_name} metadata from Spotify...\n")
                metadata = self.get_spotify_metadata(query)

                if metadata:
                    self.log_to_queue(f"✅ Found {content_type_name}: {metadata.get('name', 'Unknown')}\n")
                    # Use the auto-detected name
                    folder_name = self.sanitize_folder_name(metadata['name'])
                else:
                    # Metadata fetch failed, fallback to URL-based naming
                    self.log_to_queue(f"⚠️ Could not fetch metadata, using URL-based name\n")
                    folder_name = self.sanitize_folder_name(query)
            else:
                # For other types (tracks, etc.), create folder from URL
                folder_name = self.sanitize_folder_name(query)

            # Create folder directly in output folder (no "Playlists" parent)
            download_folder = os.path.join(download_folder, folder_name)

        # Log folder path
        self.log_to_queue(f"Folder: {download_folder}\n")

        # Build command
        cmd = ["spotdl", query]
        cmd.extend(["--format", format_val])
        cmd.extend(["--bitrate", bitrate_val])
        cmd.extend(["--threads", threads_val])
        cmd.extend(["--output", template_val])

        # Add flags
        if preload:
            cmd.append("--preload")
        if sponsor_block:
            cmd.append("--sponsor-block")
        if skip_explicit:
            cmd.append("--skip-explicit")
        if generate_lrc:
            cmd.append("--generate-lrc")
        if playlist_numbering:
            cmd.append("--playlist-numbering")

        self.log_to_queue(f"Command: {' '.join(cmd)}\n")
        self.log_to_queue(f"{'='*60}\n\n")

        # Now run the actual download
        self.run_download(cmd, download_folder, query)

    def get_spotify_metadata(self, url_or_query):
        """Get comprehensive metadata from Spotify using enhanced metadata handler

        Returns:
            dict or None: Metadata dictionary with rich fields including:
                         'name', 'type', 'artist', 'artists', 'album', 'album-artist',
                         'year', 'date', 'genre', 'genres', 'url', 'cover_url',
                         'duration', 'explicit', 'popularity', 'track_count', etc.
                         or None if fetching fails
        """
        try:
            # Use the enhanced metadata handler (lazy loaded)
            metadata = get_metadata_handler().get_metadata(url_or_query)

            if metadata:
                # Ensure 'album-artist' key exists (with dash) for template compatibility
                if 'album_artist' in metadata and 'album-artist' not in metadata:
                    metadata['album-artist'] = metadata['album_artist']

                # Ensure year is a string for template formatting
                if 'year' in metadata:
                    metadata['year'] = str(metadata['year'])

            return metadata

        except Exception as e:
            # If metadata fetch fails, return None to fallback to URL-based naming
            return None

    def apply_folder_template(self, template, metadata):
        """Apply metadata to folder name template using enhanced formatter

        Args:
            template: Template string like "{artist} - {album} ({year})"
                     Supports: {name}, {artist}, {artists}, {album}, {album-artist},
                              {year}, {date}, {genre}, {type}
            metadata: Dictionary with metadata fields

        Returns:
            str: Folder name with variables replaced, or None if template/metadata invalid
        """
        if not template or not metadata:
            return None

        # Use the metadata handler's format_template method (lazy loaded)
        return get_metadata_handler().format_template(template, metadata)

    def sanitize_folder_name(self, url_or_query):
        """Create a safe folder name from URL or query using enhanced sanitizer"""
        # Handle special Spotify queries
        special_queries = {
            "saved": "Liked Songs",
            "all-user-playlists": "All My Playlists",
            "all-saved-playlists": "My Saved Playlists",
            "all-user-followed-artists": "Followed Artists",
            "all-user-saved-albums": "Saved Albums"
        }

        if url_or_query in special_queries:
            return special_queries[url_or_query]

        # Extract meaningful part from URL
        if "spotify.com" in url_or_query and "/playlist/" in url_or_query:
            # For Spotify playlists, use the playlist ID
            parts = url_or_query.split("/")
            if len(parts) >= 2:
                playlist_id = parts[-1].split("?")[0][:12]  # Get ID, remove query params
                return f"Spotify_Playlist_{playlist_id}"

        elif "spotify.com" in url_or_query:
            # For other Spotify URLs
            parts = url_or_query.split("/")
            if len(parts) >= 2:
                # Get the type and ID
                content_type = parts[-2] if "/" in url_or_query else "item"
                content_id = parts[-1].split("?")[0][:12]
                return f"Spotify_{content_type}_{content_id}"

        elif "youtube.com/playlist" in url_or_query:
            # YouTube playlist
            list_id = url_or_query.split("list=")[-1].split("&")[0][:12]
            return f"YouTube_Playlist_{list_id}"

        elif "youtube.com" in url_or_query or "youtu.be" in url_or_query:
            # YouTube video
            return f"YouTube_{url_or_query.split('=')[-1][:8]}"

        # For other queries, use the enhanced sanitizer (lazy loaded)
        return get_metadata_handler().sanitize_folder_name(url_or_query, max_length=100)

    def run_download(self, cmd, download_folder, query):
        """Run spotdl command in background with real-time output"""
        try:
            os.makedirs(download_folder, exist_ok=True)

            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True,
                bufsize=1,  # Line buffered
                cwd=download_folder
            )

            # Read output line by line in real-time
            for line in process.stdout:
                self.log_to_queue(line)

            # Wait for completion
            process.wait()

            # Log completion
            timestamp = datetime.now().strftime("%H:%M:%S")
            if process.returncode == 0:
                self.log_to_queue(f"\n[{timestamp}] ✅ Download completed successfully!\n")
                self.log_to_queue(f"📁 Files saved to: {download_folder}\n")
            else:
                self.log_to_queue(f"\n[{timestamp}] ❌ Download failed with exit code {process.returncode}\n")

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_to_queue(f"\n[{timestamp}] ❌ Error: {str(e)}\n")

    def clear_queue(self):
        """Clear the queue display"""
        self.queue_textbox.clear()


def main():
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("SpotDL GUI")
    app.setOrganizationName("SpotDL")

    # Create and show main window
    window = SpotDLGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
