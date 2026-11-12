"""Registry of games pulled for the hype meter dataset."""

from datetime import datetime
from zoneinfo import ZoneInfo

GAMES = [
    {
        "slug": "den_lar_2026-09-27",
        "teams": ["DEN", "LAR"],
        "queries": {"DEN": "Broncos", "LAR": "Rams"},
        "kickoff": datetime(2026, 9, 27, 18, 20, tzinfo=ZoneInfo("America/Denver")),
        "note": "Broncos down 16-0 at half, won 30-26 (SNF)",
    },
    {
        "slug": "lv_no_2026-09-27",
        "teams": ["LV", "NO"],
        "queries": {"LV": "Raiders", "NO": "Saints"},
        "kickoff": datetime(2026, 9, 27, 15, 25, tzinfo=ZoneInfo("America/New_York")),
        "note": "Raiders down 11, won 35-27",
    },
    {
        "slug": "ari_nyg_2026-10-04",
        "teams": ["ARI", "NYG"],
        "queries": {"ARI": "Cardinals", "NYG": "Giants"},
        "kickoff": datetime(2026, 10, 4, 13, 0, tzinfo=ZoneInfo("America/New_York")),
        "note": "Giants erased an 11-point deficit, won 36-24",
    },
    {
        "slug": "ne_buf_2026-10-04",
        "teams": ["NE", "BUF"],
        "queries": {"NE": "Patriots", "BUF": "Bills"},
        "kickoff": datetime(2026, 10, 4, 13, 0, tzinfo=ZoneInfo("America/New_York")),
        "note": "Patriots held off a late Bills rally, won 29-26",
    },
    {
        "slug": "bal_atl_2026-10-11",
        "teams": ["BAL", "ATL"],
        "queries": {"BAL": "Ravens", "ATL": "Falcons"},
        "kickoff": datetime(2026, 10, 11, 20, 20, tzinfo=ZoneInfo("America/New_York")),
        "note": "Ravens blew an 8-point 4th-quarter lead, won in OT 30-23 (SNF)",
    },
]
