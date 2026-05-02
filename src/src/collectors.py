"""Scheduled collectors for subreddit-level metadata.

All collectors are read-only and aggregate at the subreddit level only.
No user-level data is collected, stored, or processed.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from src.reddit_client import RedditClient

logger = logging.getLogger(__name__)


def collect_about(client: RedditClient, subreddits: List[str]) -> List[Dict[str, Any]]:
    """Daily collection: subscriber counts and basic subreddit metadata."""
    results = []
    ts = datetime.now(timezone.utc).isoformat()
    for name in subreddits:
        try:
            data = client.get_subreddit_about(name)
            data["collected_at"] = ts
            results.append(data)
        except Exception as e:
            logger.error(f"Failed to fetch about for r/{name}: {e}")
    return results


def collect_listing_signal(
    client: RedditClient,
    subreddits: List[str],
    listing: str = "rising",
) -> List[Dict[str, Any]]:
    """2-4x daily: trending post signals (rising or hot listings).

    Stores only post-level metadata: id, title, score, num_comments,
    created_utc, subreddit. No author identifiers, no body content.
    """
    results = []
    ts = datetime.now(timezone.utc).isoformat()
    fetch = client.get_rising if listing == "rising" else client.get_hot

    for name in subreddits:
        try:
            posts = fetch(name)
            for p in posts:
                results.append({
                    "post_id": p.id,
                    "subreddit": name,
                    "listing": listing,
                    "title": p.title,
                    "score": p.score,
                    "num_comments": p.num_comments,
                    "created_utc": p.created_utc,
                    "collected_at": ts,
                })
        except Exception as e:
            logger.error(f"Failed to fetch {listing} for r/{name}: {e}")
    return results


def collect_post_velocity(
    client: RedditClient,
    subreddits: List[str],
) -> List[Dict[str, Any]]:
    """Hourly: post velocity baseline from /new listings.

    Used to compute posts-per-hour rate per subreddit, which is the
    primary signal for detecting topic surges.
    """
    results = []
    ts = datetime.now(timezone.utc).isoformat()
    for name in subreddits:
        try:
            posts = client.get_new(name)
            results.append({
                "subreddit": name,
                "post_count_window": len(posts),
                "earliest_created_utc": min(p.created_utc for p in posts) if posts else None,
                "latest_created_utc": max(p.created_utc for p in posts) if posts else None,
                "collected_at": ts,
            })
        except Exception as e:
            logger.error(f"Failed to fetch velocity for r/{name}: {e}")
    return results
