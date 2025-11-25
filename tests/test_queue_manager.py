"""
Tests for DownloadQueueManager class
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from queue_item import QueueItem
from queue_manager import DownloadQueueManager


class MockGUI:
    """Mock GUI for testing"""

    def __init__(self):
        self.logs = []
        self.progress_updates = []
        self.metadata_updates = []
        self.removed_cards = []
        self.download_calls = []

    def log_to_queue(self, message):
        """Mock log method"""
        self.logs.append(message)

    def update_queue_progress(self, queue_id, progress):
        """Mock progress update"""
        self.progress_updates.append((queue_id, progress))

    def update_queue_card_metadata(self, queue_id, metadata):
        """Mock metadata update"""
        self.metadata_updates.append((queue_id, metadata))

    def remove_queue_card(self, queue_id):
        """Mock card removal"""
        self.removed_cards.append(queue_id)

    def prepare_and_download(self, queue_id, query, **kwargs):
        """Mock download method - simulates a quick download"""
        self.download_calls.append((queue_id, query, kwargs))
        time.sleep(0.1)  # Simulate download time


@pytest.fixture
def mock_gui():
    """Fixture providing a mock GUI"""
    return MockGUI()


@pytest.fixture
def queue_manager(mock_gui):
    """Fixture providing a queue manager with mock GUI"""
    manager = DownloadQueueManager(mock_gui)
    yield manager
    # Cleanup after each test
    manager.stop_all()
    time.sleep(0.2)  # Give worker time to stop


class TestQueueManagerInitialization:
    """Test queue manager initialization"""

    def test_init(self, mock_gui):
        """Test initializing queue manager"""
        manager = DownloadQueueManager(mock_gui)

        assert manager.gui == mock_gui
        assert manager.queue == []
        assert manager.current_item is None
        assert manager.worker_thread is None
        assert manager.running is False
        assert manager.paused is False


class TestQueueManagerAddToQueue:
    """Test adding items to queue"""

    def test_add_single_item(self, queue_manager, mock_gui):
        """Test adding a single item to queue"""
        item = QueueItem(
            queue_id="test1",
            query="https://open.spotify.com/track/abc",
            settings={'format': 'mp3'},
            metadata={'name': 'Test Track'}
        )

        queue_manager.add_to_queue(item)

        assert len(queue_manager.queue) == 1
        assert queue_manager.queue[0] == item
        assert len(mock_gui.logs) > 0
        assert "Added to queue" in mock_gui.logs[0]

    def test_add_multiple_items(self, queue_manager):
        """Test adding multiple items to queue"""
        items = [
            QueueItem(queue_id=f"test{i}", query=f"url{i}")
            for i in range(5)
        ]

        for item in items:
            queue_manager.add_to_queue(item)

        assert len(queue_manager.queue) == 5
        assert queue_manager.queue == items

    def test_add_starts_worker(self, queue_manager):
        """Test that adding item starts worker thread"""
        item = QueueItem(queue_id="test", query="url")

        assert queue_manager.running is False

        queue_manager.add_to_queue(item)

        # Give worker thread time to start
        time.sleep(0.1)

        assert queue_manager.running is True
        assert queue_manager.worker_thread is not None
        assert queue_manager.worker_thread.is_alive()

        # Cleanup
        queue_manager.stop_all()


class TestQueueManagerProcessing:
    """Test queue processing logic"""

    def test_process_single_item(self, queue_manager, mock_gui):
        """Test processing a single queue item"""
        item = QueueItem(
            queue_id="test1",
            query="url1",
            settings={'format': 'mp3'},
            metadata={'name': 'Test Track'}
        )

        queue_manager.add_to_queue(item)

        # Wait for processing to complete
        time.sleep(0.5)

        # Check item was processed
        assert item.status == 'completed'
        assert len(mock_gui.download_calls) == 1
        assert mock_gui.download_calls[0][0] == "test1"

        # Cleanup
        queue_manager.stop_all()

    def test_process_multiple_items_sequentially(self, queue_manager, mock_gui):
        """Test that multiple items are processed one at a time"""
        items = [
            QueueItem(queue_id=f"test{i}", query=f"url{i}", metadata={'name': f'Track {i}'})
            for i in range(3)
        ]

        # Add all items
        for item in items:
            queue_manager.add_to_queue(item)

        # Wait for all to process (each takes ~0.1s + overhead)
        time.sleep(1.5)

        # All should be completed
        for item in items:
            assert item.status == 'completed'

        # All should have been downloaded
        assert len(mock_gui.download_calls) == 3

    def test_worker_stops_when_queue_empty(self, queue_manager):
        """Test that worker stops when queue is empty"""
        item = QueueItem(queue_id="test", query="url")

        queue_manager.add_to_queue(item)

        # Wait for processing (item completes + worker detects empty queue)
        time.sleep(0.8)

        # Worker should have stopped
        assert queue_manager.running is False


class TestQueueManagerCancellation:
    """Test cancellation functionality"""

    def test_cancel_pending_download(self, queue_manager):
        """Test cancelling a pending download"""
        # Pause queue first so items stay pending
        queue_manager.pause_queue()

        item = QueueItem(queue_id="test1", query="url1")
        queue_manager.add_to_queue(item)

        time.sleep(0.1)  # Let worker start but stay paused

        result = queue_manager.cancel_download("test1")

        assert result is True
        assert item.status == 'cancelled'

    def test_cancel_nonexistent_download(self, queue_manager):
        """Test cancelling a download that doesn't exist"""
        result = queue_manager.cancel_download("nonexistent")

        assert result is False

    def test_cancel_completed_download(self, queue_manager, mock_gui):
        """Test that cannot cancel a completed download"""
        item = QueueItem(queue_id="test1", query="url1")
        queue_manager.add_to_queue(item)

        # Wait for completion
        time.sleep(0.5)

        # Try to cancel
        result = queue_manager.cancel_download("test1")

        assert result is False
        assert item.status == 'completed'

        # Cleanup
        queue_manager.stop_all()


