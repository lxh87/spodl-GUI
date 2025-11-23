#!/usr/bin/env python3
"""
Test folder template functionality
"""

import sys
import os

# Mock the metadata that would come from Spotify
test_metadata = {
    'name': 'Coast To Coast',
    'artist': 'Coast To Coast',
    'artists': 'Coast To Coast',
    'album': 'Coast To Coast',
    'album-artist': 'Coast To Coast',
    'year': '2018',
    'genre': 'Pop',
}

def apply_folder_template(template, metadata):
    """Apply metadata to folder name template"""
    if not template or not metadata:
        return None

    result = template
    for key, value in metadata.items():
        if key != 'name':  # 'name' is only for auto-detect, not for templates
            result = result.replace(f"{{{key}}}", str(value) if value else "Unknown")

    return result

def sanitize_folder_name(url_or_query):
    """Create a safe folder name from URL or query"""
    # Replace problematic characters but keep safe punctuation
    # Safe characters: alphanumeric, space, dash, underscore, apostrophe, comma, ampersand,
    # exclamation, parentheses, square brackets, period
    safe_chars = (' ', '-', '_', "'", ',', '&', '!', '(', ')', '[', ']', '.')
    safe_name = ""
    for c in url_or_query:
        if c.isalnum() or c in safe_chars:
            safe_name += c
        else:
            safe_name += '_'

    # Clean up multiple underscores and trim
    safe_name = ' '.join(safe_name.split())  # Normalize spaces
    safe_name = safe_name.strip('_').strip()

    return safe_name[:100]  # Limit length

# Test cases
test_templates = [
    "{artist} ({year})",
    "{artist} - {year}",
    "{year} - {album}",
    "{album-artist} [{year}]",
    "{artist} - {album} ({year})",
    "[{year}] {artist}",
    "{genre} - {artist} ({year})",
]

print("Testing folder template functionality")
print("=" * 60)

for template in test_templates:
    print(f"\nTemplate: {template}")

    # Step 1: Apply template (what preview shows)
    applied = apply_folder_template(template, test_metadata)
    print(f"  After applying template: {applied}")

    # Step 2: Sanitize (what actual folder name becomes)
    sanitized = sanitize_folder_name(applied)
    print(f"  After sanitizing:        {sanitized}")

    # Check if they match
    if applied == sanitized:
        print(f"  [PASS] Preview matches actual folder name")
    else:
        print(f"  [FAIL] Preview does NOT match actual folder name!")
        print(f"      Expected: {applied}")
        print(f"      Got:      {sanitized}")

print("\n" + "=" * 60)
print("\nExpected behavior:")
print("  - Parentheses () should be preserved")
print("  - Square brackets [] should be preserved")
print("  - Other safe punctuation should be preserved")

# Additional edge case tests
print("\n\nEdge case tests:")
print("=" * 60)

edge_cases = [
    ("The World Doesn't Work", "Album with apostrophe"),
    ("Coast To Coast (2018)", "Album with parentheses"),
    ("AC/DC - Back in Black", "Album with slash (should convert to underscore)"),
    ("Songs: Greatest Hits", "Album with colon (should convert to underscore)"),
    ("Live @ Festival", "Album with @ symbol"),
    ("Best of [Deluxe Edition]", "Album with square brackets"),
]

for test_input, description in edge_cases:
    result = sanitize_folder_name(test_input)
    print(f"\n{description}:")
    print(f"  Input:  {test_input}")
    print(f"  Output: {result}")

print("\n" + "=" * 60)
