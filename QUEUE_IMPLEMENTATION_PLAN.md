# Download Queue Implementation Plan

## Problem Analysis

### Current Issues
1. **No Queue Management**: `download_queue = []` exists but is NEVER used
2. **Subprocess-Based**: Downloads spawn subprocess calling spotdl CLI instead of using Python API
3. **Concurrent Downloads**: Multiple clicks spawn multiple processes (no serialization)
4. **Limited Progress**: Progress tracking parses subprocess stdout for keywords ("Downloaded", "Processing")
5. **No Per-Song Progress**: Can't track individual songs within albums/playlists
6. **No Control**: Can't pause, cancel, or manage downloads

### Current Flow
```
User clicks Download
  → start_download() captures settings, creates queue card
  → Spawns thread calling prepare_and_download()
    → Fetches metadata (for albums/playlists)
    → Spawns subprocess: spotdl [url] --format mp3 ...
    → Parses stdout line-by-line for progress keywords
    → Updates progress bar to 75% when sees "Downloaded"
    → Updates to 100% on completion
```

### Architecture Discovery

**Spotdl Library Structure:**
- `Downloader` class: Main downloader with async support
- `Song` dataclass: All metadata (name, artist, album, cover_url, etc.)
- `ProgressHandler`: Rich-based progress tracking with callbacks
- `download_multiple_songs(songs: List[Song])`: Async download with progress
- `get_simple_songs(query)`: Parses URL/query into Song objects

**Key Files:**
- `spotdl/download/downloader.py`: Downloader class
- `spotdl/download/progress_handler.py`: Progress tracking
- `spotdl/types/song.py`: Song dataclass
- `spotdl/console/download.py`: Console entry point

## Solution: Two-Phase Approach

### Phase 1: Add Queue Management (Keep Subprocess) ✅ RECOMMENDED FOR NOW
**Goal**: Implement proper queue system without changing download mechanism