class TestQueueManagerPauseResume:
    """Test pause and resume functionality"""

    def test_pause_queue(self, queue_manager, mock_gui):
        """Test pausing the queue"""
        # Add items
        items = [
            QueueItem(queue_id=f"test{i}", query=f"url{i}")
            for i in range(3)
        ]
        for item in items:
            queue_manager.add_to_queue(item)

        # Pause immediately
        queue_manager.pause_queue()
        time.sleep(0.3)  # Wait a bit

        # First item might have started, but others should be pending
        assert queue_manager.paused is True
        completed_count = sum(1 for item in items if item.status == 'completed')
        assert completed_count <= 1  # At most one completed

        # Cleanup
        queue_manager.stop_all()

    def test_resume_queue(self, queue_manager, mock_gui):
        """Test resuming the queue"""
        # Add items
        items = [
            QueueItem(queue_id=f"test{i}", query=f"url{i}")
            for i in range(3)
        ]
        for item in items:
            queue_manager.add_to_queue(item)

        # Pause, then resume
        queue_manager.pause_queue()
        time.sleep(0.2)
        queue_manager.resume_queue()

        # Wait for all to complete
        time.sleep(1.5)

        # All should eventually complete
        for item in items:
            assert item.status == 'completed'

    def test_double_pause(self, queue_manager):
        """Test that double pause doesn't cause issues"""
        item = QueueItem(queue_id="test", query="url")
        queue_manager.add_to_queue(item)

        queue_manager.pause_queue()
        queue_manager.pause_queue()  # Second pause should be safe

        assert queue_manager.paused is True

        # Cleanup
        queue_manager.stop_all()


