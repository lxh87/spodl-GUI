"""
Queue Card Widget Module
Individual queue card widget for displaying download progress
"""

from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from typing import Dict, Any, Optional


class QueueCard(QFrame):
    """
    Widget representing a single download in the queue
    Displays album art, metadata, progress, and status
    """
    
    # Signal emitted when delete button is clicked
    delete_clicked = Signal(str)  # queue_id

    def __init__(self, queue_id: str, metadata: Dict[str, Any],
                 network_manager: QNetworkAccessManager, is_paused: bool = False, parent=None):
        """
        Initialize queue card

        Args:
            queue_id: Unique identifier for this queue item
            metadata: Dictionary with name, artist, image_url
            network_manager: Shared network manager for loading images
            is_paused: Whether the queue is currently paused
            parent: Parent widget
        """
        super().__init__(parent)
        self.queue_id = queue_id
        self.network_manager = network_manager
        self.total_songs = 0
        self.completed_songs = 0
        self.skipped_songs = 0
        self.is_downloading = False
        self.is_complete = False
        self.is_failed = False
        self._is_paused = is_paused

        self._setup_ui(metadata)

    def _setup_ui(self, metadata: Dict[str, Any]):
        """Setup the card UI"""
        self.setObjectName(f"card_{self.queue_id}")
        self.setStyleSheet("""
            QFrame {
                background-color: #282828;
                border: 1px solid #333;
                border-radius: 5px;
            }
            QFrame:hover { border-color: #4CAF50; }
        """)
        self.setFixedHeight(70)  # Increased from 62 for better visibility

        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 8, 5)

        # Album art
        self.art_label = QLabel()
        self.art_label.setFixedSize(60, 60)  # Increased from 52x52
        self.art_label.setStyleSheet("background-color: #1a1a1a; border-radius: 3px;")
        self.art_label.setAlignment(Qt.AlignCenter)
        self.art_label.setScaledContents(True)
        self.art_label.setText("🎵")
        self.art_label.setFont(QFont("", 18))  # Increased from 16
        layout.addWidget(self.art_label)

        # Info section
        info = QWidget()
        info.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info)
        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(metadata.get('name', 'Loading...'))
        self.title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #FFF;")  # Increased from 10px
        info_layout.addWidget(self.title_label)

        self.artist_label = QLabel(metadata.get('artist', 'Fetching...'))
        self.artist_label.setStyleSheet("font-size: 11px; color: #888;")  # Increased from 9px
        info_layout.addWidget(self.artist_label)

        # Initial status based on pause state
        if self._is_paused:
            self.song_label = QLabel("⏸ Queue paused - Press ▶ Start")
            self.song_label.setStyleSheet("font-size: 10px; color: #FF9800;")
        else:
            self.song_label = QLabel("⏳ In queue...")
            self.song_label.setStyleSheet("font-size: 10px; color: #555;")
        info_layout.addWidget(self.song_label)

        layout.addWidget(info, 1)

        # Progress section
        progress = QWidget()
        progress.setFixedWidth(65)
        progress.setStyleSheet("background: transparent;")
        progress_layout = QVBoxLayout(progress)
        progress_layout.setSpacing(1)
        progress_layout.setContentsMargins(0, 3, 0, 3)

        self.count_label = QLabel("—")
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet("font-size: 11px; color: #BBB; font-weight: bold;")  # Increased from 9px
        progress_layout.addWidget(self.count_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)  # Increased from 4 for better visibility
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 3px; background: #1a1a1a; }
            QProgressBar::chunk { background: #4CAF50; border-radius: 3px; }
        """)
        progress_layout.addWidget(self.progress_bar)

        # Initial status based on pause state  
        if self._is_paused:
            self.status_label = QLabel("Paused")
            self.status_label.setStyleSheet("font-size: 9px; color: #FF9800;")
        else:
            self.status_label = QLabel("Queued")
            self.status_label.setStyleSheet("font-size: 9px; color: #555;")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)

        layout.addWidget(progress)

        # Delete button - full height
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedWidth(28)
        self.delete_btn.setSizePolicy(self.delete_btn.sizePolicy().horizontalPolicy(), 
                                       self.delete_btn.sizePolicy().verticalPolicy())
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #888;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-height: 44px;
            }
            QPushButton:hover {
                color: #FFF;
                background-color: #F44336;
            }
        """)
        self.delete_btn.setToolTip("Remove from queue")
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.queue_id))
        layout.addWidget(self.delete_btn)

        # Load image if available
        if metadata.get('image_url'):
            self.load_image(metadata['image_url'])

    def load_image(self, url: str):
        """
        Load album art image asynchronously

        Args:
            url: Image URL to load
        """
        reply = self.network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._on_image_loaded(reply))

    def _on_image_loaded(self, reply):
        """Handle image download completion"""
        if reply.error() == reply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                # Center-crop to square
                scaled = pixmap.scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)  # Increased from 52x52
                if scaled.width() > 60 or scaled.height() > 60:
                    x = (scaled.width() - 60) // 2
                    y = (scaled.height() - 60) // 2
                    scaled = scaled.copy(x, y, 60, 60)
                self.art_label.setPixmap(scaled)
                self.art_label.setText("")
        reply.deleteLater()

    def update_metadata(self, metadata: Dict[str, Any]):
        """
        Update card metadata

        Args:
            metadata: Dictionary with name, artist, image_url
        """
        self.title_label.setText(metadata.get('name', 'Unknown'))
        self.artist_label.setText(metadata.get('artist', 'Unknown'))
        if metadata.get('image_url'):
            self.load_image(metadata['image_url'])

    def set_paused_state(self, is_paused: bool):
        """
        Update card display based on queue paused state
        Only affects pending items, not active downloads
        
        Args:
            is_paused: Whether the queue is paused
        """
        self._is_paused = is_paused
        
        # Only update if not already downloading or finished
        if not self.is_downloading and not self.is_complete and not self.is_failed:
            if is_paused:
                self.song_label.setText("⏸ Queue paused - Press ▶ Start")
                self.song_label.setStyleSheet("font-size: 10px; color: #FF9800;")
                self.status_label.setText("Paused")
                self.status_label.setStyleSheet("font-size: 9px; color: #FF9800;")
            else:
                self.song_label.setText("⏳ In queue...")
                self.song_label.setStyleSheet("font-size: 10px; color: #555;")
                self.status_label.setText("Queued")
                self.status_label.setStyleSheet("font-size: 9px; color: #555;")

    def update_progress(self, progress: int):
        """
        Update progress bar

        Args:
            progress: Progress percentage (0-100)
        """
        self.is_downloading = True
        self.progress_bar.setValue(int(progress))
        if progress < 100:
            self.status_label.setText("Downloading")
            self.status_label.setStyleSheet("font-size: 9px; color: #4CAF50;")
        else:
            self.status_label.setText("Complete ✓")
            self.status_label.setStyleSheet("font-size: 9px; color: #4CAF50; font-weight: bold;")

    def update_current_song(self, song_name: str):
        """
        Update currently downloading song

        Args:
            song_name: Name of the song being downloaded
        """
        self.is_downloading = True
        display = song_name[:28] + "..." if len(song_name) > 28 else song_name
        self.song_label.setText(f"🎵 {display}")
        self.song_label.setStyleSheet("font-size: 10px; color: #4CAF50;")

        # Increment completed count
        self.completed_songs += 1
        self._update_count_display()

    def update_skipped_song(self, song_name: str):
        """
        Update when a song is skipped (already exists)

        Args:
            song_name: Name of the song that was skipped
        """
        self.is_downloading = True
        display = song_name[:25] + "..." if len(song_name) > 25 else song_name
        self.song_label.setText(f"⏭️ {display}")
        self.song_label.setStyleSheet("font-size: 10px; color: #FF9800;")
        self.status_label.setText("Skipping")
        self.status_label.setStyleSheet("font-size: 9px; color: #FF9800;")

        # Increment both skipped and completed counts
        self.skipped_songs += 1
        self.completed_songs += 1
        self._update_count_display()

    def _update_count_display(self):
        """Update the count label and progress bar"""
        if self.total_songs > 0:
            progress = int((self.completed_songs / self.total_songs) * 100)
            self.progress_bar.setValue(progress)
            
            # Show skipped count if any
            if self.skipped_songs > 0:
                self.count_label.setText(f"{self.completed_songs}/{self.total_songs}")
                self.count_label.setToolTip(f"{self.skipped_songs} skipped (already exist)")
            else:
                self.count_label.setText(f"{self.completed_songs}/{self.total_songs}")

    def update_song_count(self, completed: int, total: int):
        """
        Update song count display

        Args:
            completed: Number of completed songs
            total: Total number of songs
        """
        self.is_downloading = True
        self.total_songs = total
        self.completed_songs = completed
        self.count_label.setText(f"{completed}/{total}")
        self.song_label.setText("🔍 Scanning...")
        self.song_label.setStyleSheet("font-size: 10px; color: #2196F3;")
        self.status_label.setText("Starting")
        self.status_label.setStyleSheet("font-size: 9px; color: #2196F3;")

    def mark_complete(self):
        """Mark download as complete"""
        self.is_complete = True
        self.is_downloading = False
        self.progress_bar.setValue(100)
        
        # Check if all songs were skipped
        if self.skipped_songs > 0 and self.skipped_songs == self.total_songs:
            self.song_label.setText("⏭️ All skipped (already exist)")
            self.song_label.setStyleSheet("font-size: 10px; color: #FF9800; font-weight: bold;")
            self.status_label.setText("Skipped ✓")
            self.status_label.setStyleSheet("font-size: 9px; color: #FF9800; font-weight: bold;")
            self.progress_bar.setStyleSheet("""
                QProgressBar { border: none; border-radius: 3px; background: #1a1a1a; }
                QProgressBar::chunk { background: #FF9800; border-radius: 3px; }
            """)
        elif self.skipped_songs > 0:
            self.song_label.setText(f"✅ Done ({self.skipped_songs} skipped)")
            self.song_label.setStyleSheet("font-size: 10px; color: #4CAF50; font-weight: bold;")
            self.status_label.setText("Complete ✓")
            self.status_label.setStyleSheet("font-size: 9px; color: #4CAF50; font-weight: bold;")
        else:
            self.song_label.setText("✅ Done!")
            self.song_label.setStyleSheet("font-size: 10px; color: #4CAF50; font-weight: bold;")
            self.status_label.setText("Complete ✓")
            self.status_label.setStyleSheet("font-size: 9px; color: #4CAF50; font-weight: bold;")

    def mark_failed(self):
        """Mark download as failed"""
        self.is_failed = True
        self.is_downloading = False
        self.song_label.setText("❌ Failed")
        self.song_label.setStyleSheet("font-size: 10px; color: #F44336;")
        self.status_label.setText("Failed")
        self.status_label.setStyleSheet("font-size: 9px; color: #F44336;")
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: none; background: #1a1a1a; } "
            "QProgressBar::chunk { background: #F44336; }"
        )
