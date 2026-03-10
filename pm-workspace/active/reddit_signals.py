"""Fetch Reddit posts and comments about Amion for PM signal research.

Usage:
  # Fetch a specific post + search for more:
  python3 active/reddit_signals.py

  # Fetch a specific post URL only:
  python3 active/reddit_signals.py https://reddit.com/r/Residency/comments/13tjdzs/amion_scheduler/

Output is printed to terminal. Pipe to a file to save:
  python3 active/reddit_signals.py | tee active/reddit_signals_output.txt
"""

from __future__ import annotations

import re
import sys
import time
from datetime import datetime

import requests

HEADERS = {"User-Agent": "AmionPMResearch/1.0 (internal product research; not scraping)"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# Subreddits + search terms to pull from
SEARCHES = [
    # Core residency subreddits
    ("Residency",               "amion"),
    ("Residency",               "amion scheduler"),
    ("Residency",               "amion scheduling"),
    ("Residency",               "scheduling software"),
    ("Residency",               "qgenda amion"),
    ("Residency",               "medhub amion"),
    # Medical school + broad medicine
    ("medicalschool",           "amion"),
    ("medicalschool",           "residency scheduling software"),
    ("medicine",                "amion"),
    ("medicine",                "amion scheduling"),
    # Specialty residency subreddits
    ("emergencymedicine",       "amion"),
    ("emergencymedicine",       "scheduling software"),
    ("Anesthesia",              "amion"),
    ("Anesthesia",              "scheduling software"),
    ("neurology",               "amion"),
    ("neurology",               "scheduling software"),
    ("surgery",                 "amion"),
    ("surgery",                 "scheduling software"),
    ("Radiology",               "amion"),
    ("FamilyMedicine",          "amion"),
    ("FamilyMedicine",          "scheduling software"),
    ("Psychiatry",              "amion"),
    ("IMResident",              "amion"),
    ("IMResident",              "scheduling software"),
    ("hospitalist",             "amion"),
    # Additional residency-adjacent communities
    ("ObGyn",                   "amion"),
    ("Pediatrics",              "amion"),
    ("orthopedics",             "amion"),
    ("Dermatology",             "amion"),
    ("urology",                 "amion"),
    ("PathologyResidents",      "amion"),
    ("medicalresidents",        "amion"),
    ("chiefresidents",          "amion"),
    ("physicianassistant",      "amion"),
]

MAX_POSTS_PER_SEARCH = 10   # top posts per search query
MAX_COMMENTS_PER_POST = 20  # top-level comments to show per post
MIN_POST_SCORE = 2          # skip posts with very few upvotes


# ── helpers ───────────────────────────────────────────────────────────────────

def _get(url: str, params: dict | None = None) -> dict:
    resp = SESSION.get(url, params=params, timeout=15)
    resp.raise_for_status()
    time.sleep(0.7)  # be polite
    return resp.json()


def fmt_date(utc_ts: float) -> str:
    return datetime.utcfromtimestamp(utc_ts).strftime("%Y-%m-%d")


def clean(text: str | None, maxlen: int = 500) -> str:
    if not text:
        return ""
    text = text.strip().replace("\n\n", " / ").replace("\n", " ")
    return text[:maxlen] + ("…" if len(text) > maxlen else "")


def divider(char: str = "─", width: int = 72) -> str:
    return char * width


# ── fetchers ─────────────────────────────────────────────────────────────────

def fetch_post(url: str) -> dict | None:
    """Fetch a single Reddit post and its comments from a URL."""
    # Normalise: strip trailing slash, force .json
    url = url.rstrip("/")
    if not url.endswith(".json"):
        url += ".json"
    url = url.replace("http://", "https://").replace(
        "https://reddit.com", "https://www.reddit.com"
    )
    try:
        data = _get(url, params={"limit": 200, "depth": 1})
    except Exception as exc:
        print(f"  [error fetching {url}]: {exc}")
        return None

    post_data = data[0]["data"]["children"][0]["data"]
    comments_raw = data[1]["data"]["children"]

    comments = []
    for c in comments_raw:
        if c["kind"] != "t1":
            continue
        d = c["data"]
        comments.append({
            "body":   d.get("body", ""),
            "score":  d.get("score", 0),
            "author": d.get("author", "[deleted]"),
        })

    # Sort by score descending
    comments.sort(key=lambda x: x["score"], reverse=True)

    return {
        "title":    post_data.get("title", ""),
        "score":    post_data.get("score", 0),
        "date":     fmt_date(post_data.get("created_utc", 0)),
        "url":      f"https://www.reddit.com{post_data.get('permalink', '')}",
        "subreddit": post_data.get("subreddit", ""),
        "selftext": post_data.get("selftext", ""),
        "comments": comments[:MAX_COMMENTS_PER_POST],
        "num_comments": post_data.get("num_comments", 0),
    }


def search_subreddit(subreddit: str, query: str) -> list[dict]:
    """Search a subreddit and return post stubs."""
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    try:
        data = _get(url, params={
            "q":            query,
            "restrict_sr":  1,
            "sort":         "top",
            "t":            "all",
            "limit":        MAX_POSTS_PER_SEARCH,
        })
    except Exception as exc:
        print(f"  [error searching r/{subreddit} for '{query}']: {exc}")
        return []

    posts = []
    for child in data["data"]["children"]:
        d = child["data"]
        if d.get("score", 0) < MIN_POST_SCORE:
            continue
        posts.append({
            "title":      d.get("title", ""),
            "score":      d.get("score", 0),
            "date":       fmt_date(d.get("created_utc", 0)),
            "url":        f"https://www.reddit.com{d.get('permalink', '')}",
            "subreddit":  d.get("subreddit", ""),
            "selftext":   d.get("selftext", ""),
            "num_comments": d.get("num_comments", 0),
            "post_id":    d.get("id", ""),
        })
    return posts


def fetch_comments_for_post(post_stub: dict) -> list[dict]:
    """Fetch top-level comments for a post stub (from search results)."""
    post_id  = post_stub["post_id"]
    subreddit = post_stub["subreddit"]
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
    try:
        data = _get(url, params={"limit": 100, "depth": 1})
    except Exception as exc:
        print(f"  [error fetching comments for {post_id}]: {exc}")
        return []

    comments = []
    for c in data[1]["data"]["children"]:
        if c["kind"] != "t1":
            continue
        d = c["data"]
        comments.append({
            "body":   d.get("body", ""),
            "score":  d.get("score", 0),
            "author": d.get("author", "[deleted]"),
        })
    comments.sort(key=lambda x: x["score"], reverse=True)
    return comments[:MAX_COMMENTS_PER_POST]


# ── printer ───────────────────────────────────────────────────────────────────

def print_post(post: dict) -> None:
    print()
    print(divider("═"))
    print(f"  {post['title']}")
    print(f"  r/{post['subreddit']}  ·  {post['date']}  ·  "
          f"↑{post['score']}  ·  {post['num_comments']} comments")
    print(f"  {post['url']}")
    if post.get("selftext") and post["selftext"] not in ("[removed]", "[deleted]"):
        print(divider())
        print(f"  POST: {clean(post['selftext'], 400)}")
    comments = post.get("comments", [])
    if comments:
        print(divider())
        print("  TOP COMMENTS:")
        for i, c in enumerate(comments, 1):
            body = clean(c["body"], 300)
            if body in ("[removed]", "[deleted]", ""):
                continue
            print(f"  {i:>2}. [↑{c['score']:>3}] {body}")
    print()


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    specific_urls: list[str] = []
    if len(sys.argv) > 1:
        specific_urls = [a for a in sys.argv[1:] if "reddit.com" in a]

    # Always include the post from the brief
    default_post = "https://reddit.com/r/Residency/comments/13tjdzs/amion_scheduler/"
    if default_post not in specific_urls:
        specific_urls.insert(0, default_post)

    print("=" * 72)
    print("  REDDIT SIGNALS — Amion / Residency Scheduling")
    print("=" * 72)

    # 1. Fetch specific posts first
    seen_urls: set[str] = set()
    if specific_urls:
        print(f"\n── PINNED POSTS ({len(specific_urls)}) ──────────────────────────────")
        for url in specific_urls:
            post = fetch_post(url)
            if post:
                seen_urls.add(post["url"])
                print_post(post)

    # 2. Search each subreddit + query combo
    all_stubs: list[dict] = []
    print("\n── SEARCH RESULTS ──────────────────────────────────────────────")
    for subreddit, query in SEARCHES:
        print(f"  Searching r/{subreddit} for '{query}'…")
        stubs = search_subreddit(subreddit, query)
        print(f"    → {len(stubs)} posts found")
        all_stubs.extend(stubs)

    # Deduplicate by URL, then sort by score
    unique_stubs: list[dict] = []
    stub_urls: set[str] = set()
    for s in sorted(all_stubs, key=lambda x: x["score"], reverse=True):
        if s["url"] not in stub_urls and s["url"] not in seen_urls:
            stub_urls.add(s["url"])
            unique_stubs.append(s)

    print(f"\n  {len(unique_stubs)} unique posts after deduplication\n")

    for stub in unique_stubs:
        stub["comments"] = fetch_comments_for_post(stub)
        print_post(stub)
        seen_urls.add(stub["url"])

    print(divider("═"))
    print(f"  Done — {len(seen_urls)} total posts")
    print(divider("═"))


if __name__ == "__main__":
    main()
