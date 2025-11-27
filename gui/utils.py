"""
GUI Utilities Module
Contains helper classes and functions for the SpotDL GUI
"""

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication


# =============================================================================
# THREAD-SAFE LOGGING
# =============================================================================

class ThreadSafeLogger(QObject):
    """Thread-safe logger using Qt signals"""
    log_signal = Signal(str)

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.log_signal.connect(self._append_text)

    def _append_text(self, text):
        self.text_widget.moveCursor(QTextCursor.End)
        self.text_widget.insertPlainText(text)
        self.text_widget.moveCursor(QTextCursor.End)

    def log(self, message):
        self.log_signal.emit(message)


# =============================================================================
# CLIPBOARD MONITORING
# =============================================================================

class ClipboardMonitor(QObject):
    """
    Monitors clipboard for valid music URLs
    Emits url_detected signal when a valid music URL is found
    """
    url_detected = Signal(str)

    def __init__(self):
        super().__init__()
        self.clipboard = QApplication.clipboard()
        self.last_clipboard_text = ""
        self.enabled = False
        self.connected = False

    def enable(self):
        """Enable clipboard monitoring"""
        self.enabled = True
        if not self.connected:
            self.last_clipboard_text = self.clipboard.text()
            self.clipboard.dataChanged.connect(self._check_clipboard)
            self.connected = True

    def disable(self):
        """Disable clipboard monitoring"""
        self.enabled = False
        if self.connected:
            try:
                self.clipboard.dataChanged.disconnect(self._check_clipboard)
            except:
                pass
            self.connected = False

    def _check_clipboard(self):
        """Check clipboard for valid music URLs"""
        if not self.enabled:
            return

        text = self.clipboard.text().strip()
        if text and text != self.last_clipboard_text:
            self.last_clipboard_text = text
            if is_valid_music_url(text):
                self.url_detected.emit(text)


# =============================================================================
# URL VALIDATION AND PARSING
# =============================================================================

def is_valid_music_url(url: str) -> bool:
    """
    Check if URL is a valid music URL (Spotify or YouTube)
    More strict check for auto-detection from clipboard

    Args:
        url: URL string to validate

    Returns:
        True if valid music URL, False otherwise
    """
    url = url.strip()
    url_lower = url.lower()
    
    # Reject if it contains newlines (likely copied log text)
    if '\n' in url or '\r' in url:
        return False
    
    # Reject if too long (likely copied text with URL in it)
    if len(url) > 300:
        return False
    
    # Reject if it contains common log/error text
    invalid_patterns = ['error', 'failed', 'skipping', 'downloaded', 'complete', 
                        'traceback', 'exception', 'warning', '[', ']', '✅', '❌', '⚠']
    for pattern in invalid_patterns:
        if pattern in url_lower:
            return False

    # Spotify URLs - must start with http/https and contain spotify.com
    if 'spotify.com/' in url_lower:
        if not url_lower.startswith(('http://', 'https://')):
            return False
        if any(keyword in url_lower for keyword in ['track', 'album', 'playlist', 'artist']):
            return True

    # YouTube URLs - must start with http/https
    if url_lower.startswith(('http://', 'https://')):
        if 'youtube.com/watch' in url_lower or 'youtu.be/' in url_lower or 'youtube.com/playlist' in url_lower:
            return True

    return False


def is_playlist(url: str) -> bool:
    """
    Check if URL is a playlist

    Args:
        url: URL string to check

    Returns:
        True if playlist URL, False otherwise
    """
    url_lower = url.lower()
    url_stripped = url.strip()

    # Spotify playlists
    spotify_playlist = 'spotify.com' in url_lower and '/playlist/' in url_lower

    # YouTube playlists
    youtube_playlist = 'youtube.com/playlist' in url_lower

    # Special playlist keywords
    special_playlists = url_stripped in ['all-user-playlists', 'all-saved-playlists']

    return spotify_playlist or youtube_playlist or special_playlists


def is_album(url: str) -> bool:
    """
    Check if URL is an album

    Args:
        url: URL string to check

    Returns:
        True if album URL, False otherwise
    """
    url_lower = url.lower()
    return 'spotify.com' in url_lower and '/album/' in url_lower


def get_content_type(url: str) -> str:
    """
    Determine content type from URL

    Args:
        url: URL string to analyze

    Returns:
        Content type: "playlist", "album", "track", or "unknown"
    """
    if is_playlist(url):
        return "playlist"
    if is_album(url):
        return "album"
    if "/track/" in url.lower():
        return "track"
    return "unknown"


# =============================================================================
# PATH UTILITIES
# =============================================================================

def sanitize_folder_name(name: str) -> str:
    """
    Sanitize folder name for filesystem compatibility

    Args:
        name: Folder name to sanitize

    Returns:
        Sanitized folder name
    """
    # Special case mappings
    special_names = {
        "saved": "Liked Songs",
        "all-user-playlists": "All Playlists"
    }

    if name in special_names:
        return special_names[name]

    # Remove or replace invalid characters
    sanitized = "".join(
        c if c.isalnum() or c in " -_'(),." else "_"
        for c in name
    ).strip()

    # Limit length and provide fallback
    return sanitized[:80] or "Download"
