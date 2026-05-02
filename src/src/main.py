"""Entry point for the trend-research collector.

Run modes:
    python main.py --mode daily      # /about collection
    python main.py --mode listings   # /rising and /hot
    python main.py --mode velocity   # /new for post-velocity baseline
"""

import argparse
import logging
from dotenv import load_dotenv

from src.reddit_client import RedditClient
from src.collectors import (
    collect_about,
    collect_listing_signal,
    collect_post_velocity,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Subreddit registry — actual list maintained in config/subreddits.yml
DEFAULT_SUBREDDITS = [
    "productivity",
    "getdisciplined",
    "personalfinance",
    "Fitness",
    "Entrepreneur",
    # ...full list loaded from config at runtime
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["daily", "listings", "velocity"],
        required=True,
    )
    args = parser.parse_args()

    load_dotenv()
    client = RedditClient()

    if args.mode == "daily":
        results = collect_about(client, DEFAULT_SUBREDDITS)
        logger.info(f"Collected /about for {len(results)} subreddits")
    elif args.mode == "listings":
        rising = collect_listing_signal(client, DEFAULT_SUBREDDITS, "rising")
        hot = collect_listing_signal(client, DEFAULT_SUBREDDITS, "hot")
        logger.info(f"Collected {len(rising)} rising + {len(hot)} hot posts")
    elif args.mode == "velocity":
        results = collect_post_velocity(client, DEFAULT_SUBREDDITS)
        logger.info(f"Collected velocity for {len(results)} subreddits")


if __name__ == "__main__":
    main()
