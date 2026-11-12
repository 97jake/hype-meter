# Hype Meter: team-specific sentiment over the course of an NFL game

Pulls Bluesky posts from the window around a completed NFL game, tags each post by which team it's about, scores "hype" with two sentiment models, and plots average hype over the course of the game — e.g. showing a losing team's sentiment craters and then spikes on a dramatic comeback.

## Pipeline

1. **`fetch_bluesky.py`** — pulls posts mentioning either team from Bluesky's public search, sliced into small time windows around kickoff to work around the unauthenticated API's pagination limits. Results are cached per-game in `data_cache/`.
2. **`teams.py` / `games.py`** — team metadata and the registry of games pulled for the dataset (slug, teams, search queries, kickoff time).
3. **`label_comments.py`** — a small CLI for hand-labeling a sample of posts as positive/neutral/negative, used to build ground truth.
4. **`label_with_claude.py`** — labels posts in bulk with Claude Haiku via the Anthropic Batches API, and can validate against the hand labels first (`--mode validate` vs `--mode bulk`). Labeled output lives in `labeled_data/`.
5. **`hype_meter.ipynb`** — ties it together: scores posts with a generic sentiment baseline vs. a sports-tuned model, bins by time, and plots per-team hype over the game.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
jupyter lab hype_meter.ipynb
```

## Notes

Originally designed around Reddit game threads, but switched to Bluesky after Reddit's Responsible Builder Policy (Nov 2025) made self-serve API access impractical.
