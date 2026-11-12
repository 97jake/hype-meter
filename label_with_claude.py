"""Bulk-label game posts for sentiment using Claude Haiku 4.5 via the Batches API.

Two modes:
    --mode validate   Label the same posts already in labeled_data/sports_labels.csv
                       (the user's hand labels) and report agreement — run this first.
    --mode bulk       Label every tagged post across games.py that isn't already in
                       labeled_data/sports_labels.csv, writing results to
                       labeled_data/claude_labels.csv.
"""

import argparse
import hashlib
import json
import os
import time

import anthropic
import pandas as pd
from dotenv import load_dotenv

from fetch_bluesky import fetch_game
from games import GAMES

load_dotenv()

MODEL = "claude-haiku-4-5"
SCHEMA = {
    "type": "object",
    "properties": {"label": {"type": "string", "enum": ["positive", "neutral", "negative"]}},
    "required": ["label"],
    "additionalProperties": False,
}
INSTRUCTIONS = (
    "Classify this social media post about an NFL game by its main purpose.\n\n"
    "- positive: the post's main purpose is to express support, excitement, or pride "
    "about a team or the game\n"
    "- negative: the post's main purpose is to express dislike, criticism, or "
    "frustration about a team or the game\n"
    "- neutral: purely informational/factual, or no clear supportive or critical lean\n\n"
)

# Hand-picked from labeled_data/sports_labels.csv, weighted toward the cases Claude got
# wrong in earlier validation rounds (mainly: banter/trash-talk/officiating gripes that
# read negative in tone but aren't genuine anger -> human labeled neutral). These exact
# post_ids are excluded from `--mode validate` below so validation never tests on an
# example the model was shown.
FEW_SHOT_EXAMPLES = [
    ("Are the broncos…. Bad? Lol", "negative"),
    ("WTH is the Rams secondary doing?", "negative"),
    (
        "Rams should have been up 4 touchdowns, but that does not excuse such an obviously "
        "ridiculous call in crunch time.  Despite all the Rams failures, that singular call "
        "ended up deciding this game.",
        "negative",
    ),
    ("FAT KICKER. RAMS HAVE A FAT KICKER.", "neutral"),
    ("Why do the Broncos keep passing it?", "neutral"),
    ("And another flag on the Rams", "neutral"),
    ("We play the rams next week in a 1 PM game lmao.", "neutral"),
    (
        "The Rams ran more than twice as many plays as the Broncos in the first half -- 46 to "
        "21. All five Rams series had multiple first downs. Meanwhile, the Broncos went "
        "three-and-out twice in four possessions.",
        "neutral",
    ),
    ("Go Broncos!", "positive"),
    ("LET'S FUCKING GO BRONCOS!", "positive"),
    (
        "Damn the Broncos really came back to be the Rams like that, what a crazy week for football",
        "positive",
    ),
    (
        "Altitude sickness or absolute masterclass? Matthew Stafford and the Rams roll into "
        "Mile High to take on Bo Nix and the Broncos in a high-stakes NFL Sunday prime-time "
        "showdown. Who takes this West Coast clash? \U0001f3c8\U0001f525 #NFL #BroncosVsRams",
        "positive",
    ),
]
FEW_SHOT_TEXTS = {body for body, _ in FEW_SHOT_EXAMPLES}

_examples_block = "\n\n".join(f'Post: "{body}"\nLabel: {label}' for body, label in FEW_SHOT_EXAMPLES)
PROMPT = INSTRUCTIONS + "Examples:\n\n" + _examples_block + '\n\nPost: "{body}"\nLabel:'


def short_id(post_id: str) -> str:
    """Batches API caps custom_id at 64 chars; Bluesky AT-URIs run longer."""
    return hashlib.sha1(post_id.encode()).hexdigest()[:16]


def build_requests(df: pd.DataFrame):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    id_map = {}
    requests = []
    for row in df.itertuples():
        sid = short_id(row.post_id)
        id_map[sid] = row.post_id
        requests.append(
            Request(
                custom_id=sid,
                params=MessageCreateParamsNonStreaming(
                    model=MODEL,
                    max_tokens=50,
                    output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
                    messages=[{"role": "user", "content": PROMPT.format(body=row.body)}],
                ),
            )
        )
    return requests, id_map


def run_batch(client: anthropic.Anthropic, df: pd.DataFrame) -> dict[str, str]:
    requests, id_map = build_requests(df)
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch {batch.id} created, {len(requests)} requests. Polling...")

    while True:
        batch = client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        print(f"  status={batch.processing_status} processing={batch.request_counts.processing}")
        time.sleep(15)

    print(f"Batch done. Succeeded={batch.request_counts.succeeded} Errored={batch.request_counts.errored}")

    labels = {}
    for result in client.messages.batches.results(batch.id):
        if result.result.type != "succeeded":
            continue
        text = next((b.text for b in result.result.message.content if b.type == "text"), None)
        if not text:
            continue
        try:
            labels[id_map[result.custom_id]] = json.loads(text)["label"]
        except (json.JSONDecodeError, KeyError):
            continue
    return labels


def load_all_tagged() -> pd.DataFrame:
    frames = [fetch_game(g) for g in GAMES]
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["validate", "bulk"], required=True)
    args = parser.parse_args()

    client = anthropic.Anthropic()

    if args.mode == "validate":
        human = pd.read_csv("labeled_data/sports_labels.csv")
        human = human[human["label"] != "off_topic"].copy()
        human = human[~human["body"].isin(FEW_SHOT_TEXTS)].copy()
        print(f"Excluded {len(FEW_SHOT_TEXTS)} few-shot example texts from validation; {len(human)} remain")
        claude_labels = run_batch(client, human)

        human["claude_label"] = human["post_id"].map(claude_labels)
        matched = human.dropna(subset=["claude_label"])
        agreement = (matched["label"] == matched["claude_label"]).mean()

        print(f"\n{len(matched)}/{len(human)} posts labeled by Claude")
        print(f"Agreement with human labels: {agreement:.1%}")
        print("\nConfusion (human -> claude):")
        print(pd.crosstab(matched["label"], matched["claude_label"]))

        os.makedirs("labeled_data", exist_ok=True)
        matched.to_csv("labeled_data/validation_comparison.csv", index=False)
        print("\nSaved labeled_data/validation_comparison.csv")

    else:
        human = pd.read_csv("labeled_data/sports_labels.csv")
        already_labeled = set(human["post_id"].astype(str))

        all_tagged = load_all_tagged()
        to_label = all_tagged[~all_tagged["post_id"].astype(str).isin(already_labeled)].drop_duplicates("post_id")
        print(f"{len(to_label)} posts to label (of {len(all_tagged)} total tagged)")

        claude_labels = run_batch(client, to_label)

        rows = [
            {"post_id": pid, "body": body, "label": claude_labels[pid]}
            for pid, body in zip(to_label["post_id"], to_label["body"])
            if pid in claude_labels
        ]
        out = pd.DataFrame(rows)
        os.makedirs("labeled_data", exist_ok=True)
        out.to_csv("labeled_data/claude_labels.csv", index=False)
        print(f"Labeled {len(out)} posts -> labeled_data/claude_labels.csv")
        print(out["label"].value_counts())


if __name__ == "__main__":
    main()
