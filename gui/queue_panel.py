"""
Queue Panel Module
Right panel containing queue controls, cards display, and output log
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QScrollArea, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtNetwork import QNetworkAccessManager
from typing import Dict, Any

from gui.utils import ThreadSafeLogger
from gui.queue_card import QueueCard


class QueuePanel(QWidget):
    """
    Panel for managing download queue
    Contains controls, queue card display, and output log
    """

    # Signals
    start_queue_clicked = Signal()
    pause_queue_clicked = Signal()
    clear_completed_clicked = Signal()
    auto_download_changed = Signal(bool)
    auto_clear_changed = Signal(bool)

    def __init__(self, auto_download: bool = True, auto_clear: bool = False, parent=None):
        """
        Initialize queue panel

        Args:
            auto_download: Initial state of auto-download checkbox
            auto_clear: Initial state of auto-clear checkbox
            parent: Parent widget
        """
        super().__init__(parent)
        self.queue_cards = {}
        self.network_manager = QNetworkAccessManager()
        self._setup_ui(auto_download, auto_clear)

    def _setup_ui(self, auto_download: bool, auto_clear: bool):
        """Setup the panel UI"""
        self.setStyleSheet("background-color: #1a1a1a;")

        layout = QVBoxLayout(self)
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

        # Controls frame
        controls_frame = QFrame()
        controls_frame.setStyleSheet("background-color: #252525; border-radius: 5px;")
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(4)
        controls_layout.setContentsMargins(8, 6, 8, 6)

        # Control buttons
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; font-size: 8pt; padding: 4px 8px; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #2b2b2b; color: #555; }
        """)
        self.start_btn.setFixedHeight(24)
        self.start_btn.setToolTip("Start processing downloads from queue")
        self.start_btn.clicked.connect(self.start_queue_clicked.emit)
        self.start_btn.setEnabled(False)
        controls_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setStyleSheet("""
            QPushButton { background-color: #FF9800; font-size: 8pt; padding: 4px 8px; }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:disabled { background-color: #2b2b2b; color: #555; }
        """)
        self.pause_btn.setFixedHeight(24)
        self.pause_btn.setToolTip("Pause current download")
        self.pause_btn.clicked.connect(self.pause_queue_clicked.emit)
        self.pause_btn.setEnabled(False)
        controls_layout.addWidget(self.pause_btn)

        self.clear_btn = QPushButton("🧹 Clear")
        self.clear_btn.setStyleSheet("""
            QPushButton { background-color: #424242; font-size: 8pt; padding: 4px 8px; }
            QPushButton:hover { background-color: #555; }
        """)
        self.clear_btn.setFixedHeight(24)
        self.clear_btn.setToolTip("Clear completed downloads from queue")
        self.clear_btn.clicked.connect(self.clear_completed_clicked.emit)
        controls_layout.addWidget(self.clear_btn)

        controls_layout.addStretch()

        # Checkboxes
        self.auto_download_check = QCheckBox("Auto-download")
        self.auto_download_check.setStyleSheet("font-size: 8pt;")
        self.auto_download_check.setToolTip("Automatically start downloads when added to queue")
        self.auto_download_check.setChecked(auto_download)
        self.auto_download_check.stateChanged.connect(
            lambda state: self.auto_download_changed.emit(state == Qt.Checked.value or state == Qt.Checked)
        )
        controls_layout.addWidget(self.auto_download_check)

        self.auto_clear_queue_check = QCheckBox("Auto-clear")
        self.auto_clear_queue_check.setStyleSheet("font-size: 8pt;")
        self.auto_clear_queue_check.setToolTip("Automatically remove completed downloads after 5 seconds")
        self.auto_clear_queue_check.setChecked(auto_clear)
        self.auto_clear_queue_check.stateChanged.connect(
            lambda state: self.auto_clear_changed.emit(state == Qt.Checked.value or state == Qt.Checked)
        )
        controls_layout.addWidget(self.auto_clear_queue_check)

        layout.addWidget(controls_frame)

        # Stats label
        self.queue_stats_label = QLabel("No jobs in queue")
        self.queue_stats_label.setStyleSheet("color: #555; font-size: 8pt; padding: 2px 0;")
        layout.addWidget(self.queue_stats_label)

        # Vertical splitter for queue cards and log
        self.queue_splitter = QSplitter(Qt.Vertical)
        self.queue_splitter.setChildrenCollapsible(False)

        # Queue cards area
        queue_container = QWidget()
        queue_container.setMinimumHeight(60)  # Reduced from 120 for more flexibility
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
        log_container.setMinimumHeight(40)  # Reduced from 80 for more flexibility
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
        clear_log_btn.clicked.connect(self.clear_log)
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

        # Create logger
        self.logger = ThreadSafeLogger(self.queue_textbox)

    def add_queue_card(self, queue_id: str, metadata: Dict[str, Any]) -> QueueCard:
        """
        Add a new queue card

        Args:
            queue_id: Unique identifier for the queue item
            metadata: Dictionary with name, artist, image_url

        Returns:
            Created QueueCard widget
        """
        card = QueueCard(queue_id, metadata, self.network_manager, self)
        self.queue_preview_layout.insertWidget(
            self.queue_preview_layout.count() - 1,
            card
        )
        self.queue_cards[queue_id] = card
        return card

    def remove_queue_card(self, queue_id: str):
        """
        Remove a queue card

        Args:
            queue_id: Queue item identifier
        """
        if queue_id in self.queue_cards:
            card = self.queue_cards[queue_id]
            self.queue_preview_layout.removeWidget(card)
            card.deleteLater()
            del self.queue_cards[queue_id]

    def get_queue_card(self, queue_id: str) -> QueueCard:
        """
        Get queue card by ID

        Args:
            queue_id: Queue item identifier

        Returns:
            QueueCard widget or None
        """
        return self.queue_cards.get(queue_id)

    def update_stats(self, stats_text: str):
        """
        Update queue statistics label

        Args:
            stats_text: Statistics text to display
        """
        self.queue_stats_label.setText(stats_text)

    def update_status(self, status_text: str, color: str = "#555"):
        """
        Update queue status label

        Args:
            status_text: Status text to display
            color: Text color
        """
        self.queue_status_label.setText(status_text)
        self.queue_status_label.setStyleSheet(f"color: {color}; font-size: 9pt; margin-left: 6px;")

    def set_start_enabled(self, enabled: bool):
        """Enable/disable start button"""
        self.start_btn.setEnabled(enabled)

    def set_pause_enabled(self, enabled: bool):
        """Enable/disable pause button"""
        self.pause_btn.setEnabled(enabled)

    def log(self, message: str):
        """
        Log message to output

        Args:
            message: Message to log
        """
        self.logger.log(message)

    def clear_log(self):
        """Clear the output log"""
        self.queue_textbox.clear()

    def is_auto_download_enabled(self) -> bool:
        """Check if auto-download is enabled"""
        return self.auto_download_check.isChecked()

    def is_auto_clear_enabled(self) -> bool:
        """Check if auto-clear is enabled"""
        return self.auto_clear_queue_check.isChecked()
