"""Copy the files the models just produced from work/ into data/, which the website reads.

A sport's files are only replaced if its notebook finished without errors and the new
files have the columns the website expects. Otherwise the previous files stay in place.
Also writes data/last_updated.json so the site can show when each sport was refreshed.

Usage: CBB_OUTCOME=success NFL_OUTCOME=failure python scripts/publish.py
"""
import json
import os
import shutil
import sys
from datetime import datetime, timezone

import pandas as pd

WORK, DATA = "work", "data"

SPORTS = {
    "cbb": {
        "outcome_env": "CBB_OUTCOME",
        "picks": ("cbb_upcoming_picks.csv", ["tipoff_utc", "matchup", "pick", "price", "provider", "market_prob",
                                             "model_prob", "final_prob", "edge", "ev", "lean"], "lean"),
        "ratings": ("cbb_team_ratings.csv", ["rank", "team", "conference", "games", "offense", "defense",
                                             "tempo", "elo", "net"]),
    },
    "nfl": {
        "outcome_env": "NFL_OUTCOME",
        "picks": ("nfl_upcoming_picks.csv", ["gameday", "matchup", "market", "pick", "price", "market_prob",
                                             "model_prob", "raw_prob", "edge", "ev", "confidence",
                                             "track_record", "model_lean"], "model_lean"),
        "ratings": ("nfl_team_ratings.csv", ["team", "elo", "pass_offense", "rush_offense", "pass_defense",
                                             "rush_defense", "points_for", "points_against", "quarterback",
                                             "qb_rating"]),
    },
}


def has_columns(path, columns):
    df = pd.read_csv(path)
    missing = [c for c in columns if c not in df.columns]
    return df, missing


def publish_sport(name, spec, now):
    outcome = os.environ.get(spec["outcome_env"], "skipped")
    status = {"status": "not updated", "notebook": outcome}
    if outcome != "success":
        print(f"{name}: notebook {outcome}, keeping the previous files.")
        return status, outcome == "failure"

    ratings_file, ratings_cols = spec["ratings"]
    picks_file, picks_cols, lean_col = spec["picks"]
    src_ratings = os.path.join(WORK, ratings_file)
    if not os.path.exists(src_ratings):
        print(f"{name}: {ratings_file} was not produced, keeping the previous files.")
        return status, True
    ratings, missing = has_columns(src_ratings, ratings_cols)
    if missing or len(ratings) == 0:
        print(f"{name}: {ratings_file} is empty or missing columns {missing}, keeping the previous files.")
        return status, True

    src_picks = os.path.join(WORK, picks_file)
    if os.path.exists(src_picks):
        picks, missing = has_columns(src_picks, picks_cols)
        if missing:
            print(f"{name}: {picks_file} is missing columns {missing}, keeping the previous files.")
            return status, True
        shutil.copy(src_picks, os.path.join(DATA, picks_file))
    else:
        # The notebook skips the file when no upcoming game has a line yet.
        # Publish an empty table so the site shows "no games" instead of old picks.
        picks = pd.DataFrame(columns=picks_cols)
        picks.to_csv(os.path.join(DATA, picks_file), index=False)
    shutil.copy(src_ratings, os.path.join(DATA, ratings_file))

    status.update({
        "status": "updated",
        "updated_utc": now,
        "upcoming_rows": int(len(picks)),
        "leans": int((picks[lean_col] == "LEAN").sum()) if len(picks) else 0,
        "teams_rated": int(len(ratings)),
    })
    print(f"{name}: published {len(picks)} pick rows ({status['leans']} leans) and {len(ratings)} team ratings.")
    return status, False


def main():
    os.makedirs(DATA, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    stamp_path = os.path.join(DATA, "last_updated.json")
    previous = {}
    if os.path.exists(stamp_path):
        with open(stamp_path) as f:
            previous = json.load(f)

    stamp, problems = {"checked_utc": now}, []
    for name, spec in SPORTS.items():
        status, problem = publish_sport(name, spec, now)
        if status["status"] != "updated" and "updated_utc" in previous.get(name, {}):
            status["updated_utc"] = previous[name]["updated_utc"]   # keep the last good time
        stamp[name] = status
        if problem:
            problems.append(name)

    with open(stamp_path, "w") as f:
        json.dump(stamp, f, indent=2)
    if problems:
        print(f"Problems with: {', '.join(problems)}. See the log above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
