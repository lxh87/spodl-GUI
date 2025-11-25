# Debug Queue Cards - Investigation Results

## What I Found

### ✅ Metadata Fetching Works
Tested the metadata flow with `test_queue_metadata_flow.py` - **IT WORKS!**

```
[MetadataHandler] Spotify client init failed: (expected, needs credentials)
[MetadataHandler] Falling back to subprocess mode
[MetadataHandler] Using subprocess mode (calling spotdl CLI)
[MetadataHandler] Fetching metadata via subprocess for: https://open.spotify.com/album/...
[MetadataHandler] Successfully fetched metadata: Philantropiques

Metadata includes:
   - Name: Philantropiques
   - Artist: Guts, Jowee Omicil
   - Cover URL: https://i.scdn.co/image/ab67616d0000b273b3c12aa7fe1cb14f6ee0...
```

### Debug Logging Added

I've added comprehensive debug logging to trace the issue:

1. **Metadata Handler** (`metadata_handler.py`):
   - Shows when falling back to subprocess mode
   - Shows when fetching metadata
   - Shows successful metadata retrieval

2. **GUI get_spotify_metadata** (`spotdl_gui.py:1815-1826`):
   - Shows when metadata is fetched successfully
   - Shows errors if metadata fetch fails

3. **GUI prepare_and_download** (`spotdl_gui.py:1749-1751`):
   - Shows when scheduling card update
   - Shows the queue_id being used
   - Shows the metadata being passed

4. **GUI update_queue_card_metadata** (`spotdl_gui.py:1588-1605`):
   - Shows when method is called
   - Shows the queue_id and metadata
   - Shows available queue_items keys
   - Shows if queue_id is not found
   - Shows when labels are updated
   - Shows when loading images

## How to Test

### Option 1: Test with Real GUI
1. Run the GUI: `python spotdl_gui.py`
2. Add an **album** or **playlist** URL (not a single track)
   - Example album: `https://open.spotify.com/album/3fsnW79AlDwj2mF8HhnByU`
3. Watch the console output for debug messages

### Option 2: Test Metadata Only
Run the test script:
```bash
python test_queue_metadata_flow.py
```

## What to Look For

When you add an album/playlist to the queue, you should see this sequence in the console:

```
1. [MetadataHandler] Using subprocess mode (calling spotdl CLI)

2. [MetadataHandler] Fetching metadata via subprocess for: <URL>

3. [MetadataHandler] Successfully fetched metadata: <Album Name>

4. [DEBUG] Metadata fetched successfully: <Album Name>

5. [DEBUG] Scheduling card update for queue_id=<ID>

6. [DEBUG] Metadata to update: {'name': '...', 'artist': '...', ...}

7. [DEBUG] update_queue_card_metadata called for queue_id=<ID>

8. [DEBUG] Updated card labels for <ID>

9. [DEBUG] Loading image for <ID>: https://...
```

## Potential Issues

If the cards aren't updating, look for these problems in the console:

### Issue 1: Metadata Not Being Fetched
**Symptoms:**
```
[DEBUG] Metadata fetch returned None for: <URL>
⚠️ Could not fetch metadata
```

**Cause:** The `spotdl save` command is failing
**Fix:** Check if spotdl is installed and working: `spotdl --version`

### Issue 2: Queue ID Mismatch
**Symptoms:**
```
[DEBUG] ERROR: queue_id <ID> not found in queue_items!
[DEBUG] queue_items keys: [...]  # Different IDs
```

**Cause:** The queue_id used to create the card doesn't match the one used to update it
**Fix:** This would be a bug in the queue ID generation

### Issue 3: QTimer Not Firing
**Symptoms:**
- You see "Scheduling card update" but NOT "update_queue_card_metadata called"

**Cause:** QTimer.singleShot is not executing the callback
**Fix:** Might need to use a different threading approach

### Issue 4: Only Works for Single Tracks
**Symptom:** Single tracks update, but albums/playlists don't

**Cause:** The code at line 1731 only fetches metadata for albums/playlists:
```python
if is_playlist_url or is_album_url:  # Only for albums/playlists
    metadata = self.get_spotify_metadata(query)
```

**This is intentional** - single tracks probably get metadata from spotdl output directly.

## Next Steps

1. **Run the GUI** and test with an album URL
2. **Check the console output** - share it if cards still don't update
3. Look for which debug message sequence you see
4. This will tell us exactly where the flow is breaking

## Test URLs

Good URLs to test with:

### Albums:
- `https://open.spotify.com/album/3fsnW79AlDwj2mF8HhnByU`
- `https://open.spotify.com/album/4EgtTz16lhI1IkdPgEYKre`

### Playlists:
- `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`

### Tracks (metadata might not be fetched):
- `https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp`

---

**Status:** Ready for testing with real downloads to see console output.
