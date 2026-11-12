"""Resumable CLI tool for hand-labeling game-window posts as pos/neutral/neg.

Run from the project venv:
    python label_comments.py --n 400

By default samples across every game in games.py, stratified evenly per game
so the labeled set stays diverse rather than dominated by whichever game has
the most posts. Pass --data_cache to label a single game's parquet instead
(the original behavior).

Labels are appended to labeled_data/sports_labels.csv as you go, so you can
Ctrl+C and resume later without re-labeling anything.
"""

import argparse
import csv
import os

import pandas as pd

from fetch_bluesky import fetch_game
from games import GAMES

LABELS_PATH = "labeled_data/sports_labels.csv"
LABEL_KEYS = {"p": "positive", "u": "neutral", "n": "negative", "o": "off_topic"}


def load_already_labeled(labels_path: str) -> set[str]:
    if not os.path.exists(labels_path):
        return set()
    return set(pd.read_csv(labels_path)["post_id"].astype(str))


def ensure_labels_file(labels_path: str) -> None:
    os.makedirs(os.path.dirname(labels_path), exist_ok=True)
    if not os.path.exists(labels_path):
        with open(labels_path, "w", newline="") as f:
            csv.writer(f).writerow(["post_id", "body", "label"])


def sample_across_games(n: int, seed: int, already: set[str]) -> pd.DataFrame:
    per_game = max(1, n // len(GAMES))
    chunks = []
    for game in GAMES:
        df = fetch_game(game)
        df = df[~df["post_id"].astype(str).isin(already)]
        chunks.append(df.sample(n=min(per_game, len(df)), random_state=seed))
    pool = pd.concat(chunks, ignore_index=True)
    return pool.sample(frac=1, random_state=seed)  # shuffle so games aren't labeled in blocks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_cache", default=None, help="Label a single game's parquet instead of all games")
    parser.add_argument("--labels_path", default=LABELS_PATH)
    parser.add_argument("--n", type=int, default=400, help="Target sample size to label")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    ensure_labels_file(args.labels_path)
    already = load_already_labeled(args.labels_path)

    if args.data_cache:
        df = pd.read_parquet(args.data_cache)
        df = df[~df["post_id"].astype(str).isin(already)]
        rows = df.sample(n=min(args.n, len(df)), random_state=args.seed).to_dict("records")
    else:
        rows = sample_across_games(args.n, args.seed, already).to_dict("records")

    print(f"{len(already)} already labeled. {len(rows)} queued this session.")
    print("Labels: p=positive  u=neutral  n=negative  o=off-topic (not about football)  s=skip for now  q=quit\n")

    session_counts: dict[str, int] = {}

    def report_and_exit():
        total = sum(session_counts.values())
        if total:
            off_topic = session_counts.get("off_topic", 0)
            print(f"\nThis session: {total} labeled ({off_topic} off-topic, {off_topic / total:.0%}).")
            print(dict(session_counts))

    with open(args.labels_path, "a", newline="") as f:
        writer = csv.writer(f)
        for i, row in enumerate(rows):
            print(f"[{i + 1}/{len(rows)}] {row['body']!r}")
            while True:
                key = input("label (p/u/n/o/s/q): ").strip().lower()
                if key == "q":
                    print("Stopping — progress saved.")
                    report_and_exit()
                    return
                if key == "s":
                    break
                if key in LABEL_KEYS:
                    label = LABEL_KEYS[key]
                    writer.writerow([row["post_id"], row["body"], label])
                    f.flush()
                    session_counts[label] = session_counts.get(label, 0) + 1
                    break
                print("  invalid key, try again")
            print()

    print("Done labeling this batch.")
    report_and_exit()


if __name__ == "__main__":
    main()
