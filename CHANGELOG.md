# Changelog

## v2.4.3 - App Icon Update (2025-11-27)

### Visual Improvements

1. **New Application Icon**
   - Added custom icon featuring music note combined with download arrow
   - Uses app's signature green color (#4CAF50) on dark background
   - Modern, minimalist flat design suitable for desktop application
   - Scalable design for various window sizes and system displays

### Technical Details
- `spotdl_gui.py`: Added `QIcon` import and `app.setWindowIcon(app_icon)` to load custom icon
- `icon.png`: New 512x512px PNG icon file added to project root

---

## v2.4.2 - UI/UX Improvements (2025-11-27)

### UI/UX Improvements

1. **Tooltips fixed**
   - Dark background (#333) with white text for better readability
   - Consistent 9pt font size across all tooltips

2. **Clear URL button**
   - Visible ✕ button inside the URL text field (right side)
   - Hover effect with red highlight
   - Properly styled within the input container

3. **Delete job button**
   - Added ✕ button on each queue card (full height, right side)
   - Tall rectangle with rounded corners
   - Turns red on hover
   - Cancels download if active, removes from queue

4. **Music folder button**
   - Moved from sidebar to queue panel controls (more accessible)

5. **Horizontal splitter**
   - Removed max-width constraint, allowing more flexible resizing

### Queue Status Improvements

1. **Clearer pending job status**
   - Shows "⏸ Queue paused - Press ▶ Start" when paused/auto-download off
   - Shows "⏳ In queue..." when waiting normally
   - No more confusing "Loading...", "Fetching...", "Waiting..."

2. **Skipped songs detection (duplicates)**
   - Properly counts skipped files across multi-line output
   - Shows ⏭️ icon with orange color for skipped songs
   - Final status shows "All skipped (already exist)" or "Done (X skipped)"
   - Progress bar turns orange if all songs were skipped

### Auto-Detection Improvements

1. **Auto-add on link detection**
   - Detected URLs are automatically added to queue
   - Respects auto-download checkbox setting

2. **Stricter URL validation**
   - Rejects clipboard text with newlines, error keywords, or excessive length
   - Prevents false positives from copied log text

### Bug Fixes

1. **Encoding fix**
   - Subprocess uses UTF-8 with error replacement for Windows compatibility
   - Fixes crashes when output contains emoji characters

### Technical Details
- `theme.py`: Updated QToolTip stylesheet with dark background and white text
- `download_panel.py`: Embedded clear button inside URL field
- `queue_panel.py`: Added music folder button, delete signal, and `update_all_cards_paused_state()` method
- `queue_card.py`: Added delete button, paused state tracking, skipped songs counter, and visual states
- `main_window.py`: Removed max-width, connected signals, auto-add logic, stricter validation
- `controller.py`: UTF-8 encoding with error replacement for subprocess output

---

## v2.4.0 - Project Reorganization (2025-11-27)

### Project Structure
- **New `core/` package**: Created for backend logic (queue management, metadata handling)
- **Cleaned up root directory**: Removed unused legacy files
- **Better separation**: Frontend (gui/) and backend (core/) are now clearly separated

### Files Moved to `core/`
- `queue_manager.py` - Download queue management
- `queue_item.py` - Queue item data structure
- `metadata_handler.py` - Spotify metadata fetching

### Files Deleted
- `matching_handler.py` - Unused legacy file
- `spotdl_gui_ctk.py` - Old CustomTkinter version (54KB)
- `test_queue_metadata_flow.py` - Obsolete test file

### Technical Details
- Updated all imports across gui/, core/, and tests/
- Maintained git history with `git mv` for moved files
- All tests updated to use `core.` imports
- Application tested and confirmed working

---

## v2.3.3 - UI/UX Fixes (2025-11-27)

### Improvements
1. **Tooltip readability**: Tooltips now have white background with black text instead of dark grey
2. **Progress counter accuracy**: Fixed counting for long song names that wrap across multiple lines
3. **URL field clear button**: Added ✕ button to quickly clear the URL field

### Technical Details
- Added QToolTip styling to theme.py for better readability
- Controller now handles wrapped "Downloaded" lines with fallback regex
- Clear button added to download_panel.py next to paste button

---

## v2.3.2 - UX Improvements (2025-11-27)

### Improvements
1. **Progress counting for duplicates**: Now correctly counts skipped files and LookupErrors
2. **LookupError handling**: Shows warning when songs can't be found (⚠️ Could not find: [song])
3. **Vertical splitter flexibility**: Further relaxed minimum heights (30px each) for better resizing
4. **Queue card size increase**: All fonts increased by 2pt and card height increased to 70px
   - Card height: 62→70px
   - Album art: 52x52→60x60px
   - Title font: 10px→12px
   - Artist font: 9px→11px
   - Song font: 8px→10px
   - Count font: 9px→11px
   - Status font: 7px→9px
   - Progress bar height: 4→6px

### Technical Details
- Controller now parses "Skipping" messages without quotes
- Controller now detects and logs "LookupError: No results found" messages
- All dynamic font sizes in queue_card.py updated consistently
- Minimum heights reduced from 60/40→30/30 for maximum splitter flexibility

---

## v2.3.1 - Bug Fixes (2025-11-26)

### Bug Fixes
1. **Auto-download toggle**: Now works correctly - downloads won't start when disabled
2. **Progress counter**: Fixed duplicate file counting (0/X) and double-counting (2X/X)
3. **Vertical splitter**: Relaxed minimum height limits for better resizing
4. **Tooltips**: Restored all tooltips that were missing after refactoring

### Technical Details
- queue_manager no longer auto-starts worker (MainWindow controls this)
- Controller counts both "Downloaded" and "Skipped" messages
- Uses startswith() to prevent double-counting progress lines
- Reduced queue cards min height from 120→60, log from 80→40

---

## v2.3 - Architecture Refactoring (2025-11-26)

### Major Changes
- **Modular Architecture**: Complete refactoring from monolithic 1,449-line file into 9 focused modules
- **Backward Compatible**: 100% compatible with v2.2 - same entry point, same UX
- **Maintainability**: Each module now has a single responsibility for easier maintenance and testing

### New Module Structure
Created the following modules in the `gui/` package:
- `utils.py` - Utility functions (ThreadSafeLogger, ClipboardMonitor, URL validation)
- `theme.py` - Dark theme stylesheet management
- `config.py` - ConfigManager for settings persistence
- `controller.py` - DownloadController for command building and execution
- `download_panel.py` - Left panel widget for download configuration
- `queue_panel.py` - Right panel widget for queue management
- `queue_card.py` - Individual queue card widget
- `settings_panel.py` - Settings tab widget
- `main_window.py` - Main application window integrating all panels

### Technical Improvements
- Clean separation of concerns between UI and business logic
- Reusable widget components for better code organization
- Signal-based communication between components
- Thread-safe logging and UI updates
- Simplified entry point (spotdl_gui.py reduced to 27 lines)

### Documentation Cleanup
- Removed 9 implementation/debug documentation files
- Renamed CHANGELOG_UI.md to CHANGELOG.md
- Kept essential documentation: README.md, QUICKSTART.md, TROUBLESHOOTING.md
