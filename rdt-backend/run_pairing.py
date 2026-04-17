from pairing import run_pairing
from emailer import send_pairing_emails

def main():
    pairs = run_pairing()

    if not pairs:
        print("Not enough active users to pair this week, skipping.")
        return

    print(f"Pairing complete: {len(pairs)} pairs this week.")
    send_pairing_emails(pairs)
    print(f"Reminder emails sent to {len(pairs)} pairs/groups.")

if __name__ == "__main__":
    main()