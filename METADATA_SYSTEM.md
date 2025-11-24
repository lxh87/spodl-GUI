## Enhanced Metadata System

This document explains the enhanced metadata handling system built on top of spotdl's robust foundation.

### Overview

The metadata system provides comprehensive Spotify metadata extraction with three modes of operation:

1. **Direct Import (Fastest)** - Uses spotdl Python modules directly
2. **Subprocess (Compatible)** - Calls `spotdl` command-line tool
3. **Automatic Fallback** - Intelligently chooses the best available method

### Architecture

```
spotdl_gui.py
    ↓
metadata_handler.py (Unified API)
    ↓
    ├─→ Direct: spotdl.types.* (Python import)
    └─→ Subprocess: spotdl CLI command
```

### Files

| File | Purpose |
|------|---------|
| `metadata_handler.py` | Main metadata extraction and formatting |
| `matching_handler.py` | Audio matching algorithms (optional) |
| `spotdl_gui.py` | GUI application using metadata handlers |
| `test_enhanced_metadata.py` | Comprehensive test suite |

---

## Metadata Handler Features

### 1. Universal Compatibility

The handler automatically detects and works with:

- **Source Code** - `spotdl/` folder in project directory
- **Pip Installed** - `pip install spotdl` (system-wide or venv)
- **Standalone Executable** - `spotdl.exe` (Windows)

### 2. Rich Metadata Extraction

Extracts comprehensive metadata for:

- **Tracks**: 20+ fields including ISRC, popularity, explicit flag, etc.
- **Albums**: Full track list + album metadata
- **Playlists**: Playlist info + all tracks
- **Artists**: Top tracks (via subprocess)

#### Metadata Fields

```python
{
    'type': 'track' | 'album' | 'playlist' | 'artist',
    'name': 'Track/Album/Playlist Name',
    'artist': 'Primary Artist',
    'artists': ['Artist 1', 'Artist 2'],
    'album': 'Album Name',
    'album_artist': 'Album Artist',
    'year': 2024,
    'date': '2024-01-15',
    'genre': 'Pop',
    'genres': ['Pop', 'Rock'],
    'url': 'https://open.spotify.com/...',
    'cover_url': 'https://i.scdn.co/...',

    # Track-specific
    'duration': 180,  # seconds
    'explicit': True,
    'popularity': 85,  # 0-100
    'isrc': 'USUM71234567',
    'track_number': 1,
    'tracks_count': 12,
    'disc_number': 1,
    'disc_count': 1,

    # Album/Playlist-specific
    'track_count': 15,
    'songs': [Song, Song, ...],  # List of Song objects

    # Playlist-specific
    'description': 'Playlist description',
    'author_name': 'Creator Name',
    'author_url': 'https://open.spotify.com/user/...',
}
```

### 3. Template Formatting

Apply metadata to folder naming templates:

```python
handler = SpotifyMetadataHandler()
metadata = handler.get_metadata(url)

# Apply template
formatted = handler.format_template("{artist} - {album} ({year})", metadata)
# Result: "Artist Name - Album Name (2024)"
```

#### Supported Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{name}` | Track/album/playlist name | "Song Title" |
| `{artist}` | Primary artist | "Artist Name" |
| `{artists}` | All artists (comma-separated) | "Artist 1, Artist 2" |
| `{album}` | Album name | "Album Title" |
| `{album-artist}` | Album artist | "Album Artist" |
| `{album_artist}` | Album artist (underscore) | "Album Artist" |
| `{year}` | Release year | "2024" |
| `{date}` | Full release date | "2024-01-15" |
| `{genre}` | Primary genre | "Pop" |
| `{type}` | Content type | "track", "album", "playlist" |

### 4. Folder Name Sanitization

Ensures folder names are safe for all operating systems:

```python
sanitized = handler.sanitize_folder_name("Artist/Album: Title!", max_length=100)
# Result: "Artist_Album_ Title!"
```

**Safe Characters:**
- Alphanumeric: `A-Z a-z 0-9`
- Punctuation: `( ) [ ] - _ ' , & ! .`
- Spaces (normalized)

**Unsafe Characters** (replaced with `_`):
- Path separators: `/ \`
- Special chars: `: * ? < > | "`
- Control characters

---

## Usage Examples

### Basic Usage

