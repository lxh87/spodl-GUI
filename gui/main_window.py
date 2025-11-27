"""
Main Window Module
Primary application window integrating all panels and managing application state
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTabWidget, QSplitter, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

# Import queue management
from core.queue_item import QueueItem
from core.queue_manager import DownloadQueueManager

# Import GUI modules
from gui.utils import ClipboardMonitor, is_playlist, is_album
from gui.theme import get_dark_theme_stylesheet
from gui.config import ConfigManager
from gui.controller import DownloadController
from gui.download_panel import DownloadPanel
from gui.queue_panel import QueuePanel
from gui.settings_panel import SettingsPanel
from gui.queue_card import QueueCard

# Lazy import metadata handler
_metadata_handler = None


def get_metadata_handler():
    """Lazy load metadata handler"""
    global _metadata_handler
    if _metadata_handler is None:
        from core.metadata_handler import SpotifyMetadataHandler
        _metadata_handler = SpotifyMetadataHandler()
    return _metadata_handler


class MainWindow(QMainWindow):
    """
    Main application window
    Integrates download panel, queue panel, and settings panel
    """

    # Qt Signals for thread-safe GUI updates
    create_card_signal = Signal(str, dict, bool)  # queue_id, metadata, is_paused
    update_metadata_signal = Signal(str, dict)
    update_progress_signal = Signal(str, int)
    update_current_song_signal = Signal(str, str)
    update_skipped_song_signal = Signal(str, str)  # queue_id, song_name
    update_song_count_signal = Signal(str, int, int)

    def __init__(self):
        super().__init__()

        # Initialize config and settings
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.settings

        # Setup window
        self.setWindowTitle("SpotDL GUI")
        self.resize(1400, 900)
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(get_dark_theme_stylesheet())

        # Initialize components
        self.clipboard_monitor = ClipboardMonitor()
        self.download_controller = DownloadController(self._get_spotify_metadata)
        self.queue_manager = DownloadQueueManager(self)
        self.auto_clear_timers = {}

        # Setup UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

        # Start timers
        self.queue_status_timer = QTimer()
        self.queue_status_timer.timeout.connect(self._update_queue_status)
        self.queue_status_timer.start(2000)

        # Check SpotDL
        QTimer.singleShot(100, self._check_spotdl)

    def _setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Tab widget
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

        # Create tabs
        self._create_main_tab()
        self._create_settings_tab()

    def _create_sidebar(self):
        """Create compact sidebar"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(120)
        self.sidebar.setStyleSheet("background-color: #202020;")

        layout = QVBoxLayout(self.sidebar)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 14, 10, 14)

        # Logo
        logo_label = QLabel("🎵 SpotDL")
        logo_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        self.version_label = QLabel("v4.4.3")
        self.version_label.setStyleSheet("color: #555; font-size: 8pt;")
        self.version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.version_label)

        layout.addStretch()
        
        # Note: Music folder button moved to queue panel

    def _create_main_tab(self):
        """Create main downloads tab"""
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Horizontal splitter for left/right panels
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        # Download panel (left) - removed maxWidth to allow more splitter range
        self.download_panel = DownloadPanel(self.settings)
        self.download_panel.setMinimumWidth(260)
        # No max width - allows splitter to go further right
        self.main_splitter.addWidget(self.download_panel)

        # Queue panel (right)
        self.queue_panel = QueuePanel(
            auto_download=self.settings.get("auto_download", True),
            auto_clear=self.settings.get("auto_clear_completed", False)
        )
        self.queue_panel.setMinimumWidth(400)
        self.main_splitter.addWidget(self.queue_panel)

        self.main_splitter.setSizes([340, 860])
        main_layout.addWidget(self.main_splitter)

        self.tab_widget.addTab(main_widget, "🎵 Downloads")

    def _create_settings_tab(self):
        """Create settings tab"""
        self.settings_panel = SettingsPanel(self.settings)
        self.tab_widget.addTab(self.settings_panel, "⚙️ Settings")

    def _connect_signals(self):
        """Connect all panel signals to handlers"""
        # Download panel signals
        self.download_panel.add_job_clicked.connect(self._add_to_queue)
        self.download_panel.clipboard_monitoring_changed.connect(self._toggle_clipboard_monitoring)
        self.download_panel.settings_changed.connect(self._update_command_preview)

        # Queue panel signals
        self.queue_panel.start_queue_clicked.connect(self._start_queue)
        self.queue_panel.pause_queue_clicked.connect(self._pause_queue)
        self.queue_panel.clear_completed_clicked.connect(self._clear_completed_items)
        self.queue_panel.auto_download_changed.connect(self._on_auto_download_changed)
        self.queue_panel.open_folder_clicked.connect(self._open_download_folder)
        self.queue_panel.delete_job_clicked.connect(self._delete_queue_item)

        # Settings panel signals
        self.settings_panel.save_settings_clicked.connect(self._save_settings)

        # Clipboard monitor
        self.clipboard_monitor.url_detected.connect(self._on_clipboard_url_detected)

        # Queue card signals
        self.create_card_signal.connect(self._create_queue_card_wrapper)
        self.update_metadata_signal.connect(self._update_metadata_wrapper)
        self.update_progress_signal.connect(self._update_progress_wrapper)
        self.update_current_song_signal.connect(self._update_current_song_wrapper)
        self.update_skipped_song_signal.connect(self._update_skipped_song_wrapper)
        self.update_song_count_signal.connect(self._update_song_count_wrapper)

        # Enable clipboard monitoring by default
        self.download_panel.set_clipboard_monitoring_enabled(True)
        self.clipboard_monitor.enable()

    # =========================================================================
    # QUEUE MANAGEMENT
    # =========================================================================

    def _add_to_queue(self, query: str, panel_settings: dict):
        """Add new job to queue"""
        if not query:
            QMessageBox.warning(self, "No URL", "Please enter a URL")
            return

        # Merge panel settings with global settings
        settings = {
            'format': panel_settings['format'],
            'bitrate': panel_settings['bitrate'],
            'threads': int(self.settings_panel.get_threads()),
            'template': (self.settings_panel.get_playlist_template() if is_playlist(query)
                        else self.settings_panel.get_song_template()),
            'download_folder': self.settings_panel.get_download_folder(),
            'folder_per_url': panel_settings['folder_per_url'],
            'is_playlist_url': is_playlist(query),
            'is_album_url': is_album(query),
            'preload': panel_settings['preload'],
            'sponsor_block': panel_settings['sponsor_block'],
            'skip_explicit': panel_settings['skip_explicit'],
            'generate_lrc': panel_settings['generate_lrc'],
            'playlist_numbering': panel_settings['playlist_numbering']
        }

        timestamp = datetime.now().strftime("%H:%M:%S")
        queue_id = str(hash(query + timestamp))
        content_type = self._get_content_type(query)

        # Determine if queue is paused for initial card state
        is_paused = self.queue_manager.paused or not self.queue_panel.is_auto_download_enabled()

        metadata = {'name': 'Loading...', 'artist': 'Fetching...', 'type': content_type}
        self.create_card_signal.emit(queue_id, metadata, is_paused)

        queue_item = QueueItem(
            queue_id=queue_id, query=query, status='pending',
            settings=settings, metadata=metadata, progress=0,
            created_at=datetime.now()
        )

        self.queue_manager.add_to_queue(queue_item)

        icons = {"playlist": "📃", "album": "💿", "track": "🎵"}
        self.queue_panel.log(f"[{timestamp}] {icons.get(content_type, '📥')} Added: {query[:50]}...\n")

        if self.queue_panel.is_auto_download_enabled() and not self.queue_manager.running:
            self.queue_manager.start_worker()

        self._update_queue_status()

    def _start_queue(self):
        """Start or resume queue"""
        if not self.queue_manager.running:
            self.queue_manager.start_worker()
            self.queue_panel.log("▶ Queue started\n")
        elif self.queue_manager.paused:
            self.queue_manager.resume_queue()
            self.queue_panel.log("▶ Queue resumed\n")
        
        # Update all cards to show they're no longer paused
        self.queue_panel.update_all_cards_paused_state(False)
        self._update_queue_status()

    def _pause_queue(self):
        """Pause queue"""
        if self.queue_manager.running and not self.queue_manager.paused:
            self.queue_manager.pause_queue()
            self.queue_panel.log("⏸ Queue paused\n")
            
            # Update all pending cards to show paused state
            self.queue_panel.update_all_cards_paused_state(True)
        self._update_queue_status()

    def _on_auto_download_changed(self, enabled: bool):
        """Handle auto-download toggle"""
        self.queue_panel.log(f"{'🔄 Auto-download enabled' if enabled else '⏹ Auto-download disabled'}\n")
        
        # If auto-download is disabled, show paused state on pending cards
        if not enabled:
            self.queue_panel.update_all_cards_paused_state(True)
        elif not self.queue_manager.paused:
            self.queue_panel.update_all_cards_paused_state(False)
            
        self._update_queue_status()

    def _clear_completed_items(self):
        """Clear completed items from queue"""
        with self.queue_manager.lock:
            completed = [i.queue_id for i in self.queue_manager.queue if i.is_finished()]
        for qid in completed:
            self.queue_panel.remove_queue_card(qid)
        self.queue_manager.clear_completed()
        self._update_queue_status()

    def _update_queue_status(self):
        """Update queue status display"""
        if not hasattr(self, 'queue_manager'):
            return

        summary = self.queue_manager.get_queue_summary()
        pending, downloading, completed, failed = (
            summary['pending'], summary['downloading'],
            summary['completed'], summary['failed']
        )
        total = summary['total']

        # Update stats
        if total == 0:
            self.queue_panel.update_stats("No jobs in queue")
        else:
            parts = []
            if pending: parts.append(f"{pending} pending")
            if downloading: parts.append(f"{downloading} active")
            if completed: parts.append(f"{completed} done")
            if failed: parts.append(f"{failed} failed")
            self.queue_panel.update_stats(" • ".join(parts))

        # Update button states
        auto_mode = self.queue_panel.is_auto_download_enabled()
        is_running = self.queue_manager.running
        is_paused = self.queue_manager.paused

        self.queue_panel.set_start_enabled(pending > 0 and (not is_running or is_paused) and not auto_mode)
        self.queue_panel.set_pause_enabled(is_running and not is_paused)

        # Update status label
        if is_paused:
            self.queue_panel.update_status("Paused", "#FF9800")
        elif downloading > 0:
            self.queue_panel.update_status("Downloading", "#4CAF50")
        elif pending > 0:
            status = "Processing" if is_running else "Waiting"
            color = "#2196F3" if is_running else "#666"
            self.queue_panel.update_status(status, color)
        else:
            self.queue_panel.update_status("Ready", "#666")

        # Auto-clear completed items
        if self.queue_panel.is_auto_clear_enabled():
            with self.queue_manager.lock:
                for item in self.queue_manager.queue:
                    if item.is_finished() and item.queue_id not in self.auto_clear_timers:
                        timer = QTimer()
                        timer.setSingleShot(True)
                        qid = item.queue_id
                        timer.timeout.connect(lambda q=qid: self._remove_queue_item_by_id(q))
                        self.auto_clear_timers[item.queue_id] = timer
                        timer.start(5000)

    def _remove_queue_item_by_id(self, queue_id: str):
        """Remove queue item by ID"""
        self.queue_panel.remove_queue_card(queue_id)
        with self.queue_manager.lock:
            self.queue_manager.queue = [i for i in self.queue_manager.queue if i.queue_id != queue_id]
        if queue_id in self.auto_clear_timers:
            self.auto_clear_timers[queue_id].stop()
            del self.auto_clear_timers[queue_id]
        self._update_queue_status()

    def _delete_queue_item(self, queue_id: str):
        """Delete a queue item (from delete button click)"""
        # Try to cancel if it's downloading
        self.queue_manager.cancel_download(queue_id)
        # Remove from UI and queue
        self._remove_queue_item_by_id(queue_id)
        self.queue_panel.log(f"🗑️ Removed job from queue\n")

    # =========================================================================
    # QUEUE CARD WRAPPERS
    # =========================================================================

    def _create_queue_card_wrapper(self, queue_id: str, metadata: dict, is_paused: bool):
        """Wrapper to create queue card from signal"""
        self.queue_panel.add_queue_card(queue_id, metadata, is_paused)

    def _update_metadata_wrapper(self, queue_id: str, metadata: dict):
        """Wrapper to update card metadata from signal"""
        card = self.queue_panel.get_queue_card(queue_id)
        if card:
            card.update_metadata(metadata)

    def _update_progress_wrapper(self, queue_id: str, progress: int):
        """Wrapper to update card progress from signal"""
        card = self.queue_panel.get_queue_card(queue_id)
        if card:
            card.update_progress(progress)

    def _update_current_song_wrapper(self, queue_id: str, song: str):
        """Wrapper to update current song from signal"""
        card = self.queue_panel.get_queue_card(queue_id)
        if card:
            card.update_current_song(song)

    def _update_skipped_song_wrapper(self, queue_id: str, song: str):
        """Wrapper to update skipped song from signal"""
        card = self.queue_panel.get_queue_card(queue_id)
        if card:
            card.update_skipped_song(song)

    def _update_song_count_wrapper(self, queue_id: str, completed: int, total: int):
        """Wrapper to update song count from signal"""
        card = self.queue_panel.get_queue_card(queue_id)
        if card:
            card.update_song_count(completed, total)

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
            'log': self.queue_panel.log,
            'update_metadata': lambda qid, meta: self.update_metadata_signal.emit(qid, meta),
            'update_progress': lambda qid, pct: self.update_progress_signal.emit(qid, pct),
            'update_song_count': lambda qid, cur, tot: self.update_song_count_signal.emit(qid, cur, tot),
            'update_current_song': lambda qid, song: self.update_current_song_signal.emit(qid, song),
            'update_skipped_song': lambda qid, song: self.update_skipped_song_signal.emit(qid, song),
            'on_complete': self._on_download_complete,
            'on_error': self._on_download_error
        }

        self.download_controller.prepare_and_download(queue_id, query, settings, callbacks)

    def _on_download_complete(self, queue_id: str):
        """Handle successful download completion"""
        card = self.queue_panel.get_queue_card(queue_id)
        if card:
            card.mark_complete()

    def _on_download_error(self, queue_id: str):
        """Handle download error"""
        card = self.queue_panel.get_queue_card(queue_id)
        if card:
            card.mark_failed()

    # =========================================================================
    # QUEUE MANAGER COMPATIBILITY METHODS
    # =========================================================================

    def log_to_queue(self, message: str):
        """Log message to queue (compatibility method for queue_manager)"""
        self.queue_panel.log(message)

    def update_queue_progress(self, queue_id: str, progress: int):
        """Update queue card progress (compatibility method for queue_manager)"""
        self.update_progress_signal.emit(queue_id, progress)

    def update_queue_card_metadata(self, queue_id: str, metadata: dict):
        """Update queue card metadata (compatibility method for queue_manager)"""
        self.update_metadata_signal.emit(queue_id, metadata)

    def remove_queue_card(self, queue_id: str):
        """Remove queue card (compatibility method for queue_manager)"""
        self.queue_panel.remove_queue_card(queue_id)

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def _update_command_preview(self):
        """Update command preview in download panel"""
        query = self.download_panel.get_url()
        if not query:
            self.download_panel.update_command_preview("")
            return

        template = (self.settings_panel.get_playlist_template() if is_playlist(query)
                   else self.settings_panel.get_song_template())
        settings = self.download_panel.get_settings()

        preview = self.download_controller.build_command_preview(
            query,
            settings['format'],
            settings['bitrate'],
            template
        )
        self.download_panel.update_command_preview(preview)

    def _toggle_clipboard_monitoring(self, enabled: bool):
        """Toggle clipboard monitoring"""
        if enabled:
            self.clipboard_monitor.enable()
        else:
            self.clipboard_monitor.disable()

    def _on_clipboard_url_detected(self, url: str):
        """Handle URL detected from clipboard - auto-add to queue"""
        # Extra validation - make sure it's a clean URL
        url = url.strip()
        
        # Don't auto-add if URL looks suspicious (too long, contains error text, etc.)
        if len(url) > 250 or '\n' in url:
            return
            
        self.download_panel.set_url(url)
        self.queue_panel.log(f"📋 Link detected: {url[:50]}...\n")
        self._flash_taskbar()
        
        # Auto-add the job to queue
        settings = self.download_panel.get_settings()
        self._add_to_queue(url, settings)

    def _flash_taskbar(self):
        """Flash taskbar to get attention"""
        QApplication.alert(self, 3000)
        original_title = self.windowTitle()
        self.setWindowTitle("🔔 Link Detected! - SpotDL GUI")
        QTimer.singleShot(3000, lambda: self.setWindowTitle(original_title))

    def _get_content_type(self, query: str) -> str:
        """Determine content type from query"""
        if is_playlist(query):
            return "playlist"
        elif is_album(query):
            return "album"
        return "track"

    def _get_spotify_metadata(self, url: str):
        """Get Spotify metadata"""
        try:
            return get_metadata_handler().get_metadata(url)
        except:
            return None

    def _check_spotdl(self):
        """Check if SpotDL is installed"""
        try:
            result = subprocess.run(["spotdl", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.version_label.setText(version)
                self.settings_panel.update_version_display(version)
        except:
            QMessageBox.warning(self, "SpotDL Not Found",
                "SpotDL is not installed.\nInstall with: pip install spotdl")

    def _open_download_folder(self):
        """Open download folder in file explorer"""
        folder = self.settings_panel.get_download_folder()
        if os.path.exists(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])

    def _save_settings(self):
        """Save settings to config file"""
        try:
            panel_settings = self.download_panel.get_settings()
            settings_panel_data = self.settings_panel.get_settings()

            self.config_manager.update({
                "format": panel_settings['format'],
                "bitrate": panel_settings['bitrate'],
                "threads": settings_panel_data['threads'],
                "output": settings_panel_data['output'],
                "playlist_output": settings_panel_data['playlist_output'],
                "download_folder": settings_panel_data['download_folder'],
                "create_folder_per_url": panel_settings['folder_per_url'],
                "auto_download": self.queue_panel.is_auto_download_enabled(),
                "auto_clear_completed": self.queue_panel.is_auto_clear_enabled()
            })

            if self.config_manager.save_settings():
                self.queue_panel.log("✅ Settings saved\n")
            else:
                QMessageBox.critical(self, "Error", "Failed to save settings")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        self._save_settings()
        event.accept()
