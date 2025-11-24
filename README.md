# SpotDL GUI

A modern, high-performance desktop interface for [SpotDL](https://github.com/spotDL/spotify-downloader) built with PySide6.

## Features

- **Modern Dark Theme** - Professional Qt-based interface
- **Fast Performance** - 2.8x faster than CustomTkinter
- **Dual Template System** - Automatic playlist vs album detection
- **Real-time Downloads** - Live output and progress tracking
- **Smart Organization** - Customizable folder structures
- **Tag System** - Quick template variable insertion
- **Background Processing** - Non-blocking downloads

## Installation

### Prerequisites

1. **Python 3.8+** required
2. **PySide6** for the GUI
3. **SpotDL** for downloading

### Install Dependencies

```bash
pip install PySide6
pip install spotdl
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

## Usage

Run the GUI:

```bash
python spotdl_gui.py
```

### Quick Start

1. **Enter URL** - Paste a Spotify/YouTube URL
2. **Configure** - Choose format, bitrate, options
3. **Download** - Click the download button
4. **Monitor** - Watch progress in the Queue tab

## Configuration

Settings are saved to `~/.spotdl_gui_config.json`

### Templates

**Song File Template** (for albums/tracks):
```
{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}
```

**Playlist Template** (for playlists):
```
{list-name}/{list-position} - {artists} - {title}.{output-ext}
```

### Available Variables

**Song/Album Variables:**
- `{title}` - Song title
- `{artist}` / `{artists}` - Artist names
- `{album}` / `{album-artist}` - Album info
- `{year}` - Release year
- `{track-number}` / `{disc-number}` - Track numbers
- `{genre}` - Genre
- `{output-ext}` - File extension

**Playlist Variables:**
- `{list-name}` - Playlist name
- `{list-position}` - Track position (01, 02, ...)
- `{list-length}` - Total tracks
- Plus all song variables above

## Performance

### Benchmark Results

```
Widget Creation (50 widgets):
- CustomTkinter: 0.540s
- PySide6:      0.190s
→ 2.8x faster

Expected Improvements:
- Startup: ~1-2s faster
- Tab switching: Instant
- Window resizing: Smooth 60fps
```

## Features in Detail

### Automatic Template Switching

The app automatically detects content type and uses the appropriate template:

- **Playlists** → Playlist template (all songs in one folder)
- **Albums** → Album template (organized by artist/album)
- **Tracks** → Album template

### Tag Buttons

Click any tag button to insert it at cursor position:
- Alphabetically sorted
- 6-column layout for easy scanning
- Separate tags for song vs playlist templates

### Command Preview

See the exact `spotdl` command that will run:
- Real-time updates as you change settings
- Copy button for manual execution
- Verify settings before downloading

### Background Downloads

Downloads run in background threads:
- UI remains responsive
- Real-time output to Queue tab
- Multiple concurrent downloads (configurable threads)

## Rollback to CustomTkinter

If you need the old CustomTkinter version:

```bash
# Using git tag
git checkout v1.0-customtkinter

# Or use the backup file
mv spotdl_gui.py spotdl_gui_pyside.py
mv spotdl_gui_ctk.py spotdl_gui.py
```

## Documentation

- [METADATA_SYSTEM.md](METADATA_SYSTEM.md) - Metadata extraction system
- [PLAYLIST_HANDLING.md](PLAYLIST_HANDLING.md) - Playlist vs album handling
- [CHANGELOG_UI.md](CHANGELOG_UI.md) - UI improvements history

## Requirements

- **PySide6 >= 6.6.0** - Qt GUI framework
- **Python 3.8+** - Runtime environment
- **SpotDL** - Music downloader (pip, source, or .exe)

## License

This GUI is a frontend for SpotDL. See [SpotDL's license](https://github.com/spotDL/spotify-downloader/blob/master/LICENSE) for the underlying downloader.

## Credits

Built with:
- [PySide6](https://www.qt.io/qt-for-python) - Qt for Python
- [SpotDL](https://github.com/spotDL/spotify-downloader) - Music downloader
