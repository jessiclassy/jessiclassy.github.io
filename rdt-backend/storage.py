import json
import os
import secrets
from datetime import datetime, timezone
import requests
try: # for local testing
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, assume env vars are set manually

GIST_TOKEN = os.environ["GIST_TOKEN"]
GIST_ID = os.environ["GIST_ID"]

HEADERS = {
    "Authorization": f"Bearer {GIST_TOKEN}",
    "Accept": "application/vnd.github+json"
}

GIST_URL = f"https://api.github.com/gists/{GIST_ID}"


# ── Low-level Gist read/write ──────────────────────────────────────────────

def _read_gist():
    """Fetch both files from the Gist. Returns (users, pairings)."""
    r = requests.get(GIST_URL, headers=HEADERS)
    r.raise_for_status()
    files = r.json()["files"]

    users = json.loads(files["users.json"]["content"])
    pairings = json.loads(files["pairings.json"]["content"])
    return users, pairings


def _write_gist(users=None, pairings=None):
    """Write one or both files back to the Gist. Pass None to skip a file."""
    files = {}
    if users is not None:
        files["users.json"] = {"content": json.dumps(users, indent=2)}
    if pairings is not None:
        files["pairings.json"] = {"content": json.dumps(pairings, indent=2)}

    r = requests.patch(GIST_URL, headers=HEADERS, json={"files": files})
    r.raise_for_status()


# ── User helpers ───────────────────────────────────────────────────────────

def _current_week():
    """Returns ISO week string like '2025-W03'."""
    return datetime.now(timezone.utc).strftime("%Y-W%W")


def load_users():
    users, _ = _read_gist()
    return users


def load_pairings():
    _, pairings = _read_gist()
    return pairings


# ── User operations ────────────────────────────────────────────────────────

def add_user(name, email):
    """Sign up a new user. If email exists (was deleted), treat as new."""
    users, _ = _read_gist()

    # Remove any existing user with this email (clean slate)
    users = [u for u in users if u["email"] != email]

    new_user = {
        "id": secrets.token_urlsafe(8),
        "name": name,
        "email": email,
        "joined": datetime.now(timezone.utc).date().isoformat(),
        "opted_out_weeks": []
    }
    users.append(new_user)
    _write_gist(users=users)
    return new_user


def opt_out_week(token):
    """Skip this week only. User is back in automatically next week."""
    users, _ = _read_gist()
    week = _current_week()

    for u in users:
        if u["id"] == token:
            if week not in u["opted_out_weeks"]:
                u["opted_out_weeks"].append(week)
            _write_gist(users=users)
            return u

    return None


def opt_out_forever(token):
    """Permanently leave the group — user is deleted entirely."""
    users, _ = _read_gist()

    for i, u in enumerate(users):
        if u["id"] == token:
            deleted_user = users.pop(i)
            _write_gist(users=users)
            return deleted_user

    return None


def get_user_by_token(token):
    """Look up a user by their id token (used by opt-out page)."""
    users, _ = _read_gist()
    return next((u for u in users if u["id"] == token), None)


def get_active_users():
    """Return users who haven't opted out this week."""
    users, _ = _read_gist()
    week = _current_week()
    return [
        u for u in users
        if week not in u["opted_out_weeks"]
    ]


# ── Pairing operations ─────────────────────────────────────────────────────

def save_pairings(week, pairs):
    """Save this week's pairs, keeping only the last 2 weeks of history."""
    _, pairings = _read_gist()

    pairings.append({"week": week, "pairs": pairs})
    pairings = pairings[-2:]  # no-consecutive-repeat only needs last 1 week,
                               # keep 2 for a small buffer

    _write_gist(pairings=pairings)


def get_last_week_pairs():
    """Return the most recent week's pairs, or empty list if none."""
    _, pairings = _read_gist()
    if not pairings:
        return []
    return pairings[-1]["pairs"]