**Benefits:**
- ✅ Low risk - minimal changes to existing code
- ✅ Immediate value - proper queue management
- ✅ Quick to implement and test
- ✅ Subprocess isolation (crash doesn't affect GUI)
- ✅ Doesn't break existing functionality

**Limitations:**
- ❌ Still limited progress tracking
- ❌ Can't get per-song progress in albums
- ❌ Still parsing text output

### Phase 2: Integrate Spotdl API (Future Enhancement) 🔮
**Goal**: Use spotdl Python API for better progress and control

**Benefits:**
- ✅ Real progress callbacks via ProgressHandler
- ✅ Per-song progress tracking
- ✅ Can pause/cancel specific songs
- ✅ Access to full Song metadata
- ✅ More efficient (no subprocess overhead)

**Challenges:**
- ⚠️ More complex implementation
- ⚠️ Need custom ProgressHandler for Qt signals
- ⚠️ Async/event loop integration with Qt
- ⚠️ Higher risk of bugs

---

## Phase 1 Implementation Plan (CURRENT FOCUS)

### 1. Queue Data Structure

```python
class QueueItem:
    """Represents a download in the queue"""
    queue_id: str
    query: str  # URL or query
    status: str  # 'pending', 'downloading', 'completed', 'failed'
    settings: dict  # format, bitrate, template, flags, etc.
    metadata: dict  # name, artist, type, image_url
    progress: int  # 0-100
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
    process: Optional[subprocess.Popen]  # Current subprocess
```

### 2. Queue Manager Class

```python
class DownloadQueueManager:
    """Manages the download queue"""

    def __init__(self, gui):
        self.gui = gui
        self.queue: List[QueueItem] = []
        self.current_item: Optional[QueueItem] = None
        self.worker_thread = None
        self.running = False
        self.lock = threading.Lock()

    def add_to_queue(self, item: QueueItem):
        """Add item to queue and start processing if needed"""

    def start_worker(self):
        """Start the worker thread that processes queue"""

    def process_queue(self):
        """Worker thread - processes queue one at a time"""

    def cancel_download(self, queue_id: str):
        """Cancel a specific download"""

    def pause_queue(self):
        """Pause queue processing"""

    def resume_queue(self):
        """Resume queue processing"""

    def clear_completed(self):
        """Remove completed/failed items from queue"""

    def get_queue_status(self) -> List[dict]:
        """Get status of all queue items"""
```

### 3. Integration with Existing GUI

**Changes to SpotDLGUI class:**

```python
# In __init__:
self.queue_manager = DownloadQueueManager(self)

# In start_download():
# Instead of spawning thread directly, create QueueItem and add to queue
item = QueueItem(
    queue_id=queue_id,
    query=query,
    status='pending',
    settings={...},
    metadata=initial_metadata,
    progress=0,
    created_at=datetime.now()
)
self.queue_manager.add_to_queue(item)

# Queue manager will call back to:
# - self.log_to_queue() for logging
# - self.update_queue_progress() for progress
# - self.update_queue_card_metadata() for metadata updates
# - self.remove_queue_card() on completion
```

### 4. Test Structure

**Create `tests/` directory structure:**
```
tests/
├── __init__.py
├── conftest.py                 # Pytest fixtures
├── test_queue_manager.py      # Queue manager tests
├── test_queue_item.py         # QueueItem tests
├── test_clipboard.py          # Clipboard monitoring tests
├── test_gui_integration.py   # GUI integration tests (mock Qt)
└── fixtures/
    ├── sample_metadata.json
    └── sample_urls.txt
```

**Move existing tests:**
```
mv test_metadata.py tests/
mv test_enhanced_metadata.py tests/
mv test_folder_template.py tests/
```

### 5. Test Cases

**test_queue_manager.py:**
- `test_add_to_queue()` - Add items to queue
- `test_process_queue_sequentially()` - Items processed one at a time
- `test_cancel_download()` - Cancel specific download
- `test_pause_resume_queue()` - Pause/resume functionality
- `test_queue_status()` - Get queue status
- `test_error_handling()` - Handle download failures
- `test_multiple_concurrent_adds()` - Thread safety

**test_queue_item.py:**
- `test_queue_item_creation()` - Create queue item
- `test_status_transitions()` - Valid state transitions
- `test_progress_updates()` - Progress tracking
- `test_serialization()` - Save/load queue state

**test_clipboard.py:**
- `test_clipboard_detection()` - Detect valid URLs
- `test_clipboard_invalid_urls()` - Ignore invalid content
- `test_clipboard_duplicate_detection()` - Ignore duplicates

### 6. Implementation Steps

**Step 1: Create QueueItem class**
- File: `queue_item.py`
- Tests: `tests/test_queue_item.py`

**Step 2: Create DownloadQueueManager**
- File: `queue_manager.py`
- Tests: `tests/test_queue_manager.py`

**Step 3: Integrate with GUI**
- Modify: `spotdl_gui.py`
- Tests: `tests/test_gui_integration.py`

**Step 4: Move existing tests**
- Move test files to `tests/`
- Update imports
- Add conftest.py with shared fixtures

**Step 5: Add UI controls**
- Pause/Resume button
- Cancel button per queue item
- Clear completed button
- Queue item count display

### 7. Backwards Compatibility

**Ensure no breaking changes:**
- All existing features continue to work
- Settings are preserved
- Queue cards display as before
- Progress updates work as before
- Just add queue management on top

### 8. Success Criteria

✅ Multiple downloads queued and processed sequentially
✅ Can cancel individual downloads
✅ Can pause/resume queue
✅ Progress bars update correctly
✅ Queue cards show correct status
✅ All tests pass
✅ No breaking changes to existing functionality
✅ Test coverage > 80%

---

## Phase 2: Spotdl API Integration (Future)

### Overview
Replace subprocess calls with spotdl Python API for better progress tracking.

### Key Components

**1. Custom ProgressHandler with Qt Signals:**
```python
class QtProgressHandler(ProgressHandler):
    """ProgressHandler that emits Qt signals"""

    progress_updated = Signal(str, int, int)  # (song_id, current, total)
    song_started = Signal(dict)  # Song metadata
    song_completed = Signal(str, bool)  # (song_id, success)
```

**2. Downloader Wrapper:**
```python
class SpotdlDownloader:
    """Wrapper around spotdl.Downloader with Qt integration"""

    def __init__(self, settings):
        self.downloader = Downloader(settings)
        self.progress_handler = QtProgressHandler()

    async def download_songs(self, songs: List[Song]):
        """Download songs with progress callbacks"""
```

**3. Integration:**
```python
# In queue_manager.py:
def process_item_with_api(self, item: QueueItem):
    """Process queue item using spotdl API"""

    # Parse query into songs
    songs = get_simple_songs([item.query])

    # Download with progress callbacks
    downloader = SpotdlDownloader(item.settings)
    downloader.progress_handler.progress_updated.connect(
        lambda song_id, curr, total: self.update_song_progress(item, song_id, curr, total)
    )

    results = await downloader.download_songs(songs)
```

### Benefits of Phase 2
- Per-song progress in albums/playlists
- Real-time progress (not estimated)
- Better error handling
- Can implement pause/resume per song
- Access to full song metadata
- No text parsing needed

### Challenges
- Async/await integration with Qt event loop
- More complex error handling
- Need to maintain event loop in GUI thread
- Testing async code

---

## File Organization

### Current Structure:
```
spodl-GUI/
├── spotdl_gui.py           # Main GUI
├── metadata_handler.py     # Metadata extraction
├── test_metadata.py        # Metadata tests
├── test_enhanced_metadata.py
├── test_folder_template.py
└── spotdl/                 # Spotdl library source
```

### Proposed Structure:
```
spodl-GUI/
├── spotdl_gui.py           # Main GUI (modified)
├── queue_item.py           # NEW: QueueItem class
├── queue_manager.py        # NEW: DownloadQueueManager
├── metadata_handler.py     # Existing
├── tests/                  # NEW: Test directory
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_queue_manager.py
│   ├── test_queue_item.py
│   ├── test_clipboard.py
│   ├── test_metadata.py         # Moved
│   ├── test_enhanced_metadata.py # Moved
│   ├── test_folder_template.py  # Moved
│   └── fixtures/
│       ├── sample_metadata.json
│       └── sample_urls.txt
└── spotdl/                 # Spotdl library source
```

---

## Risk Assessment

### Phase 1 Risks: LOW ✅

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Queue deadlock | Low | High | Thread safety with locks, timeouts |
| Subprocess hang | Medium | Medium | Process timeouts, cleanup on error |
| Breaking existing features | Low | High | Comprehensive testing, backwards compat |
| Memory leak (queue growth) | Low | Medium | Clear completed items, max queue size |

### Phase 2 Risks: MEDIUM ⚠️

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Event loop conflicts | Medium | High | Separate thread for async operations |
| Async bugs | Medium | Medium | Extensive async testing |
| Breaking changes in spotdl | Low | High | Pin spotdl version, integration tests |
| Performance regression | Low | Medium | Benchmark before/after |

---

## Timeline Estimate

### Phase 1: Queue Management
- QueueItem class: 2-3 hours
- DownloadQueueManager: 4-5 hours
- GUI integration: 3-4 hours
- Tests: 4-5 hours
- Test migration: 1-2 hours
- **Total: 14-19 hours** (2-3 days)

### Phase 2: API Integration (Future)
- QtProgressHandler: 3-4 hours
- SpotdlDownloader wrapper: 4-5 hours
- Async integration: 5-6 hours
- Tests: 5-6 hours
- **Total: 17-21 hours** (3-4 days)

---

## Decision: Implement Phase 1 Now

**Rationale:**
1. **Low Risk**: Minimal changes to existing code
2. **High Value**: Proper queue management is essential
3. **Quick Win**: Can be done in 2-3 days
4. **Foundation**: Sets up for Phase 2 later
5. **User Need**: Multiple downloads is a common use case

**Phase 2 can be considered later** once Phase 1 is stable and if there's a need for:
- Per-song progress in large playlists
- Pause/resume individual songs
- Better error reporting
