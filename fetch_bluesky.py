"""Fetch and cache Bluesky posts for a game window.

Unauthenticated searchPosts (api.bsky.app) allows one page (~100 results) per
request and 403s on any cursor param, so we slice the search window into small
time chunks and take the first page of each instead of paginating.
"""

import os
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from teams import tag_teams

SEARCH_URL = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"


def search_team_posts(query, since, until, chunk=pd.Timedelta(minutes=10)):
    posts = []
    t = since
    while t < until:
        t2 = min(t + chunk, until)
        params = {
            "q": query,
            "since": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "until": t2.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "limit": 100,
            "sort": "latest",
        }
        resp = requests.get(SEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
        posts.extend(resp.json().get("posts", []))
        t = t2
    return posts


def fetch_game(game, pregame_minutes=15, postgame_hours=4.5, cache_dir="data_cache"):
    """Fetch (or load cached) tagged posts for a game dict from games.py."""
    cache_path = os.path.join(cache_dir, f"{game['slug']}.parquet")

    if os.path.exists(cache_path):
        posts_df = pd.read_parquet(cache_path)
    else:
        kickoff_utc = game["kickoff"].astimezone(ZoneInfo("UTC"))
        since = pd.Timestamp(kickoff_utc) - pd.Timedelta(minutes=pregame_minutes)
        until = pd.Timestamp(kickoff_utc) + pd.Timedelta(hours=postgame_hours)

        raw_posts = []
        for query in game["queries"].values():
            raw_posts.extend(search_team_posts(query, since, until))

        by_uri = {
            p["uri"]: {"post_id": p["uri"], "body": p["record"]["text"], "created_at": p["record"]["createdAt"]}
            for p in raw_posts
        }
        posts_df = pd.DataFrame(by_uri.values())
        if posts_df.empty:
            posts_df = pd.DataFrame(columns=["post_id", "body", "created_at", "minutes_since_kickoff"])
        else:
            posts_df["created_at"] = pd.to_datetime(posts_df["created_at"], utc=True, format="mixed")
            posts_df["minutes_since_kickoff"] = (
                posts_df["created_at"] - pd.Timestamp(kickoff_utc)
            ).dt.total_seconds() / 60.0

        os.makedirs(cache_dir, exist_ok=True)
        posts_df.to_parquet(cache_path, index=False)

    posts_df["teams_mentioned"] = posts_df["body"].apply(lambda t: tag_teams(t, game["teams"]))
    posts_df["n_teams"] = posts_df["teams_mentioned"].apply(len)
    tagged_df = posts_df[posts_df["n_teams"] == 1].copy()
    tagged_df["team"] = tagged_df["teams_mentioned"].apply(lambda t: t[0])
    tagged_df["game_slug"] = game["slug"]
    return tagged_df
