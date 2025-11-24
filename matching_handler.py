"""
Matching Handler - Wrapper for spotdl's audio matching algorithms

This module provides access to spotdl's sophisticated matching algorithms
that are used to find the best audio source for a given song.

The matching system considers:
- Artist name similarity
- Song title similarity
- Album name similarity
- Duration matching
- Forbidden words detection (remix, cover, live, etc.)

This can be useful for:
- Verifying download quality
- Custom audio source selection
- Building download previews
- Quality assurance workflows
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Try to import spotdl matching utilities
MATCHING_AVAILABLE = False
Song = None
Result = None
order_results = None
get_best_matches = None
check_forbidden_words = None
FORBIDDEN_WORDS = []

try:
    # Add local spotdl directory to path if it exists
    script_dir = Path(__file__).parent
    spotdl_dir = script_dir / "spotdl"
    if spotdl_dir.exists():
        sys.path.insert(0, str(spotdl_dir))

    # Import matching utilities
    from spotdl.types.song import Song
    from spotdl.types.result import Result
    from spotdl.utils.matching import (
        order_results,
        get_best_matches,
        check_forbidden_words,
        FORBIDDEN_WORDS,
    )

    MATCHING_AVAILABLE = True
    logger.info("✓ Successfully imported spotdl matching utilities")
except ImportError as e:
    logger.warning(f"⚠ Could not import spotdl matching utilities: {e}")


class MatchingHandler:
    """
    Handler for audio matching operations using spotdl's algorithms.

    The matching system uses a sophisticated scoring algorithm that considers:
    - Main artist match (0-100%)
    - Additional artists match (0-100%)
    - Song name match (0-100%)
    - Album match (0-100%, for verified results)
    - Duration match (0-100%, exponential decay)
    - Forbidden words penalties (remix, cover, live, etc.)

    Results are ranked by overall match score, and only results above
    certain thresholds are considered valid matches.
    """

    def __init__(self):
        """Initialize the matching handler"""
        if not MATCHING_AVAILABLE:
            raise ImportError(
                "Spotdl matching utilities are not available. "
                "Ensure spotdl is installed or the source code is present."
            )

    @staticmethod
    def get_forbidden_words() -> List[str]:
        """
        Get the list of forbidden words used in matching.

        These words trigger penalties during matching as they indicate
        modified versions of songs (remixes, covers, live versions, etc.)

        Returns:
            List of forbidden words
        """
        return FORBIDDEN_WORDS.copy()

    def check_forbidden_words(self, song: Song, result: Result) -> Tuple[bool, List[str]]:
        """
        Check if result contains forbidden words not present in the song.

        Args:
            song: Song object to match
            result: Result object to check

        Returns:
            Tuple of (has_forbidden_words, list_of_found_words)
        """
        return check_forbidden_words(song, result)

    def order_results(
        self,
        results: List[Result],
        song: Song,
        search_query: Optional[str] = None
    ) -> Dict[Result, float]:
        """
        Order and score a list of results for a given song.

        This is the main matching algorithm. It calculates match scores
        for each result based on multiple factors and returns them ordered
        by best match.

        Args:
            results: List of Result objects to score
            song: Song object to match against
            search_query: Optional custom search query used to find results

        Returns:
            Dictionary mapping Result objects to their match scores (0-100)
        """
        return order_results(results, song, search_query)

    def get_best_matches(
        self,
        scored_results: Dict[Result, float],
        score_threshold: float = 5.0
    ) -> List[Tuple[Result, float]]:
        """
        Get the best matches from scored results.

        Returns all results within score_threshold of the best score.
        For example, if the best score is 95 and threshold is 5,
        returns all results with scores >= 90.

        Args:
            scored_results: Dictionary of Result -> score from order_results()
            score_threshold: Maximum score difference from best to include

        Returns:
            List of (Result, score) tuples for best matches
        """
        return get_best_matches(scored_results, score_threshold)

    def match_song_to_results(
        self,
        song: Song,
        results: List[Result],
        score_threshold: float = 5.0,
        search_query: Optional[str] = None
    ) -> List[Tuple[Result, float]]:
        """
        Complete matching workflow: score results and get best matches.

        This is a convenience method that combines order_results() and
        get_best_matches() into a single call.

        Args:
            song: Song to match
            results: List of Result objects (audio sources)
            score_threshold: Threshold for best matches (default 5.0)
            search_query: Optional search query

        Returns:
            List of (Result, score) tuples for best matches, ordered by score
        """
        # Score all results
        scored = self.order_results(results, song, search_query)

        if not scored:
            return []

        # Get best matches
        best = self.get_best_matches(scored, score_threshold)

        return best

    @staticmethod
    def format_match_summary(result: Result, score: float, song: Song) -> str:
        """
        Format a human-readable summary of a match.

        Args:
            result: The Result object
            score: The match score (0-100)
            song: The Song being matched

        Returns:
            Formatted string with match details
        """
        summary_lines = [
            f"Match Score: {score:.1f}%",
            f"Source: {result.source}",
            f"Title: {result.name}",
            f"Artists: {', '.join(result.artists) if result.artists else 'Unknown'}",
            f"Duration: {result.duration}s (expected: {song.duration}s)",
            f"Verified: {'Yes' if result.verified else 'No'}",
        ]

        # Check for forbidden words
        has_forbidden, found_words = check_forbidden_words(song, result)
        if has_forbidden:
            summary_lines.append(f"⚠ Contains forbidden words: {', '.join(found_words)}")

        return '\n'.join(summary_lines)


def is_matching_available() -> bool:
    """
    Check if matching functionality is available.

    Returns:
        True if spotdl matching utilities are available
    """
    return MATCHING_AVAILABLE


# Example usage
if __name__ == "__main__":
    import sys
    import io

    # Fix Windows console encoding issues
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    print("\n" + "="*60)
    print("MATCHING HANDLER TEST")
    print("="*60)

    print(f"\nMatching utilities available: {MATCHING_AVAILABLE}")

    if MATCHING_AVAILABLE:
        handler = MatchingHandler()

        print("\nForbidden words used in matching:")
        forbidden = handler.get_forbidden_words()
        print(", ".join(forbidden[:10]) + "..." if len(forbidden) > 10 else ", ".join(forbidden))

        print("\n[OK] Matching handler initialized successfully")
        print("\nNote: To test actual matching, you need Song and Result objects")
        print("This is typically done during the download process")
    else:
        print("\n[ERROR] Matching utilities not available")
        print("Install spotdl or ensure the source code is present")

    print("\n" + "="*60)
