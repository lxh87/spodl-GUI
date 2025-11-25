"""
Tests for QueueItem class
"""

import pytest
from datetime import datetime, timedelta
from queue_item import QueueItem


class TestQueueItemCreation:
    """Test QueueItem creation and initialization"""

    def test_create_with_minimal_params(self):
        """Test creating queue item with minimal required parameters"""
        item = QueueItem(
            queue_id="test123",
            query="https://open.spotify.com/track/abc"
        )

        assert item.queue_id == "test123"
        assert item.query == "https://open.spotify.com/track/abc"
        assert item.status == "pending"
        assert item.progress == 0
        assert item.settings == {}
        assert item.metadata == {}
        assert item.started_at is None
        assert item.completed_at is None
        assert item.error is None
        assert item.process is None
        assert isinstance(item.created_at, datetime)

    def test_create_with_all_params(self):
        """Test creating queue item with all parameters"""
        settings = {'format': 'mp3', 'bitrate': '320k'}
        metadata = {'name': 'Test Track', 'artist': 'Test Artist'}
        created = datetime.now()

        item = QueueItem(
            queue_id="test456",
            query="https://open.spotify.com/album/xyz",
            status="pending",
            settings=settings,
            metadata=metadata,
            progress=0,
            created_at=created
        )

        assert item.queue_id == "test456"
        assert item.settings == settings
        assert item.metadata == metadata
        assert item.created_at == created

    def test_invalid_status_raises_error(self):
        """Test that invalid status raises ValueError"""
        with pytest.raises(ValueError, match="Invalid status"):
            QueueItem(
                queue_id="test789",
                query="https://open.spotify.com/track/abc",
                status="invalid_status"
            )


class TestQueueItemStatusTransitions:
    """Test status transitions and state management"""

    def test_start_download(self):
        """Test starting a download"""
        item = QueueItem(queue_id="test1", query="url1")

        assert item.status == "pending"
        assert item.started_at is None

        item.start_download()

        assert item.status == "downloading"
        assert item.progress == 0
        assert isinstance(item.started_at, datetime)

    def test_start_download_from_invalid_status(self):
        """Test that starting download from non-pending status raises error"""
        item = QueueItem(queue_id="test2", query="url2")
        item.start_download()

        with pytest.raises(ValueError, match="Cannot start download in status"):
            item.start_download()  # Already downloading

    def test_complete_download(self):
        """Test completing a download"""
        item = QueueItem(queue_id="test3", query="url3")
        item.start_download()

        assert item.status == "downloading"
        assert item.completed_at is None

        item.complete_download()

        assert item.status == "completed"
        assert item.progress == 100
        assert isinstance(item.completed_at, datetime)
        assert item.process is None

    def test_complete_download_from_invalid_status(self):
        """Test that completing from non-downloading status raises error"""
        item = QueueItem(queue_id="test4", query="url4")

        with pytest.raises(ValueError, match="Cannot complete download in status"):
            item.complete_download()  # Still pending

    def test_fail_download(self):
        """Test failing a download"""
        item = QueueItem(queue_id="test5", query="url5")
        item.start_download()

        error_msg = "Network error"
        item.fail_download(error_msg)

        assert item.status == "failed"
        assert item.error == error_msg
        assert isinstance(item.completed_at, datetime)
        assert item.process is None

    def test_fail_download_from_pending(self):
        """Test failing a download that hasn't started yet"""
        item = QueueItem(queue_id="test6", query="url6")

        item.fail_download("Failed to start")

        assert item.status == "failed"
        assert item.error == "Failed to start"

    def test_cancel_download_from_pending(self):
        """Test cancelling a pending download"""
        item = QueueItem(queue_id="test7", query="url7")

        item.cancel_download()

        assert item.status == "cancelled"
        assert isinstance(item.completed_at, datetime)

    def test_cancel_download_from_downloading(self):
        """Test cancelling an active download"""
        item = QueueItem(queue_id="test8", query="url8")
        item.start_download()

        item.cancel_download()

        assert item.status == "cancelled"
        assert isinstance(item.completed_at, datetime)

    def test_cancel_download_from_invalid_status(self):
        """Test that cancelling from completed status raises error"""
        item = QueueItem(queue_id="test9", query="url9")
        item.start_download()
        item.complete_download()

        with pytest.raises(ValueError, match="Cannot cancel download in status"):
            item.cancel_download()