```python
from metadata_handler import SpotifyMetadataHandler

# Initialize handler
handler = SpotifyMetadataHandler()

# Get metadata
url = "https://open.spotify.com/track/..."
metadata = handler.get_metadata(url)

if metadata:
    print(f"Name: {metadata['name']}")
    print(f"Artist: {metadata['artist']}")
    print(f"Album: {metadata['album']}")
    print(f"Year: {metadata['year']}")
```

### Force Subprocess Mode

```python
# Use subprocess even if Python imports are available
handler = SpotifyMetadataHandler(use_subprocess=True)
metadata = handler.get_metadata(url)
```

### Template Formatting

```python
handler = SpotifyMetadataHandler()
metadata = handler.get_metadata(url)

# Simple template
folder = handler.format_template("{artist} - {album}", metadata)

# Complex template
folder = handler.format_template(
    "[{year}] {album_artist} - {album} [{genre}]",
    metadata
)

# Sanitize for filesystem
safe_folder = handler.sanitize_folder_name(folder)
```

### Convenience Function

```python
from metadata_handler import get_metadata

# Quick one-liner
metadata = get_metadata("https://open.spotify.com/album/...")

if metadata:
    print(f"{metadata['name']} by {metadata['artist']}")
```

---

## Matching Handler (Optional)

The matching handler provides access to spotdl's audio matching algorithms.

### Features

- **Forbidden Words Detection** - Identifies remixes, covers, live versions
- **Result Scoring** - Scores audio sources by match quality
- **Best Match Selection** - Finds the best audio source

### Usage

```python
from matching_handler import MatchingHandler, is_matching_available

if is_matching_available():
    handler = MatchingHandler()

    # Check forbidden words
    has_forbidden, words = handler.check_forbidden_words(song, result)

    # Score results
    scored = handler.order_results(results, song)

    # Get best matches
    best = handler.get_best_matches(scored, threshold=5.0)

    # Complete workflow
    best_matches = handler.match_song_to_results(song, results)
```

**Note:** Matching requires Song and Result objects, typically available during download operations.

---

## Compatibility Matrix

| Scenario | Direct Import | Subprocess | Notes |
|----------|--------------|------------|-------|
| Source code in `spotdl/` folder | ✓ | ✓ | Fastest, full control |
| `pip install spotdl` | ✓ | ✓ | Standard installation |
| `spotdl.exe` standalone | ✗ | ✓ | Windows portable version |
| Virtual environment | ✓ | ✓ | Depends on venv activation |

### How It Works

1. **Import Detection** - Tries to import spotdl modules
2. **Fallback** - Falls back to subprocess if import fails
3. **Execution** - Uses the available method transparently

```python
# Automatic detection
handler = SpotifyMetadataHandler()
# Uses: Direct import if available, else subprocess

# Manual control
handler_direct = SpotifyMetadataHandler(use_subprocess=False)
handler_subprocess = SpotifyMetadataHandler(use_subprocess=True)
```

---

## Testing

Run comprehensive tests:

```bash
python test_enhanced_metadata.py
```

### Test Coverage

1. **Metadata Extraction** - Tracks, albums, playlists
2. **Method Comparison** - Direct import vs subprocess
3. **Template Formatting** - Various template patterns
4. **Folder Sanitization** - Edge cases and special characters
5. **Error Handling** - Invalid URLs, empty inputs
6. **Convenience Functions** - Helper function testing

### Quick Test

```python
# Test if metadata system is working
from metadata_handler import SPOTDL_AVAILABLE, get_metadata

print(f"SpotDL available: {SPOTDL_AVAILABLE}")

metadata = get_metadata("https://open.spotify.com/track/...")
if metadata:
    print(f"✓ Success: {metadata['name']} by {metadata['artist']}")
else:
    print("✗ Failed to fetch metadata")
```

---

## Integration with GUI

The GUI automatically uses the enhanced metadata handler:

```python
class SpotDLGUI(ctk.CTk):
    def __init__(self):
        # Initialize metadata handler
        self.metadata_handler = SpotifyMetadataHandler()

    def get_spotify_metadata(self, url):
        # Uses enhanced handler
        return self.metadata_handler.get_metadata(url)

    def apply_folder_template(self, template, metadata):
        # Uses enhanced template formatter
        return self.metadata_handler.format_template(template, metadata)

    def sanitize_folder_name(self, name):
        # Uses enhanced sanitizer
        return self.metadata_handler.sanitize_folder_name(name)
```

---

## Future Compatibility

