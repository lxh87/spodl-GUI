"""
Queue Item module for SpotDL GUI

Represents a single download in the queue with all its metadata and state.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import subprocess


@dataclass
class QueueItem:
    """
    Represents a download in the queue.

    Attributes:
        queue_id: Unique identifier for this queue item
        query: URL or search query to download
        status: Current status ('pending', 'downloading', 'completed', 'failed', 'cancelled')
        settings: Download settings (format, bitrate, template, flags, etc.)
        metadata: Track/album/playlist metadata (name, artist, type, image_url, etc.)
        progress: Download progress (0-100)
        created_at: Timestamp when item was added to queue
        started_at: Timestamp when download started (None if not started)
        completed_at: Timestamp when download completed (None if not completed)
        error: Error message if download failed (None if no error)
        process: Subprocess handle for the running download (None if not running)
    """

    queue_id: str
    query: str
    status: str = 'pending'
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    progress: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    process: Optional[subprocess.Popen] = None

    def __post_init__(self):
        """Validate status value"""
        valid_statuses = ['pending', 'downloading', 'completed', 'failed', 'cancelled']
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")

    def start_download(self):
        """Mark download as started"""
        if self.status != 'pending':
            raise ValueError(f"Cannot start download in status: {self.status}")
        self.status = 'downloading'
        self.started_at = datetime.now()
        self.progress = 0

    def update_progress(self, progress: int):
        """Update download progress (0-100)"""
        if not 0 <= progress <= 100:
            raise ValueError(f"Progress must be between 0 and 100, got {progress}")
        self.progress = progress

    def complete_download(self):
        """Mark download as completed successfully"""
        if self.status != 'downloading':
            raise ValueError(f"Cannot complete download in status: {self.status}")
        self.status = 'completed'
        self.completed_at = datetime.now()
        self.progress = 100
        self.process = None

    def fail_download(self, error: str):
        """Mark download as failed with error message"""
        if self.status not in ['downloading', 'pending']:
            raise ValueError(f"Cannot fail download in status: {self.status}")
        self.status = 'failed'
        self.completed_at = datetime.now()
        self.error = error
        self.process = None

    def cancel_download(self):
        """Cancel the download"""
        if self.status not in ['pending', 'downloading']:
            raise ValueError(f"Cannot cancel download in status: {self.status}")

        # Kill process if running
        if self.process:
            try:
                self.process.kill()
                self.process.wait(timeout=5)
            except Exception:
                pass
            self.process = None

        self.status = 'cancelled'
        self.completed_at = datetime.now()

    def update_metadata(self, metadata: Dict[str, Any]):
        """Update metadata dictionary"""
        self.metadata.update(metadata)

    def is_active(self) -> bool:
        """Check if download is currently active"""
        return self.status in ['pending', 'downloading']

    def is_finished(self) -> bool:
        """Check if download is finished (completed, failed, or cancelled)"""
        return self.status in ['completed', 'failed', 'cancelled']

    def get_duration(self) -> Optional[float]:
        """Get download duration in seconds (None if not finished)"""
        if not self.started_at or not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for serialization/logging)"""
        return {
            'queue_id': self.queue_id,
            'query': self.query,
            'status': self.status,
            'settings': self.settings,
            'metadata': self.metadata,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
            'duration': self.get_duration()
        }

    def __repr__(self) -> str:
        """String representation for debugging"""
        return (f"QueueItem(queue_id='{self.queue_id}', query='{self.query[:50]}...', "
                f"status='{self.status}', progress={self.progress}%)")
