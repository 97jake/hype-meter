"""Per-team keyword lists for tagging which NFL team(s) a comment is about.

Usage for a specific game thread (recommended): only tag against the two
teams actually playing, e.g. `tag_teams(text, ["KC", "BUF"])`. Checking all 32
teams at once on a comment about one game invites false positives, since many
nicknames (Bills, Jets, Saints, ...) are also common English words.
"""

import re

TEAMS = {
    "ARI": {"city": ["arizona"], "nickname": ["cardinals", "cards"], "aliases": ["az"]},
    "ATL": {"city": ["atlanta"], "nickname": ["falcons"], "aliases": ["atl"]},
    "BAL": {"city": ["baltimore"], "nickname": ["ravens"], "aliases": ["bal"]},
    "BUF": {"city": ["buffalo"], "nickname": ["bills"], "aliases": ["buf"]},
    "CAR": {"city": ["carolina"], "nickname": ["panthers"], "aliases": ["car"]},
    "CHI": {"city": ["chicago"], "nickname": ["bears"], "aliases": ["chi"]},
    "CIN": {"city": ["cincinnati"], "nickname": ["bengals"], "aliases": ["cin"]},
    "CLE": {"city": ["cleveland"], "nickname": ["browns"], "aliases": ["cle"]},
    "DAL": {"city": ["dallas"], "nickname": ["cowboys"], "aliases": ["dal"]},
    "DEN": {"city": ["denver"], "nickname": ["broncos"], "aliases": ["den"]},
    "DET": {"city": ["detroit"], "nickname": ["lions"], "aliases": ["det"]},
    "GB": {"city": ["green bay"], "nickname": ["packers"], "aliases": ["gb", "gbp"]},
    "HOU": {"city": ["houston"], "nickname": ["texans"], "aliases": ["hou"]},
    "IND": {"city": ["indianapolis"], "nickname": ["colts"], "aliases": ["ind"]},
    "JAX": {"city": ["jacksonville"], "nickname": ["jaguars", "jags"], "aliases": ["jax"]},
    "KC": {"city": ["kansas city"], "nickname": ["chiefs"], "aliases": ["kc"]},
    "LAC": {"city": ["los angeles", "la"], "nickname": ["chargers"], "aliases": ["lac"]},
    "LAR": {"city": ["los angeles", "la"], "nickname": ["rams"], "aliases": ["lar"]},
    "LV": {"city": ["las vegas"], "nickname": ["raiders"], "aliases": ["lv"]},
    "MIA": {"city": ["miami"], "nickname": ["dolphins", "fins"], "aliases": ["mia"]},
    "MIN": {"city": ["minnesota"], "nickname": ["vikings", "vikes"], "aliases": ["min"]},
    "NE": {"city": ["new england"], "nickname": ["patriots", "pats"], "aliases": ["ne"]},
    "NO": {"city": ["new orleans"], "nickname": ["saints"], "aliases": ["no"]},
    "NYG": {"city": ["new york"], "nickname": ["giants"], "aliases": ["nyg"]},
    "NYJ": {"city": ["new york"], "nickname": ["jets"], "aliases": ["nyj"]},
    "PHI": {"city": ["philadelphia", "philly"], "nickname": ["eagles"], "aliases": ["phi"]},
    "PIT": {"city": ["pittsburgh"], "nickname": ["steelers"], "aliases": ["pit"]},
    "SEA": {"city": ["seattle"], "nickname": ["seahawks", "hawks"], "aliases": ["sea"]},
    "SF": {"city": ["san francisco"], "nickname": ["49ers", "niners"], "aliases": ["sf"]},
    "TB": {"city": ["tampa bay", "tampa"], "nickname": ["buccaneers", "bucs"], "aliases": ["tb"]},
    "TEN": {"city": ["tennessee"], "nickname": ["titans"], "aliases": ["ten"]},
    "WAS": {"city": ["washington"], "nickname": ["commanders"], "aliases": ["was"]},
}


def build_team_pattern(abbr: str, extra_terms: list[str] | None = None) -> re.Pattern:
    """Compile a case-insensitive, word-boundary regex matching any alias for a team."""
    team = TEAMS[abbr]
    terms = list(team["city"]) + list(team["nickname"]) + list(team["aliases"])
    if extra_terms:
        terms += extra_terms
    escaped = sorted({re.escape(t) for t in terms}, key=len, reverse=True)
    pattern = r"\b(" + "|".join(escaped) + r")\b"
    return re.compile(pattern, re.IGNORECASE)


def tag_teams(text: str, team_abbrs: list[str], extra_terms: dict[str, list[str]] | None = None) -> list[str]:
    """Return the subset of team_abbrs mentioned in text.

    extra_terms: optional {abbr: [player_surnames, ...]} to widen matching for a
    specific game (e.g. key skill-position players fans refer to by last name).
    """
    extra_terms = extra_terms or {}
    matched = []
    for abbr in team_abbrs:
        pattern = build_team_pattern(abbr, extra_terms.get(abbr))
        if pattern.search(text):
            matched.append(abbr)
    return matched