### Updating spotdl

When updating the spotdl source code:

1. **Replace `spotdl/` folder** - Copy new version into project
2. **No code changes needed** - Metadata handler remains compatible
3. **Test** - Run `test_enhanced_metadata.py` to verify

### Using System spotdl

To switch from source code to pip-installed:

1. **Remove `spotdl/` folder** - Optional, import will use system version
2. **Install via pip** - `pip install spotdl`
3. **Works automatically** - Handler detects and uses system installation

### Standalone executable

For `spotdl.exe` (Windows):

1. **Place in PATH** - Or specify full path in subprocess calls
2. **Subprocess mode** - Automatically used (no Python modules)
3. **Feature parity** - Full metadata extraction via subprocess

---

## Performance

### Direct Import vs Subprocess

| Method | Speed | Memory | Use Case |
|--------|-------|--------|----------|
| Direct Import | ~0.5-1s | Lower | Default, when available |
| Subprocess | ~2-3s | Higher | Standalone .exe, fallback |

**Recommendation:** Use direct import when possible (faster, more control)

### Optimization Tips

1. **Reuse handler instance** - Create once, use multiple times
2. **Batch operations** - Process multiple URLs in sequence
3. **Cache metadata** - Store results for repeated queries
4. **Error handling** - Always check for None returns

---

## Troubleshooting

### Import Errors

**Problem:** `ImportError: No module named 'spotdl'`

**Solution:**
- Ensure `spotdl/` folder exists in project directory, OR
- Install via pip: `pip install spotdl`, OR
- System will fall back to subprocess mode

### Subprocess Errors

**Problem:** `FileNotFoundError: spotdl command not found`

**Solution:**
- Install spotdl: `pip install spotdl`, OR
- Add spotdl.exe to PATH, OR
- Ensure virtual environment is activated

### Metadata Returns None

**Possible causes:**
- Invalid URL format
- Network connection issues
- Spotify API rate limiting
- Track/album no longer available

**Debug:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

handler = SpotifyMetadataHandler()
metadata = handler.get_metadata(url)
# Check logs for detailed error information
```

### Template Variables Not Replaced

**Problem:** Template shows `{artist}` instead of artist name

**Solution:**
- Ensure metadata dict has the required keys
- Check for typos in variable names (use exact names from table)
- Verify metadata is not None

---

## Advanced Usage

### Custom Spotify Client

```python
from spotdl.utils.spotify import SpotifyClient

# Initialize with custom credentials
client = SpotifyClient(
    client_id='your_id',
    client_secret='your_secret'
)

# Use in handler (requires modification)
```

### Accessing Song Objects

When using direct import, you can access Song objects:

```python
from spotdl.types.song import Song

handler = SpotifyMetadataHandler(use_subprocess=False)
metadata = handler.get_metadata(album_url)

if 'songs' in metadata:
    for song in metadata['songs']:
        # song is a Song object
        print(f"{song.name} - {song.duration}s")
```

### Custom Matching Logic

```python
from matching_handler import MatchingHandler

handler = MatchingHandler()

# Get forbidden words list
forbidden = handler.get_forbidden_words()
print(f"Forbidden: {', '.join(forbidden)}")

# Check a result
has_forbidden, found = handler.check_forbidden_words(song, result)
if has_forbidden:
    print(f"Warning: Contains {', '.join(found)}")
```

---

## API Reference

### SpotifyMetadataHandler

#### `__init__(use_subprocess=False)`
Initialize the handler.

**Parameters:**
- `use_subprocess` (bool): Force subprocess mode

#### `get_metadata(url_or_query) -> Optional[Dict]`
Get metadata for URL or query.

**Returns:** Metadata dict or None

#### `format_template(template, metadata) -> Optional[str]`
Apply metadata to template.

**Returns:** Formatted string or None

#### `sanitize_folder_name(name, max_length=100) -> str`
Sanitize folder name.

**Returns:** Safe folder name

### Convenience Functions

#### `get_metadata(url_or_query, use_subprocess=False) -> Optional[Dict]`
Quick metadata fetch.

#### `is_matching_available() -> bool`
Check if matching utilities are available.

---

## License & Credits

This metadata system is built on top of [spotdl](https://github.com/spotDL/spotify-downloader), which is licensed under the MIT License.

The enhanced metadata and matching handlers provide a clean interface to spotdl's robust functionality while maintaining compatibility across different installation methods.
