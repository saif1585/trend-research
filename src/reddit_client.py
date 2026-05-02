"""Reddit API client wrapper.

Handles OAuth2 authentication, User-Agent compliance, rate limiting,
and exponential backoff per Reddit's Responsible Builder Policy.
"""

import os
import time
import logging
from typing import Optional
import praw
from prawcore.exceptions import TooManyRequests, ServerError

logger = logging.getLogger(__name__)


class RedditClient:
    """Thin wrapper around PRAW with rate-limit awareness."""

    # Conservative QPM target — well under Reddit's 100 QPM free-tier limit
    TARGET_QPM = 40
    MIN_REQUEST_INTERVAL = 60.0 / TARGET_QPM  # ~1.5s between requests

    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            username=os.environ["REDDIT_USERNAME"],
            password=os.environ["REDDIT_PASSWORD"],
            user_agent=os.environ["REDDIT_USER_AGENT"],
        )
        self.reddit.read_only = False  # script-type, but we never write
        self._last_request_ts: Optional[float] = None

    def _throttle(self) -> None:
        """Enforce minimum interval between requests."""
        if self._last_request_ts is None:
            self._last_request_ts = time.time()
            return
        elapsed = time.time() - self._last_request_ts
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_ts = time.time()

    def _with_backoff(self, func, *args, max_retries: int = 5, **kwargs):
        """Call a PRAW method with exponential backoff on 429/5xx."""
        for attempt in range(max_retries):
            try:
                self._throttle()
                return func(*args, **kwargs)
            except TooManyRequests:
                wait = 2 ** attempt
                logger.warning(f"429 received — backing off {wait}s")
                time.sleep(wait)
            except ServerError:
                wait = 2 ** attempt
                logger.warning(f"5xx error — backing off {wait}s")
                time.sleep(wait)
        raise RuntimeError(f"Exceeded {max_retries} retries")

    def get_subreddit_about(self, name: str):
        """Fetch /r/{name}/about.json (subscriber count, etc.)."""
        sub = self.reddit.subreddit(name)
        return self._with_backoff(lambda: {
            "name": sub.display_name,
            "subscribers": sub.subscribers,
            "active_user_count": sub.active_user_count,
            "created_utc": sub.created_utc,
        })

    def get_rising(self, name: str, limit: int = 25):
        """Fetch /r/{name}/rising.json."""
        sub = self.reddit.subreddit(name)
        return self._with_backoff(lambda: list(sub.rising(limit=limit)))

    def get_hot(self, name: str, limit: int = 25):
        """Fetch /r/{name}/hot.json."""
        sub = self.reddit.subreddit(name)
        return self._with_backoff(lambda: list(sub.hot(limit=limit)))

    def get_new(self, name: str, limit: int = 50):
        """Fetch /r/{name}/new.json — for post velocity baseline."""
        sub = self.reddit.subreddit(name)
        return self._with_backoff(lambda: list(sub.new(limit=limit)))
