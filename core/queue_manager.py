"""
Download Queue Manager for SpotDL GUI

Manages download queue, processing items one at a time with pause/resume/cancel support.
"""

import threading
import time
from typing import List, Optional, Dict, Any
from core.queue_item import QueueItem


class DownloadQueueManager:
    """
    Manages the download queue - processes downloads one at a time.

    The queue manager ensures only one download runs at a time, preventing
    resource contention and providing predictable behavior. It runs in a
    background worker thread and communicates with the GUI through callbacks.
    """

    def __init__(self, gui):
        """
        Initialize the queue manager.

        Args:
            gui: Reference to the SpotDLGUI instance for callbacks:
                 - gui.log_to_queue(message): Log to queue tab
                 - gui.update_queue_progress(queue_id, progress): Update progress
                 - gui.update_queue_card_metadata(queue_id, metadata): Update metadata
                 - gui.remove_queue_card(queue_id): Remove card
                 - gui.prepare_and_download(queue_id, ...): Execute download
        """
        self.gui = gui
        self.queue: List[QueueItem] = []
        self.current_item: Optional[QueueItem] = None
        self.worker_thread: Optional[threading.Thread] = None
        self.running = False
        self.paused = False
        self.lock = threading.Lock()  # Thread safety for queue operations
        self.condition = threading.Condition(self.lock)  # For pause/resume signaling

    def add_to_queue(self, item: QueueItem):
        """
        Add item to queue.

        Note: Does NOT automatically start the worker - the GUI must call
        start_worker() if auto-download is enabled. This allows the GUI
        to control when downloads start.

        Args:
            item: QueueItem to add to queue

        Thread-safe: Can be called from any thread (usually GUI thread)
        """
        with self.lock:
            self.queue.append(item)
            queue_position = len(self.queue)

        # Log to GUI
        self.gui.log_to_queue(
            f"➕ Added to queue (position {queue_position}): {item.metadata.get('name', item.query[:50])}\n"
        )

        # Note: GUI is responsible for starting worker based on auto-download setting

    def start_worker(self):
        """
        Start the worker thread that processes queue.

        The worker runs continuously, processing items one at a time until
        the queue is empty. It automatically stops when there's nothing to do.
        """
        with self.lock:
            if self.running:
                return  # Worker already running

            self.running = True
            self.paused = False
            self.worker_thread = threading.Thread(
                target=self._process_queue_worker,
                daemon=True,
                name="QueueWorker"
            )
            self.worker_thread.start()

        print("[QueueManager] Worker thread started")

    def _process_queue_worker(self):
        """
        Worker thread main loop - processes queue items sequentially.

        This runs in a background thread and should not directly manipulate
        the GUI. All GUI updates must go through callbacks.
        """
        print("[QueueManager] Worker loop started")

        while True:
            # Get next item from queue
            with self.lock:
                # Check if paused
                while self.paused and self.running:
                    print("[QueueManager] Worker paused, waiting...")
                    self.condition.wait()  # Wait for resume signal

                # Check if should stop
                if not self.running:
                    print("[QueueManager] Worker stopping (running=False)")
                    break

                # Get next pending item
                next_item = None
                for item in self.queue:
                    if item.status == 'pending':
                        next_item = item
                        break

                if next_item is None:
                    # No more items to process
                    print("[QueueManager] No more items, worker stopping")
                    self.running = False
                    break

                self.current_item = next_item

            # Process the item (outside lock to avoid blocking)
            self._process_item(self.current_item)

            # Small delay between items
            time.sleep(0.5)

        with self.lock:
            self.current_item = None
            self.running = False

        print("[QueueManager] Worker loop ended")

    def _process_item(self, item: QueueItem):
        """
        Process a single queue item - run the download.

        Args:
            item: QueueItem to process

        This method calls back to the GUI's prepare_and_download method,
        which handles the actual download subprocess.
        """
        try:
            print(f"[QueueManager] Processing item: {item.queue_id}")

            # Check if item was cancelled before we started
            if item.status == 'cancelled':
                print(f"[QueueManager] Item {item.queue_id} was cancelled before processing")
                return

            # Mark as downloading
            item.start_download()
            self.gui.log_to_queue(f"⬇️ Starting download: {item.metadata.get('name', item.query[:50])}\n")

            # Extract settings from item
            settings = item.settings

            # Call GUI's download method (this will run in worker thread)
            # The GUI method spawns subprocess and blocks until complete
            self.gui.prepare_and_download(
                queue_id=item.queue_id,
                query=item.query,
                format_val=settings.get('format', 'mp3'),
                bitrate_val=settings.get('bitrate', 'auto'),
                threads_val=str(settings.get('threads', 4)),
                template_val=settings.get('template', '{artist} - {title}'),
                download_folder=settings.get('download_folder', ''),
                folder_per_url=settings.get('folder_per_url', False),
                is_playlist_url=settings.get('is_playlist_url', False),
                is_album_url=settings.get('is_album_url', False),
                preload=settings.get('preload', False),
                sponsor_block=settings.get('sponsor_block', False),
                skip_explicit=settings.get('skip_explicit', False),
                generate_lrc=settings.get('generate_lrc', False),
                playlist_numbering=settings.get('playlist_numbering', False)
            )

            # Download completed successfully (if we reach here)
            with self.lock:
                if item.status == 'downloading':  # Not cancelled
                    item.complete_download()
                    self.gui.log_to_queue(f"✅ Download completed: {item.metadata.get('name', item.query[:50])}\n")

        except Exception as e:
            # Download failed
            print(f"[QueueManager] Error processing item: {e}")
            with self.lock:
                # Only fail if not already cancelled
                if item.status not in ['cancelled', 'completed', 'failed']:
                    item.fail_download(str(e))
                    self.gui.log_to_queue(f"❌ Download failed: {item.metadata.get('name', item.query[:50])} - {str(e)}\n")

    def cancel_download(self, queue_id: str) -> bool:
        """
        Cancel a specific download by queue_id.

        Args:
            queue_id: ID of the queue item to cancel

        Returns:
            True if cancelled, False if not found or already finished

        Thread-safe: Can be called from any thread
        """
        with self.lock:
            # Find item in queue
            item = None
            for q_item in self.queue:
                if q_item.queue_id == queue_id:
                    item = q_item
                    break

            if item is None:
                print(f"[QueueManager] Cancel failed: item {queue_id} not found")
                return False

            if item.is_finished():
                print(f"[QueueManager] Cancel failed: item {queue_id} already finished")
                return False

            # Cancel the item
            item.cancel_download()

        self.gui.log_to_queue(f"🚫 Download cancelled: {item.metadata.get('name', queue_id[:20])}\n")
        print(f"[QueueManager] Cancelled item: {queue_id}")
        return True

    def pause_queue(self):
        """
        Pause queue processing.

        Current download continues, but no new downloads will start until resumed.

        Thread-safe: Can be called from any thread
        """
        with self.condition:
            if self.paused:
                return  # Already paused

            self.paused = True

        self.gui.log_to_queue("⏸️ Queue paused - current download will continue\n")
        print("[QueueManager] Queue paused")

    def resume_queue(self):
        """
        Resume queue processing.

        Thread-safe: Can be called from any thread
        """
        with self.condition:
            if not self.paused:
                return  # Not paused

            self.paused = False
            self.condition.notify()  # Wake up worker thread

        self.gui.log_to_queue("▶️ Queue resumed\n")
        print("[QueueManager] Queue resumed")

    def clear_completed(self):
        """
        Remove all completed/failed/cancelled items from queue.

        Thread-safe: Can be called from any thread
        """
        with self.lock:
            original_count = len(self.queue)
            self.queue = [item for item in self.queue if item.is_active()]
            removed_count = original_count - len(self.queue)

        if removed_count > 0:
            self.gui.log_to_queue(f"🧹 Cleared {removed_count} completed item(s) from queue\n")
            print(f"[QueueManager] Cleared {removed_count} items")

    def get_queue_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all queue items.

        Returns:
            List of dictionaries with item info

        Thread-safe: Can be called from any thread
        """
        with self.lock:
            return [item.to_dict() for item in self.queue]

    def get_queue_summary(self) -> Dict[str, int]:
        """
        Get summary counts of queue items by status.

        Returns:
            Dictionary with counts: {'pending': N, 'downloading': N, 'completed': N, ...}

        Thread-safe: Can be called from any thread
        """
        with self.lock:
            summary = {
                'pending': 0,
                'downloading': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0,
                'total': len(self.queue)
            }

            for item in self.queue:
                if item.status in summary:
                    summary[item.status] += 1

            return summary

    def stop_all(self):
        """
        Stop all downloads and shut down the worker thread.

        Should be called when closing the application.

        Thread-safe: Can be called from any thread
        """
        print("[QueueManager] Stopping all downloads")

        with self.condition:
            # Cancel current download
            if self.current_item and not self.current_item.is_finished():
                self.current_item.cancel_download()

            # Cancel all pending downloads
            for item in self.queue:
                if item.is_active() and item != self.current_item:
                    item.cancel_download()

            # Stop worker
            self.running = False
            self.paused = False
            self.condition.notify()  # Wake up worker if paused

        # Wait for worker to finish (with timeout)
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)

        self.gui.log_to_queue("⏹️ Queue manager stopped\n")
        print("[QueueManager] Stopped")

    def __repr__(self) -> str:
        """String representation for debugging"""
        summary = self.get_queue_summary()
        return (f"DownloadQueueManager(running={self.running}, paused={self.paused}, "
                f"pending={summary['pending']}, downloading={summary['downloading']}, "
                f"completed={summary['completed']})")
