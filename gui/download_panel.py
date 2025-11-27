"""
Download Panel Module
Left panel containing URL input, format options, and add job button
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QFrame, QApplication
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from typing import Dict, Any


class DownloadPanel(QWidget):
    """
    Panel for configuring and adding downloads to queue
    Contains URL input, format/bitrate selection, options, and command preview
    """

    # Signals
    add_job_clicked = Signal(str, dict)  # query, settings
    clipboard_monitoring_changed = Signal(bool)
    settings_changed = Signal()  # Emitted when any setting changes (no parameters)

    def __init__(self, settings: Dict[str, Any], parent=None):
        """
        Initialize download panel

        Args:
            settings: Dictionary of default settings
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings = settings
        self._setup_ui()

    def _setup_ui(self):
        """Setup the panel UI"""
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(self)
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
        self.clipboard_monitor_check.setToolTip("Automatically detect music URLs copied to clipboard")
        self.clipboard_monitor_check.stateChanged.connect(
            lambda state: self.clipboard_monitoring_changed.emit(
                state == 2  # Qt.Checked value
            )
        )
        url_header.addWidget(self.clipboard_monitor_check)
        url_layout.addLayout(url_header)

        # URL input with clear button
        url_row = QHBoxLayout()
        url_row.setSpacing(4)
        
        # Container for URL entry with embedded clear button
        url_container = QFrame()
        url_container.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #333;
                border-radius: 4px;
            }
            QFrame:focus-within {
                border: 1px solid #4CAF50;
            }
        """)
        url_container_layout = QHBoxLayout(url_container)
        url_container_layout.setContentsMargins(0, 0, 4, 0)
        url_container_layout.setSpacing(0)
        
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("Paste Spotify/YouTube URL...")
        self.url_entry.setToolTip("Enter Spotify/YouTube URL, search query, or special keywords (saved, all-user-playlists, all-user-followed-artists)")
        self.url_entry.setFixedHeight(28)
        self.url_entry.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 5px;
                padding-right: 0;
            }
        """)
        self.url_entry.textChanged.connect(lambda: self.settings_changed.emit())
        url_container_layout.addWidget(self.url_entry)
        
        # Clear button inside URL field
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(22, 22)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666;
                font-size: 12px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                color: #F44336;
                background-color: rgba(244, 67, 54, 0.1);
                border-radius: 11px;
            }
        """)
        self.clear_btn.setToolTip("Clear URL field")
        self.clear_btn.clicked.connect(self._clear_url)
        url_container_layout.addWidget(self.clear_btn)
        
        url_row.addWidget(url_container)

        paste_btn = QPushButton("📋")
        paste_btn.setFixedSize(28, 28)
        paste_btn.setStyleSheet("padding: 0; font-size: 11pt;")
        paste_btn.setToolTip("Paste URL from clipboard")
        paste_btn.clicked.connect(self._paste_url)
        url_row.addWidget(paste_btn)
        url_layout.addLayout(url_row)

        # Quick buttons
        quick_row = QHBoxLayout()
        quick_row.setSpacing(3)
        quick_label = QLabel("Quick:")
        quick_label.setStyleSheet("color: #666; font-size: 8pt;")
        quick_row.addWidget(quick_label)

        quick_tooltips = {
            "Liked": "Download all your liked/saved songs",
            "Playlists": "Download all your playlists",
            "Artists": "Download all songs from artists you follow"
        }
        for text, val in [("Liked", "saved"), ("Playlists", "all-user-playlists"),
                          ("Artists", "all-user-followed-artists")]:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #333; font-size: 8pt;
                    padding: 3px 6px; min-width: 40px;
                }
                QPushButton:hover { background-color: #444; }
            """)
            btn.setFixedHeight(22)
            btn.setToolTip(quick_tooltips[text])
            btn.clicked.connect(lambda checked, v=val: self.url_entry.setText(v))
            quick_row.addWidget(btn)
        quick_row.addStretch()
        url_layout.addLayout(quick_row)

        layout.addWidget(url_section)

        # Options Section
        options_section = QFrame()
        options_section.setStyleSheet("background-color: #252525; border-radius: 5px;")
        options_layout = QVBoxLayout(options_section)
        options_layout.setSpacing(5)
        options_layout.setContentsMargins(10, 8, 10, 8)

        options_label = QLabel("Options")
        options_label.setStyleSheet("font-weight: bold; font-size: 9pt;")
        options_layout.addWidget(options_label)

        # Format row
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
        self.format_combo.setToolTip("Audio format (mp3=most compatible, flac=lossless)")
        self.format_combo.setFixedHeight(26)
        self.format_combo.currentTextChanged.connect(lambda: self.settings_changed.emit())
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
        self.bitrate_combo.setToolTip("Audio quality (320k=highest, auto=match source)")
        self.bitrate_combo.setFixedHeight(26)
        self.bitrate_combo.currentTextChanged.connect(lambda: self.settings_changed.emit())
        br_box.addWidget(self.bitrate_combo)
        format_row.addLayout(br_box)

        options_layout.addLayout(format_row)

        # Checkboxes
        checks_grid = QGridLayout()
        checks_grid.setSpacing(2)
        checks_grid.setContentsMargins(0, 2, 0, 0)

        self.preload_check = QCheckBox("Preload URLs")
        self.preload_check.setToolTip("Preload metadata before downloading")
        self.sponsor_block_check = QCheckBox("Skip Sponsors")
        self.sponsor_block_check.setToolTip("Remove sponsor segments from music")
        self.skip_explicit_check = QCheckBox("Skip Explicit")
        self.skip_explicit_check.setToolTip("Skip songs marked as explicit")
        self.generate_lrc_check = QCheckBox("Generate LRC")
        self.generate_lrc_check.setToolTip("Generate synced lyrics file (.lrc)")
        self.playlist_numbering_check = QCheckBox("Playlist #")
        self.playlist_numbering_check.setToolTip("Add playlist position number to filename")
        self.folder_per_url_check = QCheckBox("Folder per URL")
        self.folder_per_url_check.setToolTip("Create separate folder for each playlist/album")
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

        # Command preview
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
        copy_btn.setToolTip("Copy command to clipboard")
        copy_btn.clicked.connect(self._copy_command)
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

        # Add Job Button
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
        self.add_job_btn.setToolTip("Add download to queue")
        self.add_job_btn.clicked.connect(self._on_add_job)
        layout.addWidget(self.add_job_btn)

    def _paste_url(self):
        """Paste URL from clipboard"""
        if text := QApplication.clipboard().text():
            self.url_entry.setText(text)

    def _clear_url(self):
        """Clear URL field"""
        self.url_entry.clear()

    def _copy_command(self):
        """Copy command to clipboard"""
        if self.command_entry.text():
            QApplication.clipboard().setText(self.command_entry.text())

    def _on_add_job(self):
        """Handle add job button click"""
        query = self.url_entry.text().strip()
        if query:
            settings = self.get_settings()
            self.add_job_clicked.emit(query, settings)

    def get_settings(self) -> Dict[str, Any]:
        """
        Get current settings from the panel

        Returns:
            Dictionary of settings
        """
        return {
            'format': self.format_combo.currentText(),
            'bitrate': self.bitrate_combo.currentText(),
            'preload': self.preload_check.isChecked(),
            'sponsor_block': self.sponsor_block_check.isChecked(),
            'skip_explicit': self.skip_explicit_check.isChecked(),
            'generate_lrc': self.generate_lrc_check.isChecked(),
            'playlist_numbering': self.playlist_numbering_check.isChecked(),
            'folder_per_url': self.folder_per_url_check.isChecked()
        }

    def get_url(self) -> str:
        """Get current URL from entry"""
        return self.url_entry.text().strip()

    def set_url(self, url: str):
        """Set URL in entry"""
        self.url_entry.setText(url)

    def update_command_preview(self, preview: str):
        """
        Update command preview display

        Args:
            preview: Command preview string
        """
        self.command_entry.setText(preview)

    def set_clipboard_monitoring_enabled(self, enabled: bool):
        """Set clipboard monitoring checkbox state"""
        self.clipboard_monitor_check.setChecked(enabled)
