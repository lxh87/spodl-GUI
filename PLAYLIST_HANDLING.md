# Playlist vs Album Automatic Template Switching

## Overview

The GUI now automatically detects whether you're downloading a **playlist** or an **album/track** and uses the appropriate template for optimal folder organization.

---

## The Problem (Before)

When downloading playlists with the standard album template:
```
{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}
```

Each song would be organized by its **original album**, scattering playlist songs across multiple folders:
```
Output/
├── Artist 1/2020 - Album A/01 - Song 1.mp3
├── Artist 2/2021 - Album B/03 - Song 2.mp3
├── Artist 3/2019 - Album C/05 - Song 3.mp3
└── Artist 4/2022 - Album D/02 - Song 4.mp3
```

**Result**: Playlist songs scattered everywhere! 😞

---

## The Solution (After)

Now the GUI automatically uses **two different templates**:

### 1. Album/Track Template (Default)
```
{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}
```

**Used for**:
- Albums
- Individual tracks
- Artist downloads

**Creates structure**:
```
Output/
└── Artist Name/
    └── 2024 - Album Name/
        ├── 01 - Song 1.mp3
        ├── 02 - Song 2.mp3
        └── 03 - Song 3.mp3
```

### 2. Playlist Template (Automatic)
```
{list-name}/{list-position} - {artists} - {title}.{output-ext}
```

**Used for**:
- Spotify playlists
- YouTube playlists
- Special queries (saved, all-user-playlists, etc.)

**Creates structure**:
```
Output/
└── My Awesome Playlist/
    ├── 01 - Artist 1 - Song 1.mp3
    ├── 02 - Artist 2 - Song 2.mp3
    ├── 03 - Artist 3 - Song 3.mp3
    └── 04 - Artist 4 - Song 4.mp3
```

**Result**: All playlist songs in ONE folder! 🎉

---

## How It Works

### Automatic Detection

The GUI automatically detects playlists by checking the URL:

| URL Type | Detection | Template Used |
|----------|-----------|---------------|
| `spotify.com/playlist/...` | ✅ Playlist | Playlist Template |
| `spotify.com/album/...` | ❌ Album | Album Template |
| `spotify.com/track/...` | ❌ Track | Album Template |
| `youtube.com/playlist?list=...` | ✅ Playlist | Playlist Template |
| `saved` | ✅ Playlist | Playlist Template |
| `all-user-playlists` | ✅ Playlist | Playlist Template |

### Visual Feedback

When you click Download, you'll see:
```
🎼 Using playlist template
```
or
```
💿 Using album/track template
```

### Command Preview

The command preview at the bottom of the Download tab shows exactly which template will be used:
- Playlist URL → Shows playlist template in command
- Album URL → Shows album template in command

---

## Settings Configuration

### Location
Settings → **Song File Template** (for albums/tracks)
Settings → **Playlist Template** (for playlists only)

### Default Templates

**Album/Track Template**:
```
{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}
```

**Playlist Template**:
```
{list-name}/{list-position} - {artists} - {title}.{output-ext}
```

### Customization

Both templates are fully customizable! Use the clickable tags or type your own.

#### Album Template Variables
- `{title}` - Song title
- `{artist}` - Primary artist
- `{artists}` - All artists
- `{album}` - Album name
- `{album-artist}` - Album artist
- `{year}` - Release year
- `{track-number}` - Track number
- `{disc-number}` - Disc number
- `{genre}` - Genre
- `{isrc}` - ISRC code
- `{publisher}` - Publisher
- `{output-ext}` - File extension

#### Playlist Template Variables (Additional)
- `{list-name}` - Playlist name
- `{list-position}` - Position in playlist (auto-padded: 01, 02, 03...)
- `{list-length}` - Total songs in playlist
- Plus all album variables above!

---

## Example Use Cases

### Use Case 1: Workout Playlist
**URL**: `https://open.spotify.com/playlist/37i9dQZF1DX76Wlfdnj7AP`

**With Playlist Template** (`{list-name}/{list-position} - {artists} - {title}.{output-ext}`):
```
Workout Hits/
├── 01 - The Weeknd - Blinding Lights.mp3
├── 02 - Dua Lipa - Levitating.mp3
├── 03 - Bruno Mars - Uptown Funk.mp3
└── ...
```

✅ All songs in one folder, easy to copy to your phone!

**Without** (using album template):
```
The Weeknd/2020 - After Hours/03 - Blinding Lights.mp3
Dua Lipa/2020 - Future Nostalgia/05 - Levitating.mp3
Mark Ronson/2014 - Uptown Special/04 - Uptown Funk.mp3
...
```

❌ Songs scattered across 50+ folders!

### Use Case 2: Album Download
**URL**: `https://open.spotify.com/album/382ObEPsp2rxGrnsizN5TX`

**With Album Template** (`{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}`):
```
Taylor Swift/
└── 2014 - 1989/
    ├── 01 - Welcome To New York.mp3
    ├── 02 - Blank Space.mp3
    ├── 03 - Style.mp3
    └── ...
```

✅ Perfect album organization!

### Use Case 3: Custom Playlist Template
Want numbered tracks without artist names?

**Template**: `{list-name}/{list-position} - {title}.{output-ext}`

