#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced metadata handler

Tests:
1. Metadata extraction for tracks, albums, playlists
2. Direct import method vs subprocess method
3. Template formatting
4. Folder name sanitization
5. Error handling and edge cases
"""

import logging
from metadata_handler import SpotifyMetadataHandler, get_metadata, SPOTDL_AVAILABLE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_metadata(metadata, indent=0):
    """Pretty print metadata dictionary"""
    if not metadata:
        print(f"{'  ' * indent}[No metadata]")
        return

    indent_str = '  ' * indent
    for key, value in metadata.items():
        if key == 'songs':
            print(f"{indent_str}{key}: [{len(value)} songs]")
        elif isinstance(value, list):
            if value:
                print(f"{indent_str}{key}: {', '.join(str(v) for v in value[:3])}" +
                      (f"... (+{len(value)-3} more)" if len(value) > 3 else ""))
            else:
                print(f"{indent_str}{key}: []")
        elif isinstance(value, dict):
            print(f"{indent_str}{key}:")
            print_metadata(value, indent + 1)
        else:
            # Truncate long strings
            value_str = str(value)
            if len(value_str) > 80:
                value_str = value_str[:77] + "..."
            print(f"{indent_str}{key}: {value_str}")


def test_metadata_extraction():
    """Test metadata extraction with various URL types"""
    print_section("TEST 1: Metadata Extraction")

    test_cases = [
        {
            "name": "Track URL",
            "url": "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp",
            "description": "Single track - should return track metadata"
        },
        {
            "name": "Album URL",
            "url": "https://open.spotify.com/album/382ObEPsp2rxGrnsizN5TX",
            "description": "Album - should return album metadata with track list"
        },
        {
            "name": "Playlist URL",
            "url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
            "description": "Playlist - should return playlist metadata"
        }
    ]

    handler = SpotifyMetadataHandler()

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   URL: {test_case['url']}")
        print(f"   Method: {'Direct import' if not handler.use_subprocess else 'Subprocess'}")

        try:
            metadata = handler.get_metadata(test_case['url'])

            if metadata:
                print("\n   ✓ Metadata retrieved successfully:")
                print_metadata(metadata, indent=2)
            else:
                print("\n   ✗ Failed to retrieve metadata")

        except Exception as e:
            print(f"\n   ✗ Error: {e}")

    print("\n" + "-" * 70)
    print("Metadata extraction test completed")


def test_import_vs_subprocess():
    """Test both import and subprocess methods"""
    print_section("TEST 2: Direct Import vs Subprocess Comparison")

    if not SPOTDL_AVAILABLE:
        print("\n⚠ SpotDL modules not available - can only test subprocess method")
        return

    test_url = "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"

    print(f"\nTest URL: {test_url}\n")

    # Test with direct import
    print("1. Direct Import Method:")
    handler_direct = SpotifyMetadataHandler(use_subprocess=False)
    try:
        metadata_direct = handler_direct.get_metadata(test_url)
        if metadata_direct:
            print("   ✓ Success")
            print(f"   Name: {metadata_direct.get('name')}")
            print(f"   Artist: {metadata_direct.get('artist')}")
            print(f"   Type: {metadata_direct.get('type')}")
        else:
            print("   ✗ Failed")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test with subprocess
    print("\n2. Subprocess Method:")
    handler_subprocess = SpotifyMetadataHandler(use_subprocess=True)
    try:
        metadata_subprocess = handler_subprocess.get_metadata(test_url)
        if metadata_subprocess:
            print("   ✓ Success")
            print(f"   Name: {metadata_subprocess.get('name')}")
            print(f"   Artist: {metadata_subprocess.get('artist')}")
            print(f"   Type: {metadata_subprocess.get('type')}")
        else:
            print("   ✗ Failed")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n" + "-" * 70)
    print("Method comparison test completed")


def test_template_formatting():
    """Test template formatting with various templates"""
    print_section("TEST 3: Template Formatting")

    # Sample metadata
    sample_metadata = {
        'name': 'Test Album',
        'type': 'album',
        'artist': 'Test Artist',
        'artists': ['Test Artist', 'Featured Artist'],
        'album': 'Test Album',
        'album_artist': 'Test Artist',
        'year': 2024,
        'date': '2024-01-15',
        'genre': 'Pop',
        'genres': ['Pop', 'Rock'],
    }

    templates = [
        "{artist} - {album} ({year})",
        "{year} - {artist} - {album}",
        "{album_artist} - {album}",
        "{artist} [{genre}] - {album}",
        "{name} by {artist}",
        "[{year}] {artist} - {name}",
    ]

    handler = SpotifyMetadataHandler()

    print("\nSample metadata:")
    print_metadata(sample_metadata, indent=1)

    print("\n\nTemplate Formatting Results:")
    for i, template in enumerate(templates, 1):
        formatted = handler.format_template(template, sample_metadata)
        sanitized = handler.sanitize_folder_name(formatted) if formatted else None

        print(f"\n{i}. Template: {template}")
        print(f"   Formatted: {formatted}")
        print(f"   Sanitized: {sanitized}")

    print("\n" + "-" * 70)
    print("Template formatting test completed")


def test_folder_sanitization():
    """Test folder name sanitization with various inputs"""
    print_section("TEST 4: Folder Name Sanitization")

    test_cases = [
        "Artist - Album (2024)",
        "Artist/Album: The Best",
        "Artist & Friends - Album!",
        "Album [Special Edition]",
        'Album with "Quotes"',
        "Album with <brackets>",
        "Album | Deluxe Edition",
        "Track #1 - Song Name",
        "A" * 150,  # Very long name
        "   Spaces   Everywhere   ",
        "Special_Chars: *?<>|/\\",
    ]

    handler = SpotifyMetadataHandler()

    print("\nSanitization Results:\n")
    for i, test_input in enumerate(test_cases, 1):
        sanitized = handler.sanitize_folder_name(test_input, max_length=100)

        input_display = test_input if len(test_input) <= 50 else test_input[:47] + "..."

        print(f"{i}. Input:  {input_display}")
        print(f"   Output: {sanitized}")
        print(f"   Length: {len(sanitized)} chars")
        print()

    print("-" * 70)
    print("Folder sanitization test completed")


def test_error_handling():
    """Test error handling with invalid inputs"""
    print_section("TEST 5: Error Handling")

    test_cases = [
        ("Invalid URL", "https://invalid-url.com/track/123"),
        ("Empty string", ""),
        ("Non-Spotify URL", "https://youtube.com/watch?v=123"),
        ("Malformed Spotify URL", "https://open.spotify.com/invalid/123"),
    ]

    handler = SpotifyMetadataHandler()

    print("\nError Handling Results:\n")
    for name, test_input in test_cases:
        print(f"Test: {name}")
        print(f"Input: {test_input or '[empty]'}")

        try:
            metadata = handler.get_metadata(test_input)
            if metadata:
                print(f"Result: Got metadata (type: {metadata.get('type')})")
            else:
                print("Result: None (expected for invalid input)")
        except Exception as e:
            print(f"Result: Exception - {type(e).__name__}: {e}")

        print()

    print("-" * 70)
    print("Error handling test completed")


def test_convenience_function():
    """Test the convenience get_metadata function"""
    print_section("TEST 6: Convenience Function")

    test_url = "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"

    print(f"\nTesting get_metadata() convenience function")
    print(f"URL: {test_url}\n")

    metadata = get_metadata(test_url)

    if metadata:
        print("✓ Success\n")
        print("Retrieved metadata:")
        print_metadata(metadata, indent=1)
    else:
        print("✗ Failed to retrieve metadata")

    print("\n" + "-" * 70)
    print("Convenience function test completed")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  ENHANCED METADATA HANDLER TEST SUITE")
    print("=" * 70)

    print(f"\nSpotDL Modules Available: {SPOTDL_AVAILABLE}")
    print(f"Test Mode: {'Direct Import + Subprocess' if SPOTDL_AVAILABLE else 'Subprocess Only'}")

    tests = [
        ("Metadata Extraction", test_metadata_extraction),
        ("Import vs Subprocess", test_import_vs_subprocess),
        ("Template Formatting", test_template_formatting),
        ("Folder Sanitization", test_folder_sanitization),
        ("Error Handling", test_error_handling),
        ("Convenience Function", test_convenience_function),
    ]

    print("\n\nAvailable Tests:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"  {i}. {name}")

    print("\nRunning all tests...\n")

    for name, test_func in tests:
        try:
            test_func()
        except KeyboardInterrupt:
            print("\n\nTests interrupted by user")
            break
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("  TEST SUITE COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
