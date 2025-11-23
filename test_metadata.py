#!/usr/bin/env python3
"""
Test script to extract metadata from Spotify URLs
"""
import subprocess
import json
import tempfile
import os

def test_metadata_extraction(url):
    """Test extracting metadata from a Spotify URL"""
    print(f"Testing URL: {url}\n")

    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.spotdl', delete=False) as temp_file:
            temp_path = temp_file.name

        print(f"Running: spotdl save {url} --save-file {temp_path}")

        # Run spotdl save
        result = subprocess.run(
            ["spotdl", "save", url, "--save-file", temp_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"\nReturn code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")

        if result.returncode == 0 and os.path.exists(temp_path):
            # Read the metadata
            with open(temp_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            print(f"\n{'='*60}")
            print("METADATA STRUCTURE:")
            print(f"{'='*60}")
            print(f"Type: {type(metadata)}")
            print(f"Length: {len(metadata) if isinstance(metadata, list) else 'N/A'}")

            if isinstance(metadata, list) and len(metadata) > 0:
                print(f"\nFirst item keys: {metadata[0].keys()}")
                print(f"\nFirst item data:")
                for key, value in metadata[0].items():
                    print(f"  {key}: {value}")

                # Extract names
                print(f"\n{'='*60}")
                print("EXTRACTED NAMES:")
                print(f"{'='*60}")
                if 'list_name' in metadata[0]:
                    print(f"list_name: {metadata[0]['list_name']}")
                if 'album' in metadata[0]:
                    print(f"album: {metadata[0]['album']}")
                if 'artist' in metadata[0]:
                    print(f"artist: {metadata[0]['artist']}")
                if 'artists' in metadata[0]:
                    print(f"artists: {metadata[0]['artists']}")

            # Cleanup
            try:
                os.unlink(temp_path)
            except:
                pass
        else:
            print("Failed to get metadata or file doesn't exist")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Test with the album URL provided by the user
    album_url = "https://open.spotify.com/intl-de/album/4EgtTz16lhI1IkdPgEYKre?si=8s6L5efWS6GKKC-RFGjYiw"
    test_metadata_extraction(album_url)
