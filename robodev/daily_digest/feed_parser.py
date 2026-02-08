import feedparser
import requests
import time
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
import json

CACHE_DIR = Path.home() / ".robodev" / "news"

# Curated RSS feeds for robotics + AI
DEFAULT_FEEDS = [
    # ArXiv - Robotics
    "https://rss.arxiv.org/rss/cs.RO",
    # ArXiv - AI
    "https://rss.arxiv.org/rss/cs.AI",
    # ArXiv - Computer Vision (perception)
    "https://rss.arxiv.org/rss/cs.CV",
    # IEEE Spectrum Robotics
    "https://spectrum.ieee.org/feeds/topic/robotics.rss",
    # The Robot Report
    "https://www.therobotreport.com/feed/",
    # ROS Discourse
    "https://discourse.ros.org/latest.rss",
    # Hacker News (filtered later)
    "https://hnrss.org/newest?q=robotics+OR+ros2+OR+slam+OR+manipulation",
]


@dataclass
class Article:
    title: str
    url: str
    source: str
    summary: str = ""
    published: str = ""
    relevance_score: float = 0.0


def fetch_feeds(feeds: Optional[List[str]] = None, max_per_feed: int = 15) -> List[Article]:
    feeds = feeds or DEFAULT_FEEDS
    articles = []
    for feed_url in feeds:
        try:
            d = feedparser.parse(feed_url)
            source = d.feed.get("title", feed_url)
            for entry in d.entries[:max_per_feed]:
                articles.append(Article(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    source=source,
                    summary=entry.get("summary", "")[:500],
                    published=entry.get("published", ""),
                ))
        except Exception as e:
            print(f"⚠ Failed to fetch {feed_url}: {e}")
    return articles


def _cache_path(date_str: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"digest_{date_str}.json"


def save_digest(date_str: str, digest: dict):
    path = _cache_path(date_str)
    path.write_text(json.dumps(digest, indent=2))


def load_digest(date_str: str) -> Optional[dict]:
    path = _cache_path(date_str)
    if path.exists():
        return json.loads(path.read_text())
    return None