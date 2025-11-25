"""
Pytest configuration and shared fixtures for SpotDL GUI tests
"""

import pytest
import json
from pathlib import Path


@pytest.fixture
def sample_urls():
    """Fixture providing sample Spotify/YouTube URLs"""
    return {
        'track': 'https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp',
        'album': 'https://open.spotify.com/album/3fsnW79AlDwj2mF8HhnByU',
        'playlist': 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M',
        'youtube_video': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'youtube_short': 'https://youtu.be/dQw4w9WgXcQ',
        'invalid': 'https://example.com/not-a-music-url'
    }


@pytest.fixture
def sample_metadata():
    """Fixture providing sample metadata"""
    fixtures_dir = Path(__file__).parent / 'fixtures'
    metadata_file = fixtures_dir / 'sample_metadata.json'

    with open(metadata_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def sample_settings():
    """Fixture providing sample download settings"""
    return {
        'format': 'mp3',
        'bitrate': '320k',
        'threads': 4,
        'template': '{artist} - {title}',
        'download_folder': '/tmp/downloads',
        'folder_per_url': False,
        'is_playlist_url': False,
        'is_album_url': False,
        'preload': False,
        'sponsor_block': False,
        'skip_explicit': False,
        'generate_lrc': False,
        'playlist_numbering': False
    }


@pytest.fixture
def temp_download_dir(tmp_path):
    """Fixture providing a temporary download directory"""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    return download_dir


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Fixture to reset any global singletons between tests.

    This ensures test isolation when using singleton patterns.
    """
    yield
    # Reset any global state here if needed
