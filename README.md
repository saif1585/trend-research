# trend-research

A personal, read-only research tool that aggregates public metadata from
Reddit, Google Trends, and RSS feeds to identify emerging discussion
topics across communities I follow.

**Status:** in active development

## Scope

This is a personal analytics tool that runs on my own infrastructure.
It is **not** a Reddit-facing app, bot, or service used by other Redditors.

### What it does
- Polls public subreddit-level metadata (subscriber counts, post velocity,
  rising/hot listings) on a fixed schedule
- Aggregates signals into a local time-series database
- Cross-references Reddit signals with Google Trends and RSS feeds
- Surfaces emerging topics for my personal review

### What it does NOT do
- Does not post, comment, vote, message users, or modify Reddit content
- Does not scrape user post histories or build user-level profiles
- Does not store user-level identifying data
- Does not use Reddit content as training data for any model
- Does not republish Reddit content externally

## Technical approach

### Reddit
- OAuth2 script-type authentication (single user: me)
- Descriptive User-Agent per Reddit's Responsible Builder Policy:
  `python:trend-research:v1.0 (by /u/[handle])`
- Endpoints used:
  - `/r/{subreddit}/about.json` — once daily (subscriber counts)
  - `/r/{subreddit}/rising.json` — 2-4× daily (trending posts)
  - `/r/{subreddit}/hot.json` — 2-4× daily (trending posts)
  - `/r/{subreddit}/new.json` — hourly (post velocity baseline)
- Target volume: 30-50 QPM peak (well under the 100 QPM free-tier limit)
- Exponential backoff on 429 responses
- Local response caching to minimize redundant requests

### Infrastructure
- Single instance, runs on a personal Mac Mini at a residential IP
- No cloud-VPS distribution, no API key sharing
- Local SQLite for time-series storage

## Stack
- Python 3.11
- [PRAW](https://praw.readthedocs.io/) — Reddit API client
- SQLite — local storage
- python-dotenv — credential management

## Communities monitored

Approximately 15-25 public subreddits across productivity, personal
finance, health, technology, education, and self-development. Subreddit
list configured in `config/subreddits.yml` (not committed).

## Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in credentials
python main.py
```

## License

MIT
