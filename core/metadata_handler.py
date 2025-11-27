"""
Metadata Handler - Unified interface for spotdl metadata operations

This module provides a robust interface for fetching and handling Spotify metadata.
It works with:
1. spotdl installed from source (local spotdl/ folder)
2. spotdl installed via pip (system-wide or venv)
3. spotdl.exe standalone executable (falls back to subprocess)

The module automatically detects which method is available and uses the best option.
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure logging
logger = logging.getLogger(__name__)

# Try to import spotdl modules (works with pip or source)
SPOTDL_AVAILABLE = False
Song = None
Album = None
Playlist = None
SpotifyClient = None

try:
    # Add local spotdl directory to path if it exists
    script_dir = Path(__file__).parent
    spotdl_dir = script_dir / "spotdl"
    if spotdl_dir.exists():
        sys.path.insert(0, str(spotdl_dir))

    # Try importing spotdl modules
    from spotdl.types.song import Song
    from spotdl.types.album import Album
    from spotdl.types.playlist import Playlist
    from spotdl.utils.spotify import SpotifyClient

    SPOTDL_AVAILABLE = True
    logger.info("✓ Successfully imported spotdl modules")
except ImportError as e:
    logger.warning(f"⚠ Could not import spotdl modules: {e}")
    logger.info("Will fall back to subprocess calls")


class MetadataError(Exception):
    """Base class for metadata-related errors"""
    pass


class SpotifyMetadataHandler:
    """
    Unified handler for Spotify metadata extraction.

    Automatically uses the best available method:
    1. Direct Python import (fastest, most control)
    2. Subprocess call to spotdl (compatible with standalone .exe)
    """

    def __init__(self, use_subprocess: bool = False):
        """
        Initialize the metadata handler.

        Args:
            use_subprocess: Force subprocess mode even if imports are available
        """
        self.use_subprocess = use_subprocess or not SPOTDL_AVAILABLE
        self.spotify_client = None

        if not self.use_subprocess:
            try:
                self.spotify_client = SpotifyClient()
                logger.info("✓ Initialized Spotify API client")
                print("[MetadataHandler] Using direct Python API mode")
            except Exception as e:
                logger.warning(f"⚠ Failed to initialize Spotify client: {e}")
                print(f"[MetadataHandler] Spotify client init failed: {e}")
                print("[MetadataHandler] Falling back to subprocess mode")
                self.use_subprocess = True

        if self.use_subprocess:
            print("[MetadataHandler] Using subprocess mode (calling spotdl CLI)")

    def get_metadata(self, url_or_query: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive metadata for any Spotify URL or query.

        Supports:
        - Track URLs
        - Album URLs
        - Playlist URLs
        - Artist URLs
        - Special queries (saved, all-user-playlists, etc.)

        Args:
            url_or_query: Spotify URL or special query

        Returns:
            Dictionary with metadata fields, or None if fetch fails
        """
        if not url_or_query:
            return None

        if self.use_subprocess:
            return self._get_metadata_subprocess(url_or_query)
        else:
            return self._get_metadata_direct(url_or_query)

    def _get_metadata_direct(self, url_or_query: str) -> Optional[Dict[str, Any]]:
        """Get metadata using direct Python imports (fastest method)"""
        try:
            # Detect type from URL
            url_lower = url_or_query.lower()

            if "/track/" in url_lower:
                return self._get_track_metadata(url_or_query)
            elif "/album/" in url_lower:
                return self._get_album_metadata(url_or_query)
            elif "/playlist/" in url_lower:
                return self._get_playlist_metadata(url_or_query)
            elif "/artist/" in url_lower:
                return self._get_artist_metadata(url_or_query)
            else:
                # For queries, use subprocess as it's more reliable
                return self._get_metadata_subprocess(url_or_query)

        except Exception as e:
            logger.error(f"Error getting metadata directly: {e}")
            # Fall back to subprocess
            return self._get_metadata_subprocess(url_or_query)

    def _get_track_metadata(self, url: str) -> Dict[str, Any]:
        """Get metadata for a single track"""
        song = Song.from_url(url)

        return {
            'type': 'track',
            'name': song.name,
            'artist': song.artist,
            'artists': song.artists,
            'album': song.album_name,
            'album_artist': song.album_artist,
            'year': song.year,
            'date': song.date,
            'genre': song.genres[0] if song.genres else '',
            'genres': song.genres,
            'url': song.url,
            'duration': song.duration,
            'explicit': song.explicit,
            'popularity': song.popularity,
            'track_number': song.track_number,
            'tracks_count': song.tracks_count,
            'disc_number': song.disc_number,
            'disc_count': song.disc_count,
            'cover_url': song.cover_url,
            'isrc': song.isrc,
            'publisher': song.publisher,
            'copyright_text': song.copyright_text,
            'song_id': song.song_id,
            'album_id': song.album_id,
        }

    def _get_album_metadata(self, url: str) -> Dict[str, Any]:
        """Get metadata for an album"""
        metadata, songs = Album.get_metadata(url)

        # Get additional info from first song
        first_song = songs[0] if songs else None

        result = {
            'type': 'album',
            'name': metadata['name'],
            'artist': metadata['artist']['name'],
            'artists': [metadata['artist']['name']],
            'album': metadata['name'],
            'album_artist': metadata['artist']['name'],
            'url': metadata['url'],
            'track_count': len(songs),
            'songs': songs,
        }

        # Add fields from first song
        if first_song:
            result.update({
                'year': first_song.year,
                'date': first_song.date,
                'genre': first_song.genres[0] if first_song.genres else '',
                'genres': first_song.genres,
                'cover_url': first_song.cover_url,
                'publisher': first_song.publisher,
                'copyright_text': first_song.copyright_text,
                'album_id': first_song.album_id,
                'album_type': first_song.album_type,
            })

        return result

    def _get_playlist_metadata(self, url: str) -> Dict[str, Any]:
        """Get metadata for a playlist"""
        metadata, songs = Playlist.get_metadata(url)

        # Get year from first song
        first_song = songs[0] if songs else None

        result = {
            'type': 'playlist',
            'name': metadata['name'],
            'url': metadata['url'],
            'description': metadata['description'],
            'author_name': metadata['author_name'],
            'author_url': metadata['author_url'],
            'cover_url': metadata['cover_url'],
            'track_count': len(songs),
            'songs': songs,
        }

        # Try to extract artist and year from first song
        if first_song:
            result.update({
                'artist': first_song.artist,
                'artists': first_song.artists,
                'album': first_song.album_name,
                'album_artist': first_song.album_artist,
                'year': first_song.year,
                'date': first_song.date,
                'genre': first_song.genres[0] if first_song.genres else '',
                'genres': first_song.genres,
            })

        return result

    def _get_artist_metadata(self, url: str) -> Dict[str, Any]:
        """Get metadata for an artist (top tracks)"""
        # For artist URLs, we'll use subprocess as it's more straightforward
        return self._get_metadata_subprocess(url)

    def _get_metadata_subprocess(self, url_or_query: str) -> Optional[Dict[str, Any]]:
        """Get metadata using subprocess call to spotdl (compatible with .exe)"""
        try:
            print(f"[MetadataHandler] Fetching metadata via subprocess for: {url_or_query}")

            # Create temporary file for metadata
            with tempfile.NamedTemporaryFile(mode='w', suffix='.spotdl', delete=False) as temp_file:
                temp_path = temp_file.name

            # Run spotdl save to get metadata
            result = subprocess.run(
                ["spotdl", "save", url_or_query, "--save-file", temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0 or not os.path.exists(temp_path):
                logger.error(f"spotdl save failed: {result.stderr}")
                print(f"[MetadataHandler] spotdl save failed: {result.stderr}")
                return None

            # Read the .spotdl file (it's JSON)
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass

            # Parse and structure the metadata
            if not isinstance(data, list) or len(data) == 0:
                print(f"[MetadataHandler] Invalid data format or empty list")
                return None

            metadata = self._parse_subprocess_metadata(data, url_or_query)
            if metadata:
                print(f"[MetadataHandler] Successfully fetched metadata: {metadata.get('name', 'Unknown')}")
            return metadata

        except subprocess.TimeoutExpired:
            logger.error("Timeout while fetching metadata")
            return None
        except Exception as e:
            logger.error(f"Error in subprocess metadata fetch: {e}")
            return None

    def _parse_subprocess_metadata(self, data: List[Dict], url_or_query: str) -> Dict[str, Any]:
        """Parse metadata from spotdl save JSON output"""
        first_item = data[0]

        # Detect type
        content_type = 'track'
        if 'list_name' in first_item and first_item.get('list_name'):
            if '/playlist/' in url_or_query.lower():
                content_type = 'playlist'
            elif '/album/' in url_or_query.lower():
                content_type = 'album'

        # Build comprehensive metadata dict
        metadata = {
            'type': content_type,
            'name': None,
            'artist': first_item.get('artist', ''),
            'artists': first_item.get('artists', []),
            'album': first_item.get('album_name', first_item.get('album', '')),
            'album_artist': first_item.get('album_artist', first_item.get('artist', '')),
            'year': first_item.get('year', ''),
            'date': first_item.get('date', ''),
            'genre': '',
            'genres': first_item.get('genres', []),
            'url': first_item.get('url', url_or_query),
            'track_count': len(data),
        }

        # Extract genre
        if isinstance(metadata['genres'], list) and metadata['genres']:
            metadata['genre'] = metadata['genres'][0]

        # Extract display name
        if first_item.get('list_name'):
            metadata['name'] = first_item['list_name']
        elif first_item.get('album_name'):
            metadata['name'] = first_item['album_name']
        elif first_item.get('album'):
            metadata['name'] = first_item['album']
        elif first_item.get('name'):
            metadata['name'] = first_item['name']
        else:
            metadata['name'] = first_item.get('artist', 'Unknown')

        # Add track-specific fields if available
        if 'duration' in first_item:
            metadata['duration'] = first_item['duration']
        if 'explicit' in first_item:
            metadata['explicit'] = first_item['explicit']
        if 'popularity' in first_item:
            metadata['popularity'] = first_item['popularity']
        if 'cover_url' in first_item:
            metadata['cover_url'] = first_item['cover_url']
        if 'isrc' in first_item:
            metadata['isrc'] = first_item['isrc']
        if 'publisher' in first_item:
            metadata['publisher'] = first_item['publisher']

        return metadata

    def format_template(self, template: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Apply metadata to a folder name template.

        Supports variables:
        - {name} - Track/album/playlist name
        - {artist} - Primary artist
        - {artists} - All artists joined with ', '
        - {album} - Album name
        - {album-artist} or {album_artist} - Album artist
        - {year} - Release year
        - {date} - Full release date
        - {genre} - Primary genre

        Args:
            template: Template string like "{artist} - {album} ({year})"
            metadata: Metadata dictionary

        Returns:
            Formatted string with variables replaced, or None if template/metadata invalid
        """
        if not template or not metadata:
            return None

        result = template

        # Create mapping with both dash and underscore variants
        replacements = {
            'name': metadata.get('name', 'Unknown'),
            'artist': metadata.get('artist', 'Unknown'),
            'artists': ', '.join(metadata.get('artists', [])) if isinstance(metadata.get('artists'), list) else metadata.get('artists', 'Unknown'),
            'album': metadata.get('album', 'Unknown'),
            'album-artist': metadata.get('album_artist', metadata.get('artist', 'Unknown')),
            'album_artist': metadata.get('album_artist', metadata.get('artist', 'Unknown')),
            'year': str(metadata.get('year', 'Unknown')),
            'date': metadata.get('date', 'Unknown'),
            'genre': metadata.get('genre', 'Unknown'),
            'type': metadata.get('type', 'Unknown'),
        }

        # Replace all variables
        for key, value in replacements.items():
            result = result.replace(f'{{{key}}}', str(value) if value else 'Unknown')

        return result

    def sanitize_folder_name(self, name: str, max_length: int = 100) -> str:
        """
        Sanitize a string to be safe for use as a folder name.

        Args:
            name: The string to sanitize
            max_length: Maximum length for the folder name

        Returns:
            Sanitized folder name safe for all operating systems
        """
        if not name:
            return "Unknown"

        # Safe characters: alphanumeric, space, and these punctuation marks
        safe_chars = (' ', '-', '_', "'", ',', '&', '!', '(', ')', '[', ']', '.')

        # Replace unsafe characters with underscore
        safe_name = ""
        for c in name:
            if c.isalnum() or c in safe_chars:
                safe_name += c
            else:
                safe_name += '_'

        # Normalize spaces and clean up
        safe_name = ' '.join(safe_name.split())  # Collapse multiple spaces
        safe_name = safe_name.strip('_').strip()

        # Limit length
        if len(safe_name) > max_length:
            safe_name = safe_name[:max_length].rstrip()

        return safe_name or "Unknown"


def get_metadata(url_or_query: str, use_subprocess: bool = False) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get metadata for a Spotify URL or query.

    Args:
        url_or_query: Spotify URL or query string
        use_subprocess: Force subprocess mode

    Returns:
        Metadata dictionary or None if fetch fails
    """
    handler = SpotifyMetadataHandler(use_subprocess=use_subprocess)
    return handler.get_metadata(url_or_query)