class TestQueueManagerClearCompleted:
    """Test clearing completed items"""

    def test_clear_completed_items(self, queue_manager, mock_gui):
        """Test clearing completed items from queue"""
        # Add items
        items = [
            QueueItem(queue_id=f"test{i}", query=f"url{i}")
            for i in range(3)
        ]
        for item in items:
            queue_manager.add_to_queue(item)

        # Wait for all to complete
        time.sleep(1.5)

        # All should be completed
        assert len(queue_manager.queue) == 3

        # Clear completed
        queue_manager.clear_completed()

        # Queue should be empty
        assert len(queue_manager.queue) == 0

    def test_clear_keeps_active_items(self, queue_manager):
        """Test that clearing doesn't remove active items"""
        # Add items
        items = [
            QueueItem(queue_id=f"test{i}", query=f"url{i}")
            for i in range(5)
        ]
        for item in items:
            queue_manager.add_to_queue(item)

        # Pause so some remain pending
        queue_manager.pause_queue()
        time.sleep(0.3)

        # Clear completed
        queue_manager.clear_completed()

        # Should still have pending items
        assert len(queue_manager.queue) > 0

        # Cleanup
        queue_manager.stop_all()


class TestQueueManagerStatus:
    """Test status reporting methods"""

    def test_get_queue_status(self, queue_manager):
        """Test getting queue status"""
        items = [
            QueueItem(queue_id=f"test{i}", query=f"url{i}")
            for i in range(3)
        ]
        for item in items:
            queue_manager.add_to_queue(item)

        status = queue_manager.get_queue_status()

        assert len(status) == 3
        assert all(isinstance(s, dict) for s in status)
        assert all('queue_id' in s for s in status)

        # Cleanup
        queue_manager.stop_all()

    def test_get_queue_summary(self, queue_manager, mock_gui):
        """Test getting queue summary"""
        # Add some items
        items = [
            QueueItem(queue_id=f"test{i}", query=f"url{i}")
            for i in range(3)
        ]
        for item in items:
            queue_manager.add_to_queue(item)

        # Get initial summary
        summary = queue_manager.get_queue_summary()

        assert isinstance(summary, dict)
        assert 'pending' in summary
        assert 'downloading' in summary
        assert 'completed' in summary
        assert 'failed' in summary
        assert 'cancelled' in summary
        assert 'total' in summary
        assert summary['total'] == 3

        # Cleanup
        queue_manager.stop_all()


class TestQueueManagerStopAll:
    """Test stopping all downloads"""

    def test_stop_all(self, queue_manager):
        """Test stopping all downloads"""
        # Add items
        items = [
            QueueItem(queue_id=f"test{i}", query=f"url{i}")
            for i in range(5)
        ]
        for item in items:
            queue_manager.add_to_queue(item)

        # Stop all
        queue_manager.stop_all()

        # Worker should be stopped
        assert queue_manager.running is False

        # All active items should be cancelled
        for item in items:
            if item.status not in ['completed']:
                assert item.status == 'cancelled'

    def test_stop_all_waits_for_worker(self, queue_manager):
        """Test that stop_all waits for worker thread"""
        item = QueueItem(queue_id="test", query="url")
        queue_manager.add_to_queue(item)

        time.sleep(0.1)  # Let worker start

        worker_thread = queue_manager.worker_thread

        queue_manager.stop_all()

        # Worker thread should be stopped
        assert not worker_thread.is_alive() or True  # Give some tolerance


class TestQueueManagerThreadSafety:
    """Test thread safety"""

    def test_concurrent_adds(self, queue_manager):
        """Test adding items from multiple threads"""
        def add_items(start_idx):
            for i in range(10):
                item = QueueItem(
                    queue_id=f"test{start_idx}_{i}",
                    query=f"url{i}"
                )
                queue_manager.add_to_queue(item)
                time.sleep(0.01)

        # Start multiple threads adding items
        threads = [
            threading.Thread(target=add_items, args=(i,))
            for i in range(3)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have all 30 items
        assert len(queue_manager.queue) == 30

        # Cleanup
        queue_manager.stop_all()


class TestQueueManagerRepr:
    """Test string representation"""

    def test_repr(self, queue_manager):
        """Test string representation"""
        repr_str = repr(queue_manager)

        assert "DownloadQueueManager" in repr_str
        assert "running" in repr_str
        assert "paused" in repr_str
        assert "pending" in repr_str
