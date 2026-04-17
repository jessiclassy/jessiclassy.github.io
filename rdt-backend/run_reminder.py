from storage import get_active_users
from emailer import send_reminder_emails

def main():
    users = get_active_users()

    if not users:
        print("No active users this week, skipping reminder.")
        return

    send_reminder_emails(users)
    print(f"Reminder emails sent to {len(users)} users.")

if __name__ == "__main__":
    main()