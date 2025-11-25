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
    QTabWidget, QScrollArea, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QUrl
from PySide6.QtGui import QFont, QTextCursor, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# Import queue management
from queue_item import QueueItem
from queue_manager import DownloadQueueManager

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
    # Qt Signals for thread-safe GUI updates
    create_card_signal = Signal(str, dict)      # queue_id, metadata
    update_metadata_signal = Signal(str, dict)  # queue_id, metadata
    update_progress_signal = Signal(str, int)   # queue_id, progress
    update_current_song_signal = Signal(str, str)  # queue_id, current_song_name

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

        # Queue items tracking (for GUI cards)
        self.queue_items = {}  # Track queue items with metadata

        # Clipboard monitoring - initialize BEFORE creating tabs
        self.clipboard = QApplication.clipboard()
        self.last_clipboard_text = ""
        self.clipboard_monitoring_enabled = False
        self.clipboard_connected = False  # Track connection state

        # Network manager for downloading images
        self.network_manager = QNetworkAccessManager()

        # Initialize tabs (now that all attributes are set up)
        self.create_download_tab()
        self.create_queue_tab()
        self.create_settings_tab()

        # NOW it's safe to enable clipboard monitoring (logger exists)
        self.clipboard_monitor_check.setChecked(True)

        # Initialize queue manager AFTER tabs (needs GUI methods)
        self.queue_manager = DownloadQueueManager(self)
        print("[GUI] DownloadQueueManager initialized")

        # Track auto-clear timers for completed items
        self.auto_clear_timers = {}  # {queue_id: QTimer}

        # Connect thread-safe GUI update signals
        self.create_card_signal.connect(self.create_queue_card)
        self.update_metadata_signal.connect(self.update_queue_card_metadata)
        self.update_progress_signal.connect(self.update_queue_progress)
        self.update_current_song_signal.connect(self.update_current_song)
        print("[GUI] Connected thread-safe update signals")

        # Initialize command preview
        self.update_command_preview()

        # Setup queue status update timer (every 2 seconds)
        self.queue_status_timer = QTimer()
        self.queue_status_timer.timeout.connect(self.update_queue_status)
        self.queue_status_timer.start(2000)  # Update every 2 seconds

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
            self.settings["auto_clear_completed"] = self.auto_clear_queue_check.isChecked()

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

        # URL Input with clipboard monitoring option
        url_header_layout = QHBoxLayout()
        url_label = QLabel("Spotify/YouTube URL or Query:")
        url_header_layout.addWidget(url_label)

        url_header_layout.addStretch()

        self.clipboard_monitor_check = QCheckBox("Auto-detect clipboard links")
        self.clipboard_monitor_check.setToolTip("Automatically detect and paste Spotify/YouTube links when copied")
        self.clipboard_monitor_check.stateChanged.connect(self.toggle_clipboard_monitoring)
        # Don't check yet - will be set after logger is initialized
        url_header_layout.addWidget(self.clipboard_monitor_check)

        # Test button - copy test URL to clipboard
        test_clipboard_btn = QPushButton("🧪 Test Clipboard")
        test_clipboard_btn.setToolTip("Copy a test Spotify URL to clipboard to test auto-detection")
        test_clipboard_btn.clicked.connect(self.test_clipboard_copy)
        url_header_layout.addWidget(test_clipboard_btn)

        layout.addLayout(url_header_layout)

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

        self.auto_clear_queue_check = QCheckBox("Auto-Clear Completed")
        self.auto_clear_queue_check.setToolTip("Automatically remove completed downloads from queue after 5 seconds")
        self.auto_clear_queue_check.setChecked(self.settings.get("auto_clear_completed", False))
        self.auto_clear_queue_check.stateChanged.connect(self.save_settings)
        check_grid.addWidget(self.auto_clear_queue_check, 2, 0)

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
        """Create the queue tab with preview cards"""
        queue_widget = QWidget()
        layout = QVBoxLayout(queue_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header with queue controls
        header_layout = QHBoxLayout()

        title = QLabel("Download Queue")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        # Queue status label
        self.queue_status_label = QLabel("Ready")
        self.queue_status_label.setStyleSheet("color: #888888; font-size: 12pt;")
        header_layout.addWidget(self.queue_status_label)

        header_layout.addStretch()

        # Pause/Resume button
        self.pause_resume_btn = QPushButton("⏸ Pause")
        self.pause_resume_btn.setFixedWidth(100)
        self.pause_resume_btn.clicked.connect(self.toggle_queue_pause)
        self.pause_resume_btn.setEnabled(False)  # Disabled until queue has items
        header_layout.addWidget(self.pause_resume_btn)

        # Clear completed button
        self.clear_completed_btn = QPushButton("🧹 Clear Completed")
        self.clear_completed_btn.setFixedWidth(150)
        self.clear_completed_btn.clicked.connect(self.clear_completed_items)
        header_layout.addWidget(self.clear_completed_btn)

        # Clear log button
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.setFixedWidth(100)
        clear_log_btn.clicked.connect(self.clear_queue_log)
        header_layout.addWidget(clear_log_btn)

        layout.addLayout(header_layout)

        # Queue statistics bar
        stats_layout = QHBoxLayout()
        self.queue_stats_label = QLabel("No downloads in queue")
        self.queue_stats_label.setStyleSheet("color: #aaaaaa; padding: 5px;")
        stats_layout.addWidget(self.queue_stats_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Queue preview section - scrollable area for download cards
        queue_preview_label = QLabel("Active Downloads:")
        queue_preview_label_font = QFont()
        queue_preview_label_font.setBold(True)
        queue_preview_label.setFont(queue_preview_label_font)
        layout.addWidget(queue_preview_label)

        self.queue_preview_scroll = QScrollArea()
        self.queue_preview_scroll.setWidgetResizable(True)
        self.queue_preview_scroll.setFixedHeight(300)  # Increased for larger cards
        self.queue_preview_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
            }
        """)

        self.queue_preview_widget = QWidget()
        self.queue_preview_layout = QVBoxLayout(self.queue_preview_widget)
        self.queue_preview_layout.setSpacing(10)
        self.queue_preview_layout.setContentsMargins(10, 10, 10, 10)
        self.queue_preview_layout.addStretch()

        self.queue_preview_scroll.setWidget(self.queue_preview_widget)
        layout.addWidget(self.queue_preview_scroll)

        # Output log section
        output_label = QLabel("Output Log:")
        output_label_font = QFont()
        output_label_font.setBold(True)
        output_label.setFont(output_label_font)
        layout.addWidget(output_label)

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

    def test_clipboard_copy(self):
        """Test method - copies a test Spotify URL to clipboard with detailed logging"""
        test_url = "https://open.spotify.com/album/3fsnW79AlDwj2mF8HhnByU?si=9tLoGPfvRt-yNX_2fmrqCw"

        print("\n" + "="*60)
        print("[TEST] Testing Clipboard Auto-Detection")
        print("="*60)
        print(f"[TEST] Copying test URL to clipboard: {test_url}")
        print(f"[TEST] Clipboard monitoring enabled: {self.clipboard_monitoring_enabled}")
        print(f"[TEST] Clipboard signal connected: {self.clipboard_connected}")
        print(f"[TEST] Last clipboard text: {self.last_clipboard_text[:50] if self.last_clipboard_text else 'None'}...")

        # Copy to clipboard
        self.clipboard.setText(test_url)

        print(f"[TEST] Clipboard.setText() called")
        print(f"[TEST] Reading back from clipboard: {self.clipboard.text()[:50]}...")
        print(f"[TEST] Waiting for dataChanged signal to fire...")
        print("="*60 + "\n")

        self.log_to_queue(f"🧪 Test: Copied test URL to clipboard\n")

    def toggle_clipboard_monitoring(self, state):
        """Enable/disable clipboard monitoring"""
        print(f"[DEBUG] toggle_clipboard_monitoring() called with state={state}")

        # Safety check - ensure attributes exist
        if not hasattr(self, 'clipboard_connected'):
            print(f"[DEBUG] clipboard_connected attribute doesn't exist yet, returning")
            return

        print(f"[DEBUG] Attributes exist, proceeding...")
        # state is an int, Qt.Checked is an enum - compare values
        self.clipboard_monitoring_enabled = (state == Qt.Checked.value or state == Qt.Checked)
        print(f"[DEBUG] Clipboard monitoring toggled: enabled={self.clipboard_monitoring_enabled}, state={state} (type: {type(state)}), Qt.Checked={Qt.Checked}, Qt.Checked.value={Qt.Checked.value}")

        if self.clipboard_monitoring_enabled:
            # Start monitoring
            if not self.clipboard_connected:
                self.last_clipboard_text = self.clipboard.text()
                self.clipboard.dataChanged.connect(self.check_clipboard)
                self.clipboard_connected = True
                print(f"[DEBUG] Clipboard signal connected")
                self.log_to_queue("🔍 Clipboard monitoring enabled - will auto-detect Spotify/YouTube links\n")
        else:
            # Stop monitoring
            if self.clipboard_connected:
                try:
                    self.clipboard.dataChanged.disconnect(self.check_clipboard)
                    self.clipboard_connected = False
                    print(f"[DEBUG] Clipboard signal disconnected")
                except:
                    pass
                self.log_to_queue("⏸️ Clipboard monitoring disabled\n")

    def check_clipboard(self):
        """Check clipboard for Spotify/YouTube URLs"""
        print(f"[DEBUG] check_clipboard() called!")
        print(f"[DEBUG]   - monitoring_enabled: {self.clipboard_monitoring_enabled}")

        if not self.clipboard_monitoring_enabled:
            print(f"[DEBUG]   - Monitoring disabled, returning")
            return

        try:
            text = self.clipboard.text().strip()
            print(f"[DEBUG]   - Clipboard text: '{text[:100]}'")
            print(f"[DEBUG]   - Last clipboard text: '{self.last_clipboard_text[:100] if self.last_clipboard_text else 'None'}'")

            # Ignore if empty or same as last check
            if not text:
                print(f"[DEBUG]   - Text is empty, returning")
                return

            if text == self.last_clipboard_text:
                print(f"[DEBUG]   - Text same as last check, returning")
                return

            self.last_clipboard_text = text
            print(f"[DEBUG]   - New clipboard text detected!")

            # Check if it's a Spotify or YouTube URL
            is_valid = self.is_valid_music_url(text)
            print(f"[DEBUG]   - is_valid_music_url returned: {is_valid}")

            if is_valid:
                print(f"[DEBUG]   - Valid music URL detected! Pasting to URL field...")
                self.url_entry.setText(text)
                self.log_to_queue(f"📋 Auto-detected link: {text[:60]}{'...' if len(text) > 60 else ''}\n")

                # Switch to Download tab
                self.tab_widget.setCurrentIndex(0)
                print(f"[DEBUG]   - Switched to Download tab")
            else:
                print(f"[DEBUG]   - Not a valid music URL, ignoring")
        except Exception as e:
            print(f"[DEBUG] Clipboard check error: {e}")
            import traceback
            traceback.print_exc()

    def is_valid_music_url(self, text):
        """Check if text is a valid Spotify or YouTube URL"""
        print(f"[DEBUG] is_valid_music_url() checking: '{text[:80]}'")

        if not text:
            print(f"[DEBUG]   - Text is empty, returning False")
            return False

        text_lower = text.lower()
        print(f"[DEBUG]   - Lowercase text: '{text_lower[:80]}'")

        # Spotify URLs
        has_spotify = 'spotify.com/' in text_lower
        spotify_keywords = ['track', 'album', 'playlist', 'artist']
        has_keyword = any(x in text_lower for x in spotify_keywords)
        print(f"[DEBUG]   - Has 'spotify.com/': {has_spotify}")
        print(f"[DEBUG]   - Has keyword {spotify_keywords}: {has_keyword}")

        if has_spotify and has_keyword:
            print(f"[DEBUG]   - Valid Spotify URL detected!")
            return True

        # YouTube URLs
        has_youtube_watch = 'youtube.com/watch' in text_lower
        has_youtu_be = 'youtu.be/' in text_lower
        has_youtube_playlist = 'youtube.com/playlist' in text_lower
        print(f"[DEBUG]   - Has 'youtube.com/watch': {has_youtube_watch}")
        print(f"[DEBUG]   - Has 'youtu.be/': {has_youtu_be}")
        print(f"[DEBUG]   - Has 'youtube.com/playlist': {has_youtube_playlist}")

        if has_youtube_watch or has_youtu_be or has_youtube_playlist:
            print(f"[DEBUG]   - Valid YouTube URL detected!")
            return True

        print(f"[DEBUG]   - Not a valid music URL")
        return False

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

    def create_queue_card(self, queue_id, metadata):
        """Create a preview card for a download with image, info, and progress bar"""
        card = QFrame()
        card.setObjectName(f"card_{queue_id}")
        card.setStyleSheet("""
            QFrame {
                background-color: #242424;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        card.setFixedHeight(200)  # Increased for better spacing

        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(10, 10, 10, 10)

        # Album/Playlist art - BIGGER, NO WEIRD BORDER
        art_label = QLabel()
        art_label.setObjectName(f"art_{queue_id}")
        art_label.setFixedSize(150, 150)
        art_label.setStyleSheet("background-color: #2b2b2b; border: none; border-radius: 8px;")
        art_label.setAlignment(Qt.AlignCenter)
        art_label.setScaledContents(True)  # Fill the entire square
        art_label.setText("🎵")
        art_label.setFont(QFont("", 48))
        card_layout.addWidget(art_label)

        # Info section - ONE SIMPLE TEXT BOX
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(10, 10, 10, 10)

        # Single combined text label with rich formatting
        album_name = metadata.get('name', 'Loading...')
        artist_name = metadata.get('artist', metadata.get('artists', 'Fetching metadata...'))

        # Format text with HTML for better styling
        combined_text = f'<div style="line-height: 1.4;">' \
                       f'<span style="font-size: 16pt; font-weight: bold; color: #FFFFFF;">{album_name}</span><br>' \
                       f'<span style="font-size: 11pt; color: #AAAAAA;">{artist_name}</span>' \
                       f'</div>'

        text_label = QLabel(combined_text)
        text_label.setObjectName(f"text_{queue_id}")
        text_label.setTextFormat(Qt.RichText)  # Enable HTML formatting
        text_label.setStyleSheet("padding: 5px; background-color: transparent;")
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        info_layout.addWidget(text_label, 1)

        # Progress bar with song count
        progress_bar = QProgressBar()
        progress_bar.setObjectName(f"progress_{queue_id}")
        progress_bar.setFixedHeight(28)
        progress_bar.setValue(0)
        progress_bar.setFormat("%p%")
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3d3d3d;
                border-radius: 6px;
                text-align: center;
                background-color: #1a1a1a;
                color: white;
                font-weight: bold;
                font-size: 11pt;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        info_layout.addWidget(progress_bar)

        card_layout.addLayout(info_layout, 1)

        # Store references
        card.art_label = art_label
        card.text_label = text_label
        card.progress_bar = progress_bar
        card.album_name = album_name
        card.artist_name = artist_name
        card.current_song = ""

        # Track song counts
        card.total_songs = 0
        card.completed_songs = 0

        # Add to queue preview (insert before the stretch)
        self.queue_preview_layout.insertWidget(self.queue_preview_layout.count() - 1, card)

        # Store card reference
        self.queue_items[queue_id] = card

        print(f"[DEBUG] Created queue card for {queue_id}")
        print(f"[DEBUG] Album: '{album_name}', Artist: '{artist_name}'")

        # Load image if URL available
        if 'image_url' in metadata and metadata['image_url']:
            self.load_queue_image(queue_id, metadata['image_url'])

        return card

    def load_queue_image(self, queue_id, image_url):
        """Load album/playlist image asynchronously"""
        request = QNetworkRequest(QUrl(image_url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.on_image_loaded(queue_id, reply))

    def on_image_loaded(self, queue_id, reply):
        """Handle loaded image"""
        if queue_id not in self.queue_items:
            reply.deleteLater()
            return

        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)

            if not pixmap.isNull():
                # Scale to fill 150x150 (expand to fill, then crop to center)
                scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

                # Crop to exact 150x150 if needed (center crop)
                if scaled_pixmap.width() > 150 or scaled_pixmap.height() > 150:
                    x = (scaled_pixmap.width() - 150) // 2
                    y = (scaled_pixmap.height() - 150) // 2
                    scaled_pixmap = scaled_pixmap.copy(x, y, 150, 150)

                self.queue_items[queue_id].art_label.setPixmap(scaled_pixmap)
                self.queue_items[queue_id].art_label.setText("")

        reply.deleteLater()

    def update_queue_progress(self, queue_id, progress):
        """Update progress bar for a queue item"""
        print(f"[DEBUG] Updating progress for queue_id={queue_id}, progress={progress}, exists={queue_id in self.queue_items}")
        if queue_id in self.queue_items:
            self.queue_items[queue_id].progress_bar.setValue(int(progress))
            print(f"[DEBUG] Progress updated to {progress}%")
        else:
            print(f"[DEBUG] Queue ID not found in items. Available: {list(self.queue_items.keys())}")

    def update_current_song(self, queue_id, song_name):
        """Update the current song being downloaded"""
        if queue_id in self.queue_items:
            card = self.queue_items[queue_id]

            # Update current song and refresh text with HTML formatting
            card.current_song = song_name
            combined_text = f'<div style="line-height: 1.4;">' \
                           f'<span style="font-size: 16pt; font-weight: bold; color: #FFFFFF;">{card.album_name}</span><br>' \
                           f'<span style="font-size: 11pt; color: #AAAAAA;">{card.artist_name}</span><br>' \
                           f'<span style="font-size: 10pt; color: #4CAF50; font-style: italic;">🎵 {song_name}</span>' \
                           f'</div>'
            card.text_label.setText(combined_text)
            print(f"[DEBUG] Updated current song for {queue_id}: {song_name}")

            # Update song count and progress bar format
            card.completed_songs += 1
            if card.total_songs > 0:
                progress = int((card.completed_songs / card.total_songs) * 100)
                card.progress_bar.setValue(progress)
                # Format: "8/8 songs (100%)"
                card.progress_bar.setFormat(f"{card.completed_songs}/{card.total_songs} songs ({progress}%)")
                print(f"[DEBUG] Progress: {card.completed_songs}/{card.total_songs} songs ({progress}%)")
        else:
            print(f"[DEBUG] Queue ID {queue_id} not found for current song update")

    def update_queue_card_metadata(self, queue_id, metadata):
        """Update queue card with fetched metadata"""
        print(f"[DEBUG] update_queue_card_metadata called for queue_id={queue_id}")
        print(f"[DEBUG] Metadata: name={metadata.get('name')}, artist={metadata.get('artist')}, image_url={metadata.get('image_url', 'N/A')[:50]}")
        print(f"[DEBUG] queue_items keys: {list(self.queue_items.keys())}")

        if queue_id in self.queue_items:
            card = self.queue_items[queue_id]

            # Update stored metadata
            card.album_name = metadata.get('name', 'Unknown')
            card.artist_name = metadata.get('artist', 'Unknown')

            # Update text label with HTML formatting
            if card.current_song:
                combined_text = f'<div style="line-height: 1.4;">' \
                               f'<span style="font-size: 16pt; font-weight: bold; color: #FFFFFF;">{card.album_name}</span><br>' \
                               f'<span style="font-size: 11pt; color: #AAAAAA;">{card.artist_name}</span><br>' \
                               f'<span style="font-size: 10pt; color: #4CAF50; font-style: italic;">🎵 {card.current_song}</span>' \
                               f'</div>'
            else:
                combined_text = f'<div style="line-height: 1.4;">' \
                               f'<span style="font-size: 16pt; font-weight: bold; color: #FFFFFF;">{card.album_name}</span><br>' \
                               f'<span style="font-size: 11pt; color: #AAAAAA;">{card.artist_name}</span>' \
                               f'</div>'
            card.text_label.setText(combined_text)

            print(f"[DEBUG] Updated text - Album: '{card.album_name}', Artist: '{card.artist_name}'")

            # Load image if available
            if 'image_url' in metadata and metadata['image_url']:
                print(f"[DEBUG] Loading image for {queue_id}: {metadata['image_url'][:50]}")
                self.load_queue_image(queue_id, metadata['image_url'])
            else:
                print(f"[DEBUG] No image_url in metadata")
        else:
            print(f"[DEBUG] ERROR: queue_id {queue_id} not found in queue_items!")

    def remove_queue_card(self, queue_id):
        """Remove a queue card when download is complete"""
        if queue_id in self.queue_items:
            card = self.queue_items[queue_id]
            self.queue_preview_layout.removeWidget(card)
            card.deleteLater()
            del self.queue_items[queue_id]

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

        # Generate unique queue ID
        queue_id = str(hash(query + str(timestamp)))

        # Create initial queue card with placeholder data
        initial_metadata = {
            'name': 'Loading...',
            'artist': 'Fetching metadata...',
            'type': content_type
        }
        # Create card via signal (thread-safe)
        self.create_card_signal.emit(queue_id, initial_metadata)

        # Clear URL input
        self.url_entry.clear()

        # Switch to queue tab immediately (no UI freeze!)
        self.tab_widget.setCurrentIndex(1)

        # Create QueueItem with all settings
        settings = {
            'format': format_val,
            'bitrate': bitrate_val,
            'threads': int(threads_val),
            'template': template_val,
            'download_folder': download_folder,
            'folder_per_url': folder_per_url,
            'is_playlist_url': is_playlist_url,
            'is_album_url': is_album_url,
            'preload': preload,
            'sponsor_block': sponsor_block,
            'skip_explicit': skip_explicit,
            'generate_lrc': generate_lrc,
            'playlist_numbering': playlist_numbering
        }

        queue_item = QueueItem(
            queue_id=queue_id,
            query=query,
            status='pending',
            settings=settings,
            metadata=initial_metadata,
            progress=0,
            created_at=datetime.now()
        )

        # Add to queue manager (it will process items one at a time)
        self.queue_manager.add_to_queue(queue_item)

    def prepare_and_download(self, queue_id, query, format_val, bitrate_val, threads_val,
                            template_val, download_folder, folder_per_url,
                            is_playlist_url, is_album_url,
                            preload, sponsor_block, skip_explicit, generate_lrc,
                            playlist_numbering):
        """Prepare download folder (fetch metadata if needed) and start download - runs in background thread"""

        # Fetch metadata to update queue card
        metadata = None
        if is_playlist_url or is_album_url:
            content_type_name = "album" if is_album_url else "playlist"
            self.log_to_queue(f"🔍 Fetching {content_type_name} metadata from Spotify...\n")
            metadata = self.get_spotify_metadata(query)

            if metadata:
                self.log_to_queue(f"✅ Found {content_type_name}: {metadata.get('name', 'Unknown')}\n")

                # Update queue card with real metadata
                artists_str = ', '.join(metadata.get('artists', [])) if isinstance(metadata.get('artists'), list) else metadata.get('artist', 'Unknown')
                updated_metadata = {
                    'name': metadata.get('name', 'Unknown'),
                    'artist': artists_str,
                    'type': metadata.get('type', content_type_name),
                    'image_url': metadata.get('image_url', metadata.get('cover_url', ''))
                }
                print(f"[DEBUG] Emitting metadata update signal for queue_id={queue_id}")
                print(f"[DEBUG] Metadata to update: {updated_metadata}")
                # Use signal for thread-safe GUI update
                self.update_metadata_signal.emit(queue_id, updated_metadata)
            else:
                self.log_to_queue(f"⚠️ Could not fetch metadata\n")

        # Handle folder per URL organization
        if folder_per_url:
            # For albums and playlists, try to get real names
            if is_playlist_url or is_album_url:
                if metadata:
                    # Use the auto-detected name
                    folder_name = self.sanitize_folder_name(metadata['name'])
                else:
                    # Metadata fetch failed, fallback to URL-based naming
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

        # Set progress to downloading
        self.update_progress_signal.emit(queue_id, 50)

        # Now run the actual download
        self.run_download(queue_id, cmd, download_folder, query)

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

                print(f"[DEBUG] Metadata fetched successfully: {metadata.get('name', 'Unknown')}")
            else:
                print(f"[DEBUG] Metadata fetch returned None for: {url_or_query}")

            return metadata

        except Exception as e:
            # If metadata fetch fails, log error and return None to fallback to URL-based naming
            print(f"[ERROR] Failed to fetch metadata for {url_or_query}: {e}")
            import traceback
            traceback.print_exc()
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

    def run_download(self, queue_id, cmd, download_folder, query):
        """Run spotdl command in background with real-time output and per-song tracking"""
        print(f"[DEBUG] Starting download for queue_id: {queue_id}")

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

            # Track song count
            import re

            # Read output line by line in real-time
            for line in process.stdout:
                self.log_to_queue(line)

                # Parse total songs: "Found 8 songs in Number One (Album)"
                if "Found" in line and "song" in line:
                    match = re.search(r'Found (\d+) song', line)
                    if match:
                        total_songs = int(match.group(1))
                        print(f"[DEBUG] Found {total_songs} songs for {queue_id}")
                        # Update card's total_songs
                        if queue_id in self.queue_items:
                            self.queue_items[queue_id].total_songs = total_songs
                            self.queue_items[queue_id].completed_songs = 0
                            # Update progress bar format
                            self.queue_items[queue_id].progress_bar.setFormat(f"0/{total_songs} songs")

                # Parse individual song downloads: Downloaded "MASSIVE HASSLE - Twos": https://...
                if "Downloaded" in line and '"' in line:
                    # Extract song name from quotes
                    match = re.search(r'Downloaded "([^"]+)"', line)
                    if match:
                        song_name = match.group(1)
                        print(f"[DEBUG] Downloaded song: {song_name}")
                        # Update current song via signal (thread-safe)
                        self.update_current_song_signal.emit(queue_id, song_name)

                # Generic progress updates for other lines
                elif "Processing" in line or "Downloading" in line:
                    # Only update if we don't have per-song tracking yet
                    if queue_id in self.queue_items and self.queue_items[queue_id].total_songs == 0:
                        self.update_progress_signal.emit(queue_id, 50)

            # Wait for completion
            process.wait()

            # Log completion
            timestamp = datetime.now().strftime("%H:%M:%S")
            # Capture queue_id properly for lambdas
            qid = queue_id

            if process.returncode == 0:
                self.log_to_queue(f"\n[{timestamp}] ✅ Download completed successfully!\n")
                self.log_to_queue(f"📁 Files saved to: {download_folder}\n")
                # Update progress to 100%
                print(f"[DEBUG] Download complete for queue_id: {queue_id}")
                self.update_progress_signal.emit(queue_id, 100)
                # Update text to show completion
                if queue_id in self.queue_items:
                    card = self.queue_items[queue_id]
                    card.current_song = "✅ Completed"
                    combined_text = f'<div style="line-height: 1.4;">' \
                                   f'<span style="font-size: 16pt; font-weight: bold; color: #FFFFFF;">{card.album_name}</span><br>' \
                                   f'<span style="font-size: 11pt; color: #AAAAAA;">{card.artist_name}</span><br>' \
                                   f'<span style="font-size: 10pt; color: #4CAF50; font-weight: bold;">✅ Completed</span>' \
                                   f'</div>'
                    card.text_label.setText(combined_text)
                # Note: Card removal is handled by auto-clear or manual clear
            else:
                self.log_to_queue(f"\n[{timestamp}] ❌ Download failed with exit code {process.returncode}\n")
                print(f"[DEBUG] Download failed for queue_id: {queue_id}")
                if queue_id in self.queue_items:
                    card = self.queue_items[queue_id]
                    card.current_song = "❌ Failed"
                    combined_text = f'<div style="line-height: 1.4;">' \
                                   f'<span style="font-size: 16pt; font-weight: bold; color: #FFFFFF;">{card.album_name}</span><br>' \
                                   f'<span style="font-size: 11pt; color: #AAAAAA;">{card.artist_name}</span><br>' \
                                   f'<span style="font-size: 10pt; color: #F44336; font-weight: bold;">❌ Failed</span>' \
                                   f'</div>'
                    card.text_label.setText(combined_text)

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_to_queue(f"\n[{timestamp}] ❌ Error: {str(e)}\n")
            # Remove card on error
            qid = queue_id
            print(f"[DEBUG] Download error for queue_id: {qid}: {e}")
            QTimer.singleShot(3000, lambda q=qid: self.remove_queue_card(q))

    def clear_queue_log(self):
        """Clear the queue log display"""
        self.queue_textbox.clear()
        self.log_to_queue("🧹 Log cleared\n")

    def toggle_queue_pause(self):
        """Toggle pause/resume for the download queue"""
        if not hasattr(self, 'queue_manager'):
            return

        if self.queue_manager.paused:
            # Resume
            self.queue_manager.resume_queue()
            self.pause_resume_btn.setText("⏸ Pause")
            self.queue_status_label.setText("Running")
            self.queue_status_label.setStyleSheet("color: #4CAF50; font-size: 12pt;")
        else:
            # Pause
            self.queue_manager.pause_queue()
            self.pause_resume_btn.setText("▶ Resume")
            self.queue_status_label.setText("Paused")
            self.queue_status_label.setStyleSheet("color: #FF9800; font-size: 12pt;")

    def clear_completed_items(self):
        """Clear completed/failed/cancelled items from queue"""
        if not hasattr(self, 'queue_manager'):
            return

        # Get list of completed items before clearing
        with self.queue_manager.lock:
            completed_ids = [
                item.queue_id for item in self.queue_manager.queue
                if item.is_finished()
            ]

        # Remove visual cards for completed items
        for queue_id in completed_ids:
            if queue_id in self.queue_items:
                self.remove_queue_card(queue_id)
                print(f"[GUI] Removed card for completed item: {queue_id}")

        # Clear from queue manager
        self.queue_manager.clear_completed()
        self.update_queue_status()
        print(f"[GUI] Cleared {len(completed_ids)} completed items")

    def remove_queue_item_by_id(self, queue_id: str):
        """Remove a specific queue item by ID (used for auto-clear)"""
        if not hasattr(self, 'queue_manager'):
            return

        # Remove from queue manager
        with self.queue_manager.lock:
            original_len = len(self.queue_manager.queue)
            self.queue_manager.queue = [
                item for item in self.queue_manager.queue
                if item.queue_id != queue_id
            ]
            removed = original_len - len(self.queue_manager.queue)

        # Remove timer from tracking dict
        if queue_id in self.auto_clear_timers:
            self.auto_clear_timers[queue_id].stop()
            del self.auto_clear_timers[queue_id]

        if removed > 0:
            print(f"[GUI] Auto-cleared queue item: {queue_id}")
            self.log_to_queue(f"🧹 Auto-cleared completed download\n")
            self.update_queue_status()

    def update_queue_status(self):
        """Update the queue status labels"""
        if not hasattr(self, 'queue_manager'):
            return

        summary = self.queue_manager.get_queue_summary()

        # Update statistics label
        pending = summary['pending']
        downloading = summary['downloading']
        completed = summary['completed']
        failed = summary['failed']
        cancelled = summary['cancelled']
        total = summary['total']

        if total == 0:
            self.queue_stats_label.setText("No downloads in queue")
            self.pause_resume_btn.setEnabled(False)
        else:
            parts = []
            if pending > 0:
                parts.append(f"{pending} pending")
            if downloading > 0:
                parts.append(f"{downloading} downloading")
            if completed > 0:
                parts.append(f"{completed} completed")
            if failed > 0:
                parts.append(f"{failed} failed")
            if cancelled > 0:
                parts.append(f"{cancelled} cancelled")

            status_text = " | ".join(parts) if parts else "Queue empty"
            self.queue_stats_label.setText(f"Queue: {status_text} (Total: {total})")
            self.pause_resume_btn.setEnabled(pending > 0 or downloading > 0)

        # Update status label color based on state
        if self.queue_manager.paused:
            self.queue_status_label.setText("Paused")
            self.queue_status_label.setStyleSheet("color: #FF9800; font-size: 12pt;")
        elif downloading > 0:
            self.queue_status_label.setText("Downloading")
            self.queue_status_label.setStyleSheet("color: #4CAF50; font-size: 12pt;")
        elif pending > 0:
            self.queue_status_label.setText("Processing")
            self.queue_status_label.setStyleSheet("color: #2196F3; font-size: 12pt;")
        else:
            self.queue_status_label.setText("Ready")
            self.queue_status_label.setStyleSheet("color: #888888; font-size: 12pt;")

        # Auto-clear completed downloads if enabled
        if hasattr(self, 'auto_clear_queue_check') and self.auto_clear_queue_check.isChecked():
            # Get all queue items
            with self.queue_manager.lock:
                for item in self.queue_manager.queue:
                    # Check if item is finished and not already scheduled for removal
                    if item.is_finished() and item.queue_id not in self.auto_clear_timers:
                        # Create timer to remove this item after 5 seconds
                        timer = QTimer()
                        timer.setSingleShot(True)

                        # Use lambda with default parameter to capture queue_id by value
                        qid = item.queue_id
                        timer.timeout.connect(lambda q=qid: self.remove_queue_item_by_id(q))

                        # Store timer and start it
                        self.auto_clear_timers[item.queue_id] = timer
                        timer.start(5000)  # 5 seconds

                        print(f"[GUI] Scheduled auto-clear for {item.queue_id} in 5 seconds")


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
