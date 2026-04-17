import random
from datetime import datetime, timezone
from storage import get_active_users, get_last_week_pairs, save_pairings
from emailer import send_pairing_emails


# ── Main entry point ───────────────────────────────────────────────────────

def run_pairing():
    """
    Full pairing run: fetch active users, generate pairs avoiding
    last week's repeats, save to Gist, send emails.
    Returns pairs as list of lists of user ids.
    """
    users = get_active_users()
    last_week = get_last_week_pairs()
    week = _current_week()

    if len(users) < 2:
        return []

    pairs = _make_pairs(users, last_week)
    id_pairs = [[u["id"] for u in pair] for pair in pairs]

    save_pairings(week, id_pairs)
    send_pairing_emails(pairs)

    return id_pairs


# ── Pairing algorithm ──────────────────────────────────────────────────────

def _make_pairs(users, last_week_pairs):
    """
    Shuffle users into pairs, retrying if any pair exactly repeats
    last week. Falls back to best available result after 20 attempts.
    """
    last_week_sets = [frozenset(p) for p in last_week_pairs]
    best = None

    for _ in range(20):
        candidate = _shuffle_into_pairs(users)
        candidate_sets = [frozenset(u["id"] for u in pair) for pair in candidate]

        # Check for any repeated pair from last week
        repeat_found = any(p in last_week_sets for p in candidate_sets)

        if not repeat_found:
            return candidate  # clean result, use immediately

        if best is None:
            best = candidate  # store first attempt as fallback

    # If we couldn't avoid all repeats (can happen with very small pools),
    # return the best fallback rather than failing entirely
    return best


def _shuffle_into_pairs(users):
    """
    Shuffle and split users into pairs, with the last group being a
    triplet if there's an odd number.
    """
    pool = users[:]
    random.shuffle(pool)

    pairs = []
    i = 0

    while i < len(pool):
        if len(pool) - i == 3:  # exactly 3 remaining
            pairs.append(pool[i:])
            break
        pairs.append(pool[i:i + 2])
    i += 2

    return pairs


# ── Week helper ────────────────────────────────────────────────────────────

def _current_week():
    return datetime.now(timezone.utc).strftime("%Y-W%W")