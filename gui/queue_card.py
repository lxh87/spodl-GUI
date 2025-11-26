"""
Queue Card Widget Module
Individual queue card widget for displaying download progress
"""

from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from typing import Dict, Any, Optional


class QueueCard(QFrame):
    """
    Widget representing a single download in the queue
    Displays album art, metadata, progress, and status
    """

    def __init__(self, queue_id: str, metadata: Dict[str, Any],
                 network_manager: QNetworkAccessManager, parent=None):
        """
        Initialize queue card

        Args:
            queue_id: Unique identifier for this queue item
            metadata: Dictionary with name, artist, image_url
            network_manager: Shared network manager for loading images
            parent: Parent widget
        """
        super().__init__(parent)
        self.queue_id = queue_id
        self.network_manager = network_manager
        self.total_songs = 0
        self.completed_songs = 0

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
        self.setFixedHeight(62)

        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 4, 8, 4)

        # Album art
        self.art_label = QLabel()
        self.art_label.setFixedSize(52, 52)
        self.art_label.setStyleSheet("background-color: #1a1a1a; border-radius: 3px;")
        self.art_label.setAlignment(Qt.AlignCenter)
        self.art_label.setScaledContents(True)
        self.art_label.setText("🎵")
        self.art_label.setFont(QFont("", 16))
        layout.addWidget(self.art_label)

        # Info section
        info = QWidget()
        info.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info)
        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(metadata.get('name', 'Loading...'))
        self.title_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #FFF;")
        info_layout.addWidget(self.title_label)

        self.artist_label = QLabel(metadata.get('artist', 'Fetching...'))
        self.artist_label.setStyleSheet("font-size: 9px; color: #888;")
        info_layout.addWidget(self.artist_label)

        self.song_label = QLabel("⏳ Waiting...")
        self.song_label.setStyleSheet("font-size: 8px; color: #555;")
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
        self.count_label.setStyleSheet("font-size: 9px; color: #BBB; font-weight: bold;")
        progress_layout.addWidget(self.count_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 2px; background: #1a1a1a; }
            QProgressBar::chunk { background: #4CAF50; border-radius: 2px; }
        """)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Pending")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 7px; color: #555;")
        progress_layout.addWidget(self.status_label)

        layout.addWidget(progress)

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
                scaled = pixmap.scaled(52, 52, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                if scaled.width() > 52 or scaled.height() > 52:
                    x = (scaled.width() - 52) // 2
                    y = (scaled.height() - 52) // 2
                    scaled = scaled.copy(x, y, 52, 52)
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

    def update_progress(self, progress: int):
        """
        Update progress bar

        Args:
            progress: Progress percentage (0-100)
        """
        self.progress_bar.setValue(int(progress))
        if progress < 100:
            self.status_label.setText("Downloading")
            self.status_label.setStyleSheet("font-size: 7px; color: #4CAF50;")
        else:
            self.status_label.setText("Complete ✓")
            self.status_label.setStyleSheet("font-size: 7px; color: #4CAF50; font-weight: bold;")

    def update_current_song(self, song_name: str):
        """
        Update currently downloading song

        Args:
            song_name: Name of the song being downloaded
        """
        display = song_name[:28] + "..." if len(song_name) > 28 else song_name
        self.song_label.setText(f"🎵 {display}")
        self.song_label.setStyleSheet("font-size: 8px; color: #4CAF50;")

        # Increment completed count
        self.completed_songs += 1
        if self.total_songs > 0:
            progress = int((self.completed_songs / self.total_songs) * 100)
            self.progress_bar.setValue(progress)
            self.count_label.setText(f"{self.completed_songs}/{self.total_songs}")

    def update_song_count(self, completed: int, total: int):
        """
        Update song count display

        Args:
            completed: Number of completed songs
            total: Total number of songs
        """
        self.total_songs = total
        self.completed_songs = completed
        self.count_label.setText(f"{completed}/{total}")
        self.song_label.setText("🔍 Scanning...")
        self.song_label.setStyleSheet("font-size: 8px; color: #2196F3;")
        self.status_label.setText("Starting")
        self.status_label.setStyleSheet("font-size: 7px; color: #2196F3;")

    def mark_complete(self):
        """Mark download as complete"""
        self.song_label.setText("✅ Done!")
        self.song_label.setStyleSheet("font-size: 8px; color: #4CAF50; font-weight: bold;")

    def mark_failed(self):
        """Mark download as failed"""
        self.song_label.setText("❌ Failed")
        self.song_label.setStyleSheet("font-size: 8px; color: #F44336;")
        self.status_label.setText("Failed")
        self.status_label.setStyleSheet("font-size: 7px; color: #F44336;")
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: none; background: #1a1a1a; } "
            "QProgressBar::chunk { background: #F44336; }"
        )
