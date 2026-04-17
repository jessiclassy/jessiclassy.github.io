import os
import smtplib
from email.message import EmailMessage
import os
import smtplib
from email.message import EmailMessage

try: # for local testing
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, assume env vars are set manually

# SMTP configuration (SMTP2GO)
SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ["SMTP_PORT"])  # 2525, 587, or 465
SMTP_USERNAME = os.environ["SMTP_USERNAME"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
FROM_EMAIL = os.environ["FROM_EMAIL"]
OPT_OUT_BASE_URL = os.environ["OPT_OUT_BASE_URL"]


# ── Low-level sender ───────────────────────────────────────────────────────

def _send_email(to_email, to_name, subject, body):
    """
    Send a single email using SMTP.
    `to_email` and `to_name` are strings.
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Rubber Duck Talks <{FROM_EMAIL}>"
    msg["To"] = f"{to_name} <{to_email}>"
    msg.set_content(body)  # plain text

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()  # upgrade to secure connection
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


def _send_email_to_multiple(recipients, subject, body):
    """
    Send one email to multiple recipients (for pairing threads).
    `recipients` is a list of dicts: [{"email": "a@b.com", "name": "Alice"}, ...]
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Rubber Duck Talks <{FROM_EMAIL}>"
    
    # Build To header with all recipients (they'll all see each other's emails)
    to_header = ", ".join([f"{r['name']} <{r['email']}>" for r in recipients])
    msg["To"] = to_header
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


# ── Reminder email (sent Sunday) ───────────────────────────────────────────

def send_reminder_emails(users):
    """
    Send weekly reminder to all active users.
    Includes their personal opt-out link.
    `users` is a list of user dicts from storage.
    """
    for user in users:
        opt_out_url = f"{OPT_OUT_BASE_URL}?token={user['id']}"
        body = _reminder_body(user["name"], opt_out_url)
        _send_email(user["email"], user["name"], "RDT reminder", body)


def _reminder_body(name, opt_out_url):
    return f"""Hi {name},

Just a heads up — your Rubber Duck Talks pairing for this week goes out tomorrow (Monday) at noon.

If you'd like to skip this week or leave the group, you can do so here:
{opt_out_url}

Otherwise, no action needed — you'll hear from us tomorrow!

- Rubber Duck Talks
"""


# ── Pairing email (sent Monday) ────────────────────────────────────────────

def send_pairing_emails(pairs):
    """
    Send one email per pair/triplet with all members on the same thread.
    `pairs` is a list of lists of user dicts (not ids).
    """
    for pair in pairs:
        _send_pairing_thread(pair)


def _send_pairing_thread(pair):
    """Send a single email to the whole pair/triplet so they share a thread."""
    names = [u["name"] for u in pair]
    name_str = " & ".join(names)
    subject = f"Your RDT pairing this week: {name_str} 🐥"
    body = _pairing_body(names)
    
    # Build recipient list for the To header
    recipients = [{"email": u["email"], "name": u["name"]} for u in pair]
    
    _send_email_to_multiple(recipients, subject, body)


def _pairing_body(names):
    if len(names) == 2:
        greeting = f"Hi {names[0]} and {names[1]},"
        partner_str = f"You're each other's Rubber Duck Talks partner this week!"
    else:
        greeting = f"Hi {', '.join(names[:-1])} and {names[-1]},"
        partner_str = f"You're this week's Rubber Duck Talks trio!"

    return f"""{greeting}

{partner_str}

Reply to this email to get the thread going, and schedule a check-in whenever works for everyone.

See you next week,
- Rubber Duck Talks
"""