class TestQueueItemProgress:
    """Test progress tracking"""

    def test_update_progress_valid_values(self):
        """Test updating progress with valid values"""
        item = QueueItem(queue_id="test10", query="url10")

        item.update_progress(0)
        assert item.progress == 0

        item.update_progress(50)
        assert item.progress == 50

        item.update_progress(100)
        assert item.progress == 100

    def test_update_progress_invalid_values(self):
        """Test that invalid progress values raise error"""
        item = QueueItem(queue_id="test11", query="url11")

        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            item.update_progress(-1)

        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            item.update_progress(101)


class TestQueueItemMetadata:
    """Test metadata management"""

    def test_update_metadata(self):
        """Test updating metadata"""
        item = QueueItem(
            queue_id="test12",
            query="url12",
            metadata={'name': 'Original Name'}
        )

        assert item.metadata == {'name': 'Original Name'}

        item.update_metadata({'artist': 'Test Artist'})
        assert item.metadata == {'name': 'Original Name', 'artist': 'Test Artist'}

        item.update_metadata({'name': 'Updated Name'})
        assert item.metadata == {'name': 'Updated Name', 'artist': 'Test Artist'}


class TestQueueItemQueries:
    """Test query methods"""

    def test_is_active(self):
        """Test is_active method"""
        item = QueueItem(queue_id="test13", query="url13")

        # Pending is active
        assert item.is_active() is True

        # Downloading is active
        item.start_download()
        assert item.is_active() is True

        # Completed is not active
        item.complete_download()
        assert item.is_active() is False

    def test_is_finished(self):
        """Test is_finished method"""
        item = QueueItem(queue_id="test14", query="url14")

        # Pending is not finished
        assert item.is_finished() is False

        # Downloading is not finished
        item.start_download()
        assert item.is_finished() is False

        # Completed is finished
        item.complete_download()
        assert item.is_finished() is True

    def test_is_finished_after_fail(self):
        """Test is_finished returns True for failed downloads"""
        item = QueueItem(queue_id="test15", query="url15")
        item.start_download()
        item.fail_download("Error")

        assert item.is_finished() is True

    def test_is_finished_after_cancel(self):
        """Test is_finished returns True for cancelled downloads"""
        item = QueueItem(queue_id="test16", query="url16")
        item.cancel_download()

        assert item.is_finished() is True

    def test_get_duration(self):
        """Test get_duration method"""
        item = QueueItem(queue_id="test17", query="url17")

        # No duration before start
        assert item.get_duration() is None

        # Start and complete
        item.start_download()
        start_time = item.started_at

        # Simulate some time passing
        item.completed_at = start_time + timedelta(seconds=10)
        item.status = "completed"

        duration = item.get_duration()
        assert duration is not None
        assert 9.9 <= duration <= 10.1  # Allow small floating point variance


class TestQueueItemSerialization:
    """Test serialization and representation"""

    def test_to_dict(self):
        """Test converting queue item to dictionary"""
        settings = {'format': 'mp3'}
        metadata = {'name': 'Test'}

        item = QueueItem(
            queue_id="test18",
            query="url18",
            settings=settings,
            metadata=metadata
        )
        item.start_download()
        item.update_progress(50)

        result = item.to_dict()

        assert result['queue_id'] == "test18"
        assert result['query'] == "url18"
        assert result['status'] == "downloading"
        assert result['progress'] == 50
        assert result['settings'] == settings
        assert result['metadata'] == metadata
        assert isinstance(result['created_at'], str)  # ISO format
        assert isinstance(result['started_at'], str)  # ISO format
        assert result['completed_at'] is None
        assert result['error'] is None

    def test_to_dict_with_error(self):
        """Test to_dict includes error when present"""
        item = QueueItem(queue_id="test19", query="url19")
        item.start_download()
        item.fail_download("Test error")

        result = item.to_dict()

        assert result['status'] == "failed"
        assert result['error'] == "Test error"
        assert result['completed_at'] is not None

    def test_repr(self):
        """Test string representation"""
        item = QueueItem(
            queue_id="test20",
            query="https://open.spotify.com/track/very_long_url_that_should_be_truncated",
            status="downloading"
        )
        item.update_progress(75)

        repr_str = repr(item)

        assert "test20" in repr_str
        assert "downloading" in repr_str
        assert "75%" in repr_str
        assert "..." in repr_str  # URL truncated
