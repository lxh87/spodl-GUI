#!/usr/bin/env python3
"""
Test script to verify queue metadata flow
"""
import sys
from metadata_handler import SpotifyMetadataHandler

# Test album URL
album_url = "https://open.spotify.com/album/3fsnW79AlDwj2mF8HhnByU"

print("="*70)
print("Testing Queue Metadata Flow")
print("="*70)

# Initialize handler (like GUI does)
print("\n1. Initializing metadata handler...")
handler = SpotifyMetadataHandler()

# Fetch metadata (like prepare_and_download does)
print(f"\n2. Fetching metadata for album...")
metadata = handler.get_metadata(album_url)

if metadata:
    print(f"\n3. Metadata fetched successfully!")
    print(f"   Name: {metadata.get('name', 'N/A')}")
    print(f"   Artist: {metadata.get('artist', 'N/A')}")
    print(f"   Type: {metadata.get('type', 'N/A')}")
    print(f"   Cover URL: {metadata.get('cover_url', 'N/A')[:60]}..." if metadata.get('cover_url') else "   Cover URL: N/A")

    # Simulate what GUI does
    print(f"\n4. Simulating GUI update...")
    artists_str = ', '.join(metadata.get('artists', [])) if isinstance(metadata.get('artists'), list) else metadata.get('artist', 'Unknown')
    updated_metadata = {
        'name': metadata.get('name', 'Unknown'),
        'artist': artists_str,
        'type': metadata.get('type', 'album'),
        'image_url': metadata.get('image_url', metadata.get('cover_url', ''))
    }

    print(f"   Card would be updated with:")
    print(f"   - Name: {updated_metadata['name']}")
    print(f"   - Artist: {updated_metadata['artist']}")
    print(f"   - Image URL: {updated_metadata['image_url'][:60]}..." if updated_metadata.get('image_url') else "   - Image URL: (none)")

    print(f"\n✅ SUCCESS: Metadata flow works correctly!")
else:
    print(f"\n❌ FAILED: Metadata fetch returned None")
    print(f"   This means the queue cards won't be updated")

print(f"\n{'='*70}")
