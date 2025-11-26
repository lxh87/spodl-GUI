#!/usr/bin/env python3
"""
SpotDL Desktop GUI v2.2
A modern desktop interface for SpotDL - PySide6 version
Polished UI with resizable panels
"""

import subprocess
import threading
import os
from pathlib import Path
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLineEdit, QTextEdit, QLabel,
    QComboBox, QCheckBox, QSlider, QFrame, QFileDialog, QMessageBox,
    QTabWidget, QScrollArea, QProgressBar, QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap

# Import queue management
from queue_item import QueueItem
from queue_manager import DownloadQueueManager

# Import GUI modules
from gui.utils import ThreadSafeLogger, ClipboardMonitor, is_playlist, is_album
from gui.theme import get_dark_theme_stylesheet
from gui.config import ConfigManager
from gui.controller import DownloadController
from gui.queue_panel import QueuePanel
from gui.queue_card import QueueCard

# Lazy import metadata handler
_metadata_handler = None

def get_metadata_handler():
    global _metadata_handler
    if _metadata_handler is None:
        from metadata_handler import SpotifyMetadataHandler
        _metadata_handler = SpotifyMetadataHandler()
    return _metadata_handler


class SpotDLGUI(QMainWindow):
    # Qt Signals for thread-safe GUI updates
    create_card_signal = Signal(str, dict)
    update_metadata_signal = Signal(str, dict)
    update_progress_signal = Signal(str, int)
    update_current_song_signal = Signal(str, str)
    update_song_count_signal = Signal(str, int, int)

    def __init__(self):
        super().__init__()

        self.config_manager = ConfigManager()
        self.settings = self.config_manager.settings

        self.setWindowTitle("SpotDL GUI")
        self.resize(1400, 900)
        self.setMinimumSize(1100, 700)

        self.setStyleSheet(get_dark_theme_stylesheet())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: none; background-color: #1a1a1a; }
            QTabBar::tab {
                background-color: #2b2b2b; color: white;
                padding: 8px 20px; margin-right: 2px;
                border-top-left-radius: 4px; border-top-right-radius: 4px;
                font-weight: bold; font-size: 10pt;
            }
            QTabBar::tab:selected { background-color: #4CAF50; }
            QTabBar::tab:hover:!selected { background-color: #3d3d3d; }
        """)
        main_layout.addWidget(self.tab_widget, 1)

        self.clipboard_monitor = ClipboardMonitor()
        self.clipboard_monitor.url_detected.connect(self._on_clipboard_url_detected)
        self.download_controller = DownloadController(self.get_spotify_metadata)

        self.create_main_tab()
        self.create_settings_tab()

        self.clipboard_monitor_check.setChecked(True)
        self.queue_manager = DownloadQueueManager(self)
        self.auto_clear_timers = {}

        self.create_card_signal.connect(self._create_queue_card_wrapper)
        self.update_metadata_signal.connect(self._update_metadata_wrapper)
        self.update_progress_signal.connect(self._update_progress_wrapper)
        self.update_current_song_signal.connect(self._update_current_song_wrapper)
        self.update_song_count_signal.connect(self._update_song_count_wrapper)

        self.update_command_preview()

        self.queue_status_timer = QTimer()
        self.queue_status_timer.timeout.connect(self.update_queue_status)
        self.queue_status_timer.start(2000)

        QTimer.singleShot(100, self.check_spotdl)


    def create_sidebar(self):
        """Create compact sidebar"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(120)
        self.sidebar.setStyleSheet("background-color: #202020;")

        layout = QVBoxLayout(self.sidebar)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 14, 10, 14)

        # Logo
        self.logo_label = QLabel("🎵 SpotDL")
        self.logo_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)

        self.version_label = QLabel("v4.4.3")
        self.version_label.setStyleSheet("color: #555; font-size: 8pt;")
        self.version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.version_label)

        layout.addStretch()

        # Music folder button
        self.open_folder_btn = QPushButton("📁 Music")
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                font-size: 9pt;
                padding: 6px 4px;
            }
            QPushButton:hover { background-color: #444; }
        """)
        self.open_folder_btn.clicked.connect(self.open_download_folder)
        layout.addWidget(self.open_folder_btn)

    def save_settings(self):
        try:
            self.config_manager.update({
                "format": self.format_combo.currentText(),
                "bitrate": self.bitrate_combo.currentText(),
                "threads": str(self.threads_slider.value()),
                "output": self.template_entry.text(),
                "playlist_output": self.playlist_template_entry.text(),
                "download_folder": self.folder_entry.text(),
                "create_folder_per_url": self.folder_per_url_check.isChecked(),
                "auto_download": self.auto_download_check.isChecked(),
                "auto_clear_completed": self.auto_clear_queue_check.isChecked()
            })

            if self.config_manager.save_settings():
                self.log_to_queue("✅ Settings saved\n")
            else:
                QMessageBox.critical(self, "Error", "Failed to save settings")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

    def check_spotdl(self):
        try:
            result = subprocess.run(["spotdl", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.version_label.setText(version)
        except:
            QMessageBox.warning(self, "SpotDL Not Found",
                "SpotDL is not installed.\nInstall with: pip install spotdl")

    def flash_taskbar(self):
        QApplication.alert(self, 3000)
        original_title = self.windowTitle()
        self.setWindowTitle("🔔 Link Detected! - SpotDL GUI")
        QTimer.singleShot(3000, lambda: self.setWindowTitle(original_title))

    # =========================================================================
    # MAIN TAB
    # =========================================================================

    def create_main_tab(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Horizontal splitter for left/right panels
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        left_panel = self.create_download_panel()
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(420)
        self.main_splitter.addWidget(left_panel)

        self.queue_panel = QueuePanel(
            auto_download=self.settings.get("auto_download", True),
            auto_clear=self.settings.get("auto_clear_completed", False)
        )
        self.queue_panel.setMinimumWidth(450)

        # Connect signals
        self.queue_panel.start_queue_clicked.connect(self.start_queue)
        self.queue_panel.pause_queue_clicked.connect(self.pause_queue)
        self.queue_panel.clear_completed_clicked.connect(self.clear_completed_items)
        self.queue_panel.auto_download_changed.connect(self.on_auto_download_changed)

        self.main_splitter.addWidget(self.queue_panel)

        self.main_splitter.setSizes([340, 860])
        main_layout.addWidget(self.main_splitter)

        self.tab_widget.addTab(main_widget, "🎵 Downloads")

    def create_download_panel(self):
        """Create compact left panel"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header = QLabel("Add to Queue")
        header.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(header)

        # URL Section
        url_section = QFrame()
        url_section.setStyleSheet("background-color: #252525; border-radius: 5px;")
        url_layout = QVBoxLayout(url_section)
        url_layout.setSpacing(5)
        url_layout.setContentsMargins(10, 8, 10, 8)

        # URL header row
        url_header = QHBoxLayout()
        url_header.setSpacing(4)
        url_label = QLabel("URL:")
        url_label.setStyleSheet("font-weight: bold; font-size: 9pt;")
        url_header.addWidget(url_label)
        url_header.addStretch()

        self.clipboard_monitor_check = QCheckBox("Auto-detect")
        self.clipboard_monitor_check.setStyleSheet("font-size: 8pt;")
        self.clipboard_monitor_check.stateChanged.connect(self.toggle_clipboard_monitoring)
        url_header.addWidget(self.clipboard_monitor_check)
        url_layout.addLayout(url_header)

        # URL input
        url_row = QHBoxLayout()
        url_row.setSpacing(4)
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("Paste Spotify/YouTube URL...")
        self.url_entry.setFixedHeight(28)
        self.url_entry.textChanged.connect(self.update_command_preview)
        url_row.addWidget(self.url_entry)

        paste_btn = QPushButton("📋")
        paste_btn.setFixedSize(28, 28)
        paste_btn.setStyleSheet("padding: 0; font-size: 11pt;")
        paste_btn.clicked.connect(self.paste_url)
        url_row.addWidget(paste_btn)
        url_layout.addLayout(url_row)

        # Quick buttons - compact row
        quick_row = QHBoxLayout()
        quick_row.setSpacing(3)
        quick_label = QLabel("Quick:")
        quick_label.setStyleSheet("color: #666; font-size: 8pt;")
        quick_row.addWidget(quick_label)

        for text, val in [("Liked", "saved"), ("Playlists", "all-user-playlists"), ("Artists", "all-user-followed-artists")]:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #333; font-size: 8pt;
                    padding: 3px 6px; min-width: 40px;
                }
                QPushButton:hover { background-color: #444; }
            """)
            btn.setFixedHeight(22)
            btn.clicked.connect(lambda c, v=val: self.url_entry.setText(v))
            quick_row.addWidget(btn)
        quick_row.addStretch()
        url_layout.addLayout(quick_row)

        layout.addWidget(url_section)

        # Options Section - compact
        options_section = QFrame()
        options_section.setStyleSheet("background-color: #252525; border-radius: 5px;")
        options_layout = QVBoxLayout(options_section)
        options_layout.setSpacing(5)
        options_layout.setContentsMargins(10, 8, 10, 8)

        options_label = QLabel("Options")
        options_label.setStyleSheet("font-weight: bold; font-size: 9pt;")
        options_layout.addWidget(options_label)

        # Format row - tight
        format_row = QHBoxLayout()
        format_row.setSpacing(8)

        # Format
        fmt_box = QVBoxLayout()
        fmt_box.setSpacing(1)
        fmt_lbl = QLabel("Format")
        fmt_lbl.setStyleSheet("color: #777; font-size: 8pt;")
        fmt_box.addWidget(fmt_lbl)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "flac", "ogg", "opus", "m4a", "wav"])
        self.format_combo.setCurrentText(self.settings.get("format", "mp3"))
        self.format_combo.setFixedHeight(26)
        self.format_combo.currentTextChanged.connect(self.update_command_preview)
        fmt_box.addWidget(self.format_combo)
        format_row.addLayout(fmt_box)

        # Bitrate
        br_box = QVBoxLayout()
        br_box.setSpacing(1)
        br_lbl = QLabel("Bitrate")
        br_lbl.setStyleSheet("color: #777; font-size: 8pt;")
        br_box.addWidget(br_lbl)
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["auto", "320k", "256k", "192k", "128k"])
        self.bitrate_combo.setCurrentText(self.settings.get("bitrate", "320k"))
        self.bitrate_combo.setFixedHeight(26)
        self.bitrate_combo.currentTextChanged.connect(self.update_command_preview)
        br_box.addWidget(self.bitrate_combo)
        format_row.addLayout(br_box)

        options_layout.addLayout(format_row)

        # Checkboxes - tight 2-column grid
        checks_grid = QGridLayout()
        checks_grid.setSpacing(2)
        checks_grid.setContentsMargins(0, 2, 0, 0)

        self.preload_check = QCheckBox("Preload URLs")
        self.sponsor_block_check = QCheckBox("Skip Sponsors")
        self.skip_explicit_check = QCheckBox("Skip Explicit")
        self.generate_lrc_check = QCheckBox("Generate LRC")
        self.playlist_numbering_check = QCheckBox("Playlist #")
        self.folder_per_url_check = QCheckBox("Folder per URL")
        self.folder_per_url_check.setChecked(self.settings.get("create_folder_per_url", True))

        for i, cb in enumerate([self.preload_check, self.sponsor_block_check,
                                self.skip_explicit_check, self.generate_lrc_check,
                                self.playlist_numbering_check, self.folder_per_url_check]):
            cb.setStyleSheet("font-size: 8pt;")
            checks_grid.addWidget(cb, i // 2, i % 2)

        options_layout.addLayout(checks_grid)
        layout.addWidget(options_section)

        # Stretch to push command preview and button to bottom
        layout.addStretch()

        # Command preview - minimal
        cmd_frame = QFrame()
        cmd_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
        cmd_layout = QVBoxLayout(cmd_frame)
        cmd_layout.setSpacing(2)
        cmd_layout.setContentsMargins(8, 5, 8, 5)

        cmd_header = QHBoxLayout()
        cmd_label = QLabel("Command")
        cmd_label.setStyleSheet("color: #444; font-size: 8pt;")
        cmd_header.addWidget(cmd_label)
        cmd_header.addStretch()

        copy_btn = QPushButton("Copy")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #333; font-size: 7pt;
                padding: 2px 6px;
            }
            QPushButton:hover { background-color: #444; }
        """)
        copy_btn.setFixedHeight(16)
        copy_btn.clicked.connect(self.copy_command)
        cmd_header.addWidget(copy_btn)
        cmd_layout.addLayout(cmd_header)

        self.command_entry = QLineEdit()
        self.command_entry.setReadOnly(True)
        self.command_entry.setStyleSheet("""
            QLineEdit {
                font-family: Consolas, monospace;
                font-size: 8pt;
                background-color: #111;
                border: none;
                padding: 3px;
            }
        """)
        self.command_entry.setFixedHeight(20)
        cmd_layout.addWidget(self.command_entry)

        layout.addWidget(cmd_frame)

        # Add Job Button - at the very bottom
        self.add_job_btn = QPushButton("➕ Add Job")
        self.add_job_btn.setFixedHeight(38)
        self.add_job_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.add_job_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
        """)
        self.add_job_btn.clicked.connect(self.add_to_queue)
        layout.addWidget(self.add_job_btn)

        return panel

    def create_queue_panel(self):
        """Create right panel with resizable log"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a;")

        layout = QVBoxLayout(panel)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header row
        header_row = QHBoxLayout()
        title = QLabel("Download Queue")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        header_row.addWidget(title)

        self.queue_status_label = QLabel("Ready")
        self.queue_status_label.setStyleSheet("color: #555; font-size: 9pt; margin-left: 6px;")
        header_row.addWidget(self.queue_status_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Controls row - compact
        controls_frame = QFrame()
        controls_frame.setStyleSheet("background-color: #252525; border-radius: 5px;")
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(4)
        controls_layout.setContentsMargins(8, 6, 8, 6)

        # Compact control buttons
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; font-size: 8pt; padding: 4px 8px; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #2b2b2b; color: #555; }
        """)
        self.start_btn.setFixedHeight(24)
        self.start_btn.clicked.connect(self.start_queue)
        self.start_btn.setEnabled(False)
        controls_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setStyleSheet("""
            QPushButton { background-color: #FF9800; font-size: 8pt; padding: 4px 8px; }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:disabled { background-color: #2b2b2b; color: #555; }
        """)
        self.pause_btn.setFixedHeight(24)
        self.pause_btn.clicked.connect(self.pause_queue)
        self.pause_btn.setEnabled(False)
        controls_layout.addWidget(self.pause_btn)

        self.clear_btn = QPushButton("🧹 Clear")
        self.clear_btn.setStyleSheet("""
            QPushButton { background-color: #424242; font-size: 8pt; padding: 4px 8px; }
            QPushButton:hover { background-color: #555; }
        """)
        self.clear_btn.setFixedHeight(24)
        self.clear_btn.clicked.connect(self.clear_completed_items)
        controls_layout.addWidget(self.clear_btn)

        controls_layout.addStretch()

        # Checkboxes - compact
        self.auto_download_check = QCheckBox("Auto-download")
        self.auto_download_check.setStyleSheet("font-size: 8pt;")
        self.auto_download_check.setChecked(self.settings.get("auto_download", True))
        self.auto_download_check.stateChanged.connect(self.on_auto_download_changed)
        controls_layout.addWidget(self.auto_download_check)

        self.auto_clear_queue_check = QCheckBox("Auto-clear")
        self.auto_clear_queue_check.setStyleSheet("font-size: 8pt;")
        self.auto_clear_queue_check.setChecked(self.settings.get("auto_clear_completed", False))
        controls_layout.addWidget(self.auto_clear_queue_check)

        layout.addWidget(controls_frame)

        # Stats label - styled
        self.queue_stats_label = QLabel("No jobs in queue")
        self.queue_stats_label.setStyleSheet("color: #555; font-size: 8pt; padding: 2px 0;")
        layout.addWidget(self.queue_stats_label)

        # Vertical splitter for queue cards and log
        self.queue_splitter = QSplitter(Qt.Vertical)
        self.queue_splitter.setChildrenCollapsible(False)

        # Queue cards area
        queue_container = QWidget()
        queue_container.setMinimumHeight(120)
        queue_layout = QVBoxLayout(queue_container)
        queue_layout.setContentsMargins(0, 0, 0, 0)

        self.queue_preview_scroll = QScrollArea()
        self.queue_preview_scroll.setWidgetResizable(True)
        self.queue_preview_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 5px;
            }
        """)

        self.queue_preview_widget = QWidget()
        self.queue_preview_widget.setStyleSheet("background-color: #1e1e1e;")
        self.queue_preview_layout = QVBoxLayout(self.queue_preview_widget)
        self.queue_preview_layout.setSpacing(4)
        self.queue_preview_layout.setContentsMargins(4, 4, 4, 4)
        self.queue_preview_layout.addStretch()

        self.queue_preview_scroll.setWidget(self.queue_preview_widget)
        queue_layout.addWidget(self.queue_preview_scroll)

        self.queue_splitter.addWidget(queue_container)

        # Log section
        log_container = QWidget()
        log_container.setMinimumHeight(80)
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(2)

        log_header = QHBoxLayout()
        log_label = QLabel("Output Log")
        log_label.setStyleSheet("font-weight: bold; color: #555; font-size: 8pt;")
        log_header.addWidget(log_label)
        log_header.addStretch()

        clear_log_btn = QPushButton("Clear")
        clear_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #333; font-size: 7pt;
                padding: 2px 6px;
            }
            QPushButton:hover { background-color: #444; }
        """)
        clear_log_btn.setFixedHeight(16)
        clear_log_btn.clicked.connect(self.clear_queue_log)
        log_header.addWidget(clear_log_btn)
        log_layout.addLayout(log_header)

        self.queue_textbox = QTextEdit()
        self.queue_textbox.setReadOnly(True)
        self.queue_textbox.setStyleSheet("""
            QTextEdit {
                font-family: Consolas, monospace;
                font-size: 8pt;
                background-color: #111;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        log_layout.addWidget(self.queue_textbox)

        self.queue_splitter.addWidget(log_container)

        # Set initial splitter sizes (75% cards, 25% log)
        self.queue_splitter.setSizes([450, 150])

        layout.addWidget(self.queue_splitter, 1)

        self.logger = ThreadSafeLogger(self.queue_textbox)

        return panel

    # =========================================================================
    # SETTINGS TAB
    # =========================================================================

    def create_settings_tab(self):
        settings_widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(settings_widget)
        self.tab_widget.addTab(scroll, "⚙️ Settings")

        layout = QVBoxLayout(settings_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        # Download folder
        folder_section = self.create_settings_section("Download Folder")
        folder_layout = folder_section.layout()

        folder_row = QHBoxLayout()
        self.folder_entry = QLineEdit()
        self.folder_entry.setText(self.settings.get("download_folder", str(Path.home() / "Music")))
        folder_row.addWidget(self.folder_entry)

        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("background-color: #333; padding: 5px 10px;")
        browse_btn.clicked.connect(self.browse_folder)
        folder_row.addWidget(browse_btn)
        folder_layout.addLayout(folder_row)

        layout.addWidget(folder_section)

        # Song template
        song_section = self.create_settings_section("Song Template")
        song_layout = song_section.layout()

        song_help = QLabel("Use / to create folders. Click tags to insert.")
        song_help.setStyleSheet("color: #555; font-size: 8pt;")
        song_layout.addWidget(song_help)

        self.template_entry = QLineEdit()
        self.template_entry.setText(self.settings.get("output", "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}"))
        self.template_entry.textChanged.connect(self.update_template_example)
        song_layout.addWidget(self.template_entry)

        self.example_output_label = QLabel("Preview: The Weeknd/2020 - After Hours/03 - Blinding Lights.mp3")
        self.example_output_label.setStyleSheet("color: #4CAF50; font-size: 8pt;")
        song_layout.addWidget(self.example_output_label)

        # Song tags - compact
        song_tags_row = QHBoxLayout()
        song_tags_row.setSpacing(2)
        for tag in ["{artist}", "{album}", "{title}", "{year}", "{track-number}", "{album-artist}", "{output-ext}"]:
            btn = self.create_tag_button(tag, self.template_entry, self.update_template_example)
            song_tags_row.addWidget(btn)
        song_tags_row.addStretch()
        song_layout.addLayout(song_tags_row)

        layout.addWidget(song_section)

        # Playlist template
        playlist_section = self.create_settings_section("Playlist Template")
        playlist_layout = playlist_section.layout()

        self.playlist_template_entry = QLineEdit()
        self.playlist_template_entry.setText(self.settings.get("playlist_output", "{list-name}/{list-position} - {artists} - {title}.{output-ext}"))
        self.playlist_template_entry.textChanged.connect(self.update_playlist_example)
        playlist_layout.addWidget(self.playlist_template_entry)

        self.playlist_example_label = QLabel("Preview: My Playlist/05 - The Weeknd - Blinding Lights.mp3")
        self.playlist_example_label.setStyleSheet("color: #4CAF50; font-size: 8pt;")
        playlist_layout.addWidget(self.playlist_example_label)

        # Playlist tags - compact
        playlist_tags_row = QHBoxLayout()
        playlist_tags_row.setSpacing(2)
        for tag in ["{list-name}", "{list-position}", "{artists}", "{title}", "{year}", "{output-ext}"]:
            btn = self.create_tag_button(tag, self.playlist_template_entry, self.update_playlist_example)
            playlist_tags_row.addWidget(btn)
        playlist_tags_row.addStretch()
        playlist_layout.addLayout(playlist_tags_row)

        layout.addWidget(playlist_section)

        # Threads
        threads_section = self.create_settings_section("Concurrent Downloads")
        threads_layout = threads_section.layout()

        threads_row = QHBoxLayout()
        self.threads_slider = QSlider(Qt.Horizontal)
        self.threads_slider.setMinimum(1)
        self.threads_slider.setMaximum(16)
        self.threads_slider.setValue(int(self.settings.get("threads", "4")))
        self.threads_slider.valueChanged.connect(lambda v: self.threads_value_label.setText(str(v)))
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
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        # SpotDL status
        spotdl_section = self.create_settings_section("SpotDL Installation")
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
        install_btn.clicked.connect(self.install_spotdl)
        btn_row.addWidget(install_btn)
        btn_row.addStretch()
        spotdl_layout.addLayout(btn_row)

        layout.addWidget(spotdl_section)
        layout.addStretch()

        self.check_spotdl_installation()

    def create_settings_section(self, title):
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

    def create_tag_button(self, tag, entry, update_func):
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
        btn.clicked.connect(lambda: self.insert_tag(entry, tag, update_func))
        return btn

    def insert_tag(self, entry, tag, update_func):
        pos = entry.cursorPosition()
        text = entry.text()
        entry.setText(text[:pos] + tag + text[pos:])
        entry.setCursorPosition(pos + len(tag))
        update_func()

    def update_template_example(self):
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

    def update_playlist_example(self):
        template = self.playlist_template_entry.text()
        replacements = {
            "{list-name}": "My Playlist", "{list-position}": "05", "{list-length}": "50",
            "{artist}": "The Weeknd", "{artists}": "The Weeknd", "{album}": "After Hours",
            "{title}": "Blinding Lights", "{year}": "2020", "{output-ext}": "mp3"
        }
        for k, v in replacements.items():
            template = template.replace(k, v)
        self.playlist_example_label.setText(f"Preview: {template}")

    # =========================================================================
    # QUEUE CARDS
    # =========================================================================

    def create_queue_card(self, queue_id, metadata):
        """Create compact queue card"""
        card = QFrame()
        card.setObjectName(f"card_{queue_id}")
        card.setStyleSheet("""
            QFrame {
                background-color: #282828;
                border: 1px solid #333;
                border-radius: 5px;
            }
            QFrame:hover { border-color: #4CAF50; }
        """)
        card.setFixedHeight(62)

        layout = QHBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 4, 8, 4)

        # Art - smaller
        art_label = QLabel()
        art_label.setFixedSize(52, 52)
        art_label.setStyleSheet("background-color: #1a1a1a; border-radius: 3px;")
        art_label.setAlignment(Qt.AlignCenter)
        art_label.setScaledContents(True)
        art_label.setText("🎵")
        art_label.setFont(QFont("", 16))
        layout.addWidget(art_label)

        # Info
        info = QWidget()
        info.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info)
        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(metadata.get('name', 'Loading...'))
        title_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #FFF;")
        info_layout.addWidget(title_label)

        artist_label = QLabel(metadata.get('artist', 'Fetching...'))
        artist_label.setStyleSheet("font-size: 9px; color: #888;")
        info_layout.addWidget(artist_label)

        song_label = QLabel("⏳ Waiting...")
        song_label.setStyleSheet("font-size: 8px; color: #555;")
        info_layout.addWidget(song_label)

        layout.addWidget(info, 1)

        # Progress - compact
        progress = QWidget()
        progress.setFixedWidth(65)
        progress.setStyleSheet("background: transparent;")
        progress_layout = QVBoxLayout(progress)
        progress_layout.setSpacing(1)
        progress_layout.setContentsMargins(0, 3, 0, 3)

        count_label = QLabel("—")
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet("font-size: 9px; color: #BBB; font-weight: bold;")
        progress_layout.addWidget(count_label)

        progress_bar = QProgressBar()
        progress_bar.setFixedHeight(4)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 2px; background: #1a1a1a; }
            QProgressBar::chunk { background: #4CAF50; border-radius: 2px; }
        """)
        progress_layout.addWidget(progress_bar)

        status_label = QLabel("Pending")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("font-size: 7px; color: #555;")
        progress_layout.addWidget(status_label)

        layout.addWidget(progress)

        # Store refs
        card.art_label = art_label
        card.title_label = title_label
        card.artist_label = artist_label
        card.song_label = song_label
        card.count_label = count_label
        card.progress_bar = progress_bar
        card.status_label = status_label
        card.total_songs = 0
        card.completed_songs = 0

        self.queue_preview_layout.insertWidget(self.queue_preview_layout.count() - 1, card)
        self.queue_items[queue_id] = card

        if metadata.get('image_url'):
            self.load_queue_image(queue_id, metadata['image_url'])

        return card

    def load_queue_image(self, queue_id, url):
        reply = self.network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self.on_image_loaded(queue_id, reply))

    def on_image_loaded(self, queue_id, reply):
        if queue_id not in self.queue_items:
            reply.deleteLater()
            return
        if reply.error() == QNetworkReply.NoError:
            pixmap = QPixmap()
            pixmap.loadFromData(reply.readAll())
            if not pixmap.isNull():
                scaled = pixmap.scaled(52, 52, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                if scaled.width() > 52 or scaled.height() > 52:
                    x, y = (scaled.width() - 52) // 2, (scaled.height() - 52) // 2
                    scaled = scaled.copy(x, y, 52, 52)
                self.queue_items[queue_id].art_label.setPixmap(scaled)
                self.queue_items[queue_id].art_label.setText("")
        reply.deleteLater()

    def update_queue_progress(self, queue_id, progress):
        if queue_id in self.queue_items:
            card = self.queue_items[queue_id]
            card.progress_bar.setValue(int(progress))
            if progress < 100:
                card.status_label.setText("Downloading")
                card.status_label.setStyleSheet("font-size: 7px; color: #4CAF50;")
            else:
                card.status_label.setText("Complete ✓")
                card.status_label.setStyleSheet("font-size: 7px; color: #4CAF50; font-weight: bold;")

    def update_current_song(self, queue_id, song_name):
        if queue_id in self.queue_items:
            card = self.queue_items[queue_id]
            display = song_name[:28] + "..." if len(song_name) > 28 else song_name
            card.song_label.setText(f"🎵 {display}")
            card.song_label.setStyleSheet("font-size: 8px; color: #4CAF50;")
            card.completed_songs += 1
            if card.total_songs > 0:
                progress = int((card.completed_songs / card.total_songs) * 100)
                card.progress_bar.setValue(progress)
                card.count_label.setText(f"{card.completed_songs}/{card.total_songs}")

    def update_song_count(self, queue_id, completed, total):
        if queue_id in self.queue_items:
            card = self.queue_items[queue_id]
            card.total_songs = total
            card.completed_songs = completed
            card.count_label.setText(f"0/{total}")
            card.song_label.setText("🔍 Scanning...")
            card.song_label.setStyleSheet("font-size: 8px; color: #2196F3;")
            card.status_label.setText("Starting")
            card.status_label.setStyleSheet("font-size: 7px; color: #2196F3;")

    def update_queue_card_metadata(self, queue_id, metadata):
        if queue_id not in self.queue_items:
            return
        card = self.queue_items[queue_id]
        card.title_label.setText(metadata.get('name', 'Unknown'))
        card.artist_label.setText(metadata.get('artist', 'Unknown'))
        if metadata.get('image_url'):
            self.load_queue_image(queue_id, metadata['image_url'])

    def remove_queue_card(self, queue_id):
        if queue_id in self.queue_items:
            card = self.queue_items[queue_id]
            self.queue_preview_layout.removeWidget(card)
            card.deleteLater()
            del self.queue_items[queue_id]

    # =========================================================================
    # QUEUE CONTROLS
    # =========================================================================

    def add_to_queue(self):
        query = self.url_entry.text().strip()
        if not query:
            QMessageBox.warning(self, "No URL", "Please enter a URL")
            return

        settings = {
            'format': self.format_combo.currentText(),
            'bitrate': self.bitrate_combo.currentText(),
            'threads': int(self.threads_slider.value()),
            'template': self.playlist_template_entry.text() if is_playlist(query) else self.template_entry.text(),
            'download_folder': self.folder_entry.text(),
            'folder_per_url': self.folder_per_url_check.isChecked(),
            'is_playlist_url': is_playlist(query),
            'is_album_url': is_album(query),
            'preload': self.preload_check.isChecked(),
            'sponsor_block': self.sponsor_block_check.isChecked(),
            'skip_explicit': self.skip_explicit_check.isChecked(),
            'generate_lrc': self.generate_lrc_check.isChecked(),
            'playlist_numbering': self.playlist_numbering_check.isChecked()
        }

        timestamp = datetime.now().strftime("%H:%M:%S")
        queue_id = str(hash(query + timestamp))
        content_type = self.get_content_type(query)

        metadata = {'name': 'Loading...', 'artist': 'Fetching...', 'type': content_type}
        self.create_card_signal.emit(queue_id, metadata)

        queue_item = QueueItem(queue_id=queue_id, query=query, status='pending',
                               settings=settings, metadata=metadata, progress=0,
                               created_at=datetime.now())

        self.queue_manager.add_to_queue(queue_item)

        icons = {"playlist": "📃", "album": "💿", "track": "🎵"}
        self.log_to_queue(f"[{timestamp}] {icons.get(content_type, '📥')} Added: {query[:50]}...\n")

        self.url_entry.clear()

        if self.auto_download_check.isChecked() and not self.queue_manager.running:
            self.queue_manager.start_worker()

        self.update_queue_status()

    def start_queue(self):
        if not self.queue_manager.running:
            self.queue_manager.start_worker()
            self.log_to_queue("▶ Queue started\n")
        elif self.queue_manager.paused:
            self.queue_manager.resume_queue()
            self.log_to_queue("▶ Queue resumed\n")
        self.update_queue_status()

    def pause_queue(self):
        if self.queue_manager.running and not self.queue_manager.paused:
            self.queue_manager.pause_queue()
            self.log_to_queue("⏸ Queue paused\n")
        self.update_queue_status()

    def on_auto_download_changed(self, state):
        enabled = state == Qt.Checked.value or state == Qt.Checked
        self.log_to_queue(f"{'🔄 Auto-download enabled' if enabled else '⏹ Auto-download disabled'}\n")
        self.update_queue_status()

    def clear_completed_items(self):
        with self.queue_manager.lock:
            completed = [i.queue_id for i in self.queue_manager.queue if i.is_finished()]
        for qid in completed:
            self.remove_queue_card(qid)
        self.queue_manager.clear_completed()
        self.update_queue_status()

    def update_queue_status(self):
        if not hasattr(self, 'queue_manager'):
            return

        summary = self.queue_manager.get_queue_summary()
        pending, downloading, completed, failed = summary['pending'], summary['downloading'], summary['completed'], summary['failed']
        total = summary['total']

        if total == 0:
            self.queue_stats_label.setText("No jobs in queue")
        else:
            parts = []
            if pending: parts.append(f"{pending} pending")
            if downloading: parts.append(f"{downloading} active")
            if completed: parts.append(f"{completed} done")
            if failed: parts.append(f"{failed} failed")
            self.queue_stats_label.setText(" • ".join(parts))

        auto_mode = self.auto_download_check.isChecked()
        is_running = self.queue_manager.running
        is_paused = self.queue_manager.paused

        self.start_btn.setEnabled(pending > 0 and (not is_running or is_paused) and not auto_mode)
        self.pause_btn.setEnabled(is_running and not is_paused)

        if is_paused:
            self.queue_status_label.setText("Paused")
            self.queue_status_label.setStyleSheet("color: #FF9800;")
        elif downloading > 0:
            self.queue_status_label.setText("Downloading")
            self.queue_status_label.setStyleSheet("color: #4CAF50;")
        elif pending > 0:
            self.queue_status_label.setText("Processing" if is_running else "Waiting")
            self.queue_status_label.setStyleSheet("color: #2196F3;" if is_running else "color: #666;")
        else:
            self.queue_status_label.setText("Ready")
            self.queue_status_label.setStyleSheet("color: #666;")

        if self.auto_clear_queue_check.isChecked():
            with self.queue_manager.lock:
                for item in self.queue_manager.queue:
                    if item.is_finished() and item.queue_id not in self.auto_clear_timers:
                        timer = QTimer()
                        timer.setSingleShot(True)
                        qid = item.queue_id
                        timer.timeout.connect(lambda q=qid: self.remove_queue_item_by_id(q))
                        self.auto_clear_timers[item.queue_id] = timer
                        timer.start(5000)

    def remove_queue_item_by_id(self, queue_id):
        self.remove_queue_card(queue_id)
        with self.queue_manager.lock:
            self.queue_manager.queue = [i for i in self.queue_manager.queue if i.queue_id != queue_id]
        if queue_id in self.auto_clear_timers:
            self.auto_clear_timers[queue_id].stop()
            del self.auto_clear_timers[queue_id]
        self.update_queue_status()

    # =========================================================================
    # DOWNLOAD EXECUTION
    # =========================================================================

    def prepare_and_download(self, queue_id, query, format_val, bitrate_val, threads_val,
                            template_val, download_folder, folder_per_url,
                            is_playlist_url, is_album_url, preload, sponsor_block,
                            skip_explicit, generate_lrc, playlist_numbering):
        """Prepare and execute download using DownloadController"""
        settings = {
            'format': format_val,
            'bitrate': bitrate_val,
            'threads': threads_val,
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

        callbacks = {
            'log': self.log_to_queue,
            'update_metadata': lambda qid, meta: self.update_metadata_signal.emit(qid, meta),
            'update_progress': lambda qid, pct: self.update_progress_signal.emit(qid, pct),
            'update_song_count': lambda qid, cur, tot: self.update_song_count_signal.emit(qid, cur, tot),
            'update_current_song': lambda qid, song: self.update_current_song_signal.emit(qid, song),
            'on_complete': self._on_download_complete,
            'on_error': self._on_download_error
        }

        self.download_controller.prepare_and_download(queue_id, query, settings, callbacks)

    def _on_download_complete(self, queue_id):
        """Handle successful download completion"""
        card = self.queue_panel.get_queue_card(queue_id)
        if card:
            card.mark_complete()

    def _on_download_error(self, queue_id):
        """Handle download error"""
        card = self.queue_panel.get_queue_card(queue_id)
        if card:
            card.mark_failed()

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def log_to_queue(self, msg):
        self.queue_panel.log(msg)


    def paste_url(self):
        if text := QApplication.clipboard().text():
            self.url_entry.setText(text)

    def copy_command(self):
        if self.command_entry.text():
            QApplication.clipboard().setText(self.command_entry.text())

    def browse_folder(self):
        if folder := QFileDialog.getExistingDirectory(self, "Select Folder"):
            self.folder_entry.setText(folder)

    def open_download_folder(self):
        folder = self.folder_entry.text()
        if os.path.exists(folder):
            if sys.platform == "win32": os.startfile(folder)
            elif sys.platform == "darwin": subprocess.run(["open", folder])
            else: subprocess.run(["xdg-open", folder])

    def update_command_preview(self):
        query = self.url_entry.text().strip()
        if not query:
            self.command_entry.clear()
            return
        template = self.playlist_template_entry.text() if is_playlist(query) else self.template_entry.text()
        preview = self.download_controller.build_command_preview(
            query,
            self.format_combo.currentText(),
            self.bitrate_combo.currentText(),
            template
        )
        self.command_entry.setText(preview)

    def toggle_clipboard_monitoring(self, state):
        enabled = state == Qt.Checked.value or state == Qt.Checked
        if enabled:
            self.clipboard_monitor.enable()
        else:
            self.clipboard_monitor.disable()

    def _on_clipboard_url_detected(self, url):
        """Handle URL detected from clipboard"""
        self.url_entry.setText(url)
        self.log_to_queue(f"📋 Link detected: {url[:50]}...\n")
        self.flash_taskbar()

    def get_spotify_metadata(self, url):
        try: return get_metadata_handler().get_metadata(url)
        except: return None


    def check_spotdl_installation(self):
        try:
            result = subprocess.run(["spotdl", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.spotdl_status_label.setText(f"✅ {result.stdout.strip()}")
                self.spotdl_status_label.setStyleSheet("color: #4CAF50;")
                self.version_label.setText(result.stdout.strip())
            else:
                self.spotdl_status_label.setText("❌ Not working")
                self.spotdl_status_label.setStyleSheet("color: #F44336;")
        except:
            self.spotdl_status_label.setText("❌ Not installed")
            self.spotdl_status_label.setStyleSheet("color: #F44336;")

    def install_spotdl(self):
        def run():
            subprocess.run([sys.executable, "-m", "pip", "install", "spotdl"])
            QTimer.singleShot(0, self.check_spotdl_installation)
        threading.Thread(target=run, daemon=True).start()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SpotDL GUI")
    window = SpotDLGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