**Result**:
```
Chill Vibes/
├── 01 - Blinding Lights.mp3
├── 02 - Levitating.mp3
├── 03 - Uptown Funk.mp3
```

Want artist folders inside playlist folder?

**Template**: `{list-name}/{artists}/{title}.{output-ext}`

**Result**:
```
My Playlist/
├── The Weeknd/
│   └── Blinding Lights.mp3
├── Dua Lipa/
│   └── Levitating.mp3
└── Bruno Mars/
    └── Uptown Funk.mp3
```

---

## Advanced: Template Combinations

### Group by Artist, Keep Position
**Template**: `{list-name}/{artists}/{list-position} - {title}.{output-ext}`

```
Running Mix/
├── Artist 1/
│   ├── 02 - Song A.mp3
│   └── 07 - Song B.mp3
└── Artist 2/
    ├── 01 - Song C.mp3
    └── 05 - Song D.mp3
```

### Include Album Info
**Template**: `{list-name}/{list-position} - {artists} - {title} ({album}).{output-ext}`

```
Best of 2024/
├── 01 - Artist 1 - Song 1 (Album A).mp3
├── 02 - Artist 2 - Song 2 (Album B).mp3
```

### Flat Structure (No Folders)
**Template**: `{list-name} - {list-position} - {title}.{output-ext}`

```
My Playlist - 01 - Song 1.mp3
My Playlist - 02 - Song 2.mp3
My Playlist - 03 - Song 3.mp3
```

---

## How Position Numbering Works

The `{list-position}` variable is **automatically zero-padded** based on playlist length:

| Playlist Size | Padding | Example |
|---------------|---------|---------|
| 1-9 songs | 1 digit | `1`, `2`, `9` |
| 10-99 songs | 2 digits | `01`, `05`, `99` |
| 100-999 songs | 3 digits | `001`, `042`, `999` |

This ensures proper alphabetical sorting in file browsers!

---

## Interaction with Other Features

### "Create Folder per URL" Setting
- **Enabled**: Creates an outer folder, then uses template inside
- **Disabled**: Template controls the entire folder structure

**Example with "Create Folder per URL" + Custom Folder Name**:
```
Output/
└── [Custom Folder Name]/
    └── [Template Result]/
        └── Song.mp3
```

### Playlist Numbering Flag
The `--playlist-numbering` checkbox does NOT affect folder structure.

It only modifies the **audio file metadata tags**:
- Sets album name = playlist name (in MP3 tags)
- Sets track number = playlist position (in MP3 tags)

Useful for music players that organize by metadata!

---

## Migration Guide

### Updating from Old Setup

**If you had custom playlist handling before**:
1. Go to Settings
2. Find "Playlist Template (for playlists only)"
3. Customize as needed
4. Click "Save Settings"

**Your existing album template** won't be affected!

### Recommended Templates

**For Album Collectors**:
```
Album: {album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}
Playlist: {list-name}/{list-position} - {artists} - {title}.{output-ext}
```

**For DJ/Playlist Curators**:
```
Album: {artists}/{album}/{title}.{output-ext}
Playlist: {list-name}/{list-position} - {title}.{output-ext}
```

**For Minimalists**:
```
Album: {album-artist}/{album}/{title}.{output-ext}
Playlist: {list-name}/{title}.{output-ext}
```

---

## Troubleshooting

### Q: Playlist songs still going to separate folders?
**A**: Check that you're using playlist-specific variables like `{list-name}` in the **Playlist Template** setting.

### Q: Can I disable automatic template switching?
**A**: Yes! Just set both templates to the same value in Settings.

### Q: What about YouTube playlists?
**A**: They work the same way! The GUI automatically detects `youtube.com/playlist?list=...` URLs.

### Q: Can I see which template will be used before downloading?
**A**: Yes! The command preview at the bottom of the Download tab shows the exact command with the correct template.

### Q: How do I update just the playlist template?
**A**: Settings → "Playlist Template (for playlists only)" → Edit → "Save Settings"

---

## Technical Details

### Detection Logic

The GUI uses these methods (in `spotdl_gui.py`):

```python
def is_playlist(url):
    """Detect if URL is a playlist"""
    # Checks for:
    # - spotify.com/playlist/
    # - youtube.com/playlist?list=
    # - Special queries: saved, all-user-playlists, etc.

def is_album(url):
    """Detect if URL is an album"""
    # Checks for:
    # - spotify.com/album/
    # - all-user-saved-albums
```

### Template Selection

```python
# In start_download():
if is_playlist_url:
    template_val = self.playlist_template_entry.get()
else:
    template_val = self.template_entry.get()
```

### Config Storage

Templates are saved in `~/.spotdl_gui_config.json`:
```json
{
  "output": "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}",
  "playlist_output": "{list-name}/{list-position} - {artists} - {title}.{output-ext}"
}
```

---

## Summary

✅ **Automatic**: No manual switching needed
✅ **Smart**: Detects playlists vs albums
✅ **Flexible**: Fully customizable templates
✅ **Visual**: Command preview shows which template
✅ **Organized**: Playlists in one folder, albums properly structured

Now you can download both albums and playlists without songs getting scattered everywhere! 🎵
