"""
Download Controller Module
Handles download orchestration, command building, and subprocess execution
"""

import subprocess
import os
import re
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional

from gui.utils import sanitize_folder_name, is_playlist


class DownloadController:
    """
    Controller for managing downloads and command execution
    """

    def __init__(self, metadata_fetcher: Callable[[str], Optional[Dict]]):
        """
        Initialize download controller

        Args:
            metadata_fetcher: Callback function to fetch Spotify metadata
        """
        self.metadata_fetcher = metadata_fetcher

    def build_command(self, query: str, settings: Dict[str, Any]) -> List[str]:
        """
        Build spotdl command from settings

        Args:
            query: URL or query string
            settings: Dictionary of download settings

        Returns:
            List of command arguments
        """
        cmd = [
            "spotdl", query,
            "--format", settings['format'],
            "--bitrate", settings['bitrate'],
            "--threads", str(settings['threads']),
            "--output", settings['template']
        ]

        # Add optional flags
        if settings.get('preload', False):
            cmd.append("--preload")
        if settings.get('sponsor_block', False):
            cmd.append("--sponsor-block")
        if settings.get('skip_explicit', False):
            cmd.append("--skip-explicit")
        if settings.get('generate_lrc', False):
            cmd.append("--generate-lrc")
        if settings.get('playlist_numbering', False):
            cmd.append("--playlist-numbering")

        return cmd

    def build_command_preview(self, query: str, format_val: str, bitrate_val: str,
                            template: str) -> str:
        """
        Build command preview string for display

        Args:
            query: URL or query string
            format_val: Audio format
            bitrate_val: Bitrate
            template: Output template

        Returns:
            Command preview string
        """
        return f'spotdl {query} --format {format_val} --bitrate {bitrate_val} --output "{template}"'

    def prepare_and_download(
        self,
        queue_id: str,
        query: str,
        settings: Dict[str, Any],
        callbacks: Dict[str, Callable]
    ):
        """
        Prepare download (fetch metadata, create folders) and execute

        Args:
            queue_id: Unique ID for this queue item
            query: URL or query string
            settings: Dictionary of download settings containing:
                - format: Audio format (mp3, flac, etc.)
                - bitrate: Bitrate (320k, 256k, etc.)
                - threads: Number of threads
                - template: Output template
                - download_folder: Target folder
                - folder_per_url: Create subfolder per URL
                - is_playlist_url: Is this a playlist
                - is_album_url: Is this an album
                - preload: Preload metadata
                - sponsor_block: Skip sponsor segments
                - skip_explicit: Skip explicit tracks
                - generate_lrc: Generate lyrics
                - playlist_numbering: Add playlist numbering
            callbacks: Dictionary of callback functions:
                - log: Function to log messages
                - update_metadata: Function to update metadata (queue_id, metadata_dict)
                - update_progress: Function to update progress (queue_id, percent)
        """
        log = callbacks.get('log', lambda msg: None)
        update_metadata = callbacks.get('update_metadata', lambda qid, meta: None)
        update_progress = callbacks.get('update_progress', lambda qid, pct: None)

        metadata = None

        # Fetch metadata for playlists/albums
        if settings.get('is_playlist_url') or settings.get('is_album_url'):
            log("🔍 Fetching metadata...\n")
            metadata = self.metadata_fetcher(query)

            if metadata:
                log(f"✅ {metadata.get('name', 'Unknown')}\n")
                artists = ', '.join(metadata.get('artists', [])) if isinstance(
                    metadata.get('artists'), list
                ) else metadata.get('artist', 'Unknown')

                update_metadata(queue_id, {
                    'name': metadata.get('name', 'Unknown'),
                    'artist': artists,
                    'image_url': metadata.get('cover_url', metadata.get('image_url', ''))
                })

        # Determine download folder
        download_folder = settings['download_folder']
        if settings.get('folder_per_url', False):
            name = metadata['name'] if metadata else query
            download_folder = os.path.join(download_folder, sanitize_folder_name(name))

        # Build command
        cmd = self.build_command(query, settings)

        # Start download
        update_progress(queue_id, 5)
        self.run_download(queue_id, cmd, download_folder, callbacks)

    def run_download(
        self,
        queue_id: str,
        cmd: List[str],
        download_folder: str,
        callbacks: Dict[str, Callable]
    ):
        """
        Execute download command and monitor output

        Args:
            queue_id: Unique ID for this queue item
            cmd: Command arguments list
            download_folder: Target download folder
            callbacks: Dictionary of callback functions:
                - log: Function to log messages
                - update_progress: Function to update progress (queue_id, percent)
                - update_song_count: Function to update song count (queue_id, current, total)
                - update_current_song: Function to update current song (queue_id, song_name)
                - on_complete: Function called on successful completion (queue_id)
                - on_error: Function called on error (queue_id)
        """
        log = callbacks.get('log', lambda msg: None)
        update_progress = callbacks.get('update_progress', lambda qid, pct: None)
        update_song_count = callbacks.get('update_song_count', lambda qid, cur, tot: None)
        update_current_song = callbacks.get('update_current_song', lambda qid, song: None)
        on_complete = callbacks.get('on_complete', lambda qid: None)
        on_error = callbacks.get('on_error', lambda qid: None)

        try:
            # Create download folder
            os.makedirs(download_folder, exist_ok=True)

            # Start subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=download_folder
            )

            # Monitor output
            for line in process.stdout:
                log(line)

                # Parse "Found X songs" message
                if "Found" in line and "song" in line:
                    match = re.search(r'Found (\d+) song', line)
                    if match:
                        total_songs = int(match.group(1))
                        update_song_count(queue_id, 0, total_songs)

                # Parse "Downloaded" message (completed download)
                if line.strip().startswith("Downloaded") and '"' in line:
                    match = re.search(r'Downloaded "([^"]+)"', line)
                    if match:
                        song_name = match.group(1)
                        update_current_song(queue_id, song_name)

                # Parse "Skipping" message (already exists/duplicate)
                elif line.strip().startswith("Skipping") and '"' in line:
                    match = re.search(r'Skipping "([^"]+)"', line)
                    if match:
                        song_name = match.group(1)
                        update_current_song(queue_id, song_name)

            # Wait for process to complete
            process.wait()
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Handle completion
            if process.returncode == 0:
                log(f"[{timestamp}] ✅ Complete!\n")
                update_progress(queue_id, 100)
                on_complete(queue_id)
            else:
                log(f"[{timestamp}] ❌ Failed\n")
                on_error(queue_id)

        except Exception as e:
            log(f"❌ Error: {e}\n")
            on_error(queue_id)
