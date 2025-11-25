# Queue Cards Fix - Root Cause and Solution

## 🔍 Root Cause Found!

The queue cards were not updating because **`QTimer.singleShot()` doesn't work from worker threads!**

### The Problem

Looking at your logs:
```
[DEBUG] Scheduling card update for queue_id=6516549918448684514
[DEBUG] Metadata to update: {'name': 'UNREAL DAMAGE', ...}
[DEBUG] Starting download for queue_id: 6516549918448684514
```

Notice what's **missing**? This line never appears:
```
[DEBUG] update_queue_card_metadata called for queue_id=...
```

**Why?** Because `prepare_and_download()` runs in the queue manager's **worker thread**, not the main GUI thread. When we called:
```python
QTimer.singleShot(0, lambda: self.update_queue_card_metadata(...))
```

Qt couldn't execute it because Qt requires **all GUI updates to happen on the main thread**.

## ✅ The Solution: Qt Signals

I've implemented **Qt Signals** for thread-safe communication from worker thread → GUI thread:

### Changes Made

1. **Added Qt Signals** ([spotdl_gui.py:62-64](spotdl_gui.py#L62-L64)):
   ```python
   class SpotDLGUI(QMainWindow):
       # Qt Signals for thread-safe GUI updates
       create_card_signal = Signal(str, dict)      # queue_id, metadata
       update_metadata_signal = Signal(str, dict)  # queue_id, metadata
       update_progress_signal = Signal(str, int)   # queue_id, progress
   ```

2. **Connected Signals** ([spotdl_gui.py:142-145](spotdl_gui.py#L142-L145)):
   ```python
   self.create_card_signal.connect(self.create_queue_card)
   self.update_metadata_signal.connect(self.update_queue_card_metadata)
   self.update_progress_signal.connect(self.update_queue_progress)
   ```

3. **Replaced QTimer Calls with Signal Emissions**:

   **Before (BROKEN):**
   ```python
   QTimer.singleShot(0, lambda q=qid, m=meta: self.update_queue_card_metadata(q, m))
   ```

   **After (FIXED):**
   ```python
   self.update_metadata_signal.emit(queue_id, updated_metadata)
   ```

### All Replacements:

| Location | What Was Fixed |
|----------|----------------|
| Line 1694 | Create queue card (initial "Loading...") |
| Line 1759 | Update metadata (album/playlist name, artist, image) |
| Line 1806 | Update progress to 50% (download starting) |
| Line 1931 | Update progress to 75% (download in progress) |
| Line 1946 | Update progress to 100% (download complete) |

## How Qt Signals Work

Qt Signals automatically handle thread-safe communication:

```
Worker Thread                    Main GUI Thread
------------                     ---------------
1. Fetch metadata ✓
2. emit signal() ───────────────→ 3. Receive signal
                                   4. Call update method
                                   5. Update GUI ✓
```

The signal automatically:
- Queues the call to the main thread
- Ensures thread-safe execution
- Maintains parameter values correctly

## What You Should See Now

When you add an album/playlist, you'll see:

```
[MetadataHandler] Using subprocess mode (calling spotdl CLI)
[MetadataHandler] Fetching metadata via subprocess for: <URL>
[MetadataHandler] Successfully fetched metadata: <Album Name>
[DEBUG] Metadata fetched successfully: <Album Name>
[DEBUG] Emitting metadata update signal for queue_id=<ID>
[DEBUG] Metadata to update: {'name': '...', 'artist': '...', 'image_url': '...'}
[DEBUG] update_queue_card_metadata called for queue_id=<ID>  ← THIS WAS MISSING!
[DEBUG] Updated card labels for <ID>
[DEBUG] Loading image for <ID>: https://...
```

And the queue card should:
- ✅ Show album/playlist name
- ✅ Show artist name(s)
- ✅ Show album cover image
- ✅ Update progress bar (0% → 50% → 75% → 100%)

## Testing

Run the GUI and add an album:
```bash
python spotdl_gui.py
```

Test URL: `https://open.spotify.com/album/5WmmXuE72sUnSSwEQeyEx6?si=BLy9HZoWSbSZ1GwxM9G3aw`

The card should now update with real metadata and show the album cover!

---

**Status:** FIXED - All GUI updates now use Qt Signals for thread-safe communication ✅
