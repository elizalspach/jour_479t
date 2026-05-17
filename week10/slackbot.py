# importing the libraries we need to run this script
import os
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import gspread

# --- configuration ---
SHEET_ID = '1LxvSbeGDR--zVny4agzvNWV3DlQScrkLdKWIrUrdQV4'
CHANNEL = 'jour479t'
DAYS_THRESHOLD = 7

# pull secrets from environment
slack_token = os.environ.get('SLACK_API_TOKEN')
google_api_key = os.environ.get('GOOGLE_API_KEY')

# connect to slack
client = WebClient(token=slack_token)


def get_sources():
    """Pull all rows from the Google Sheet using an API key."""
    gc = gspread.api_key(google_api_key)
    sheet = gc.open_by_key(SHEET_ID).sheet1
    # returns a list of dicts using the header row as keys
    # e.g. [{'Name': 'Jane Smith', 'Phone': '...', 'Email': '...', 'Last contact date': '5/1/2024'}, ...]
    return sheet.get_all_records()


def check_overdue(sources):
    """Return a list of message strings for sources not contacted in 7+ days."""
    overdue = []
    today = datetime.today()

    for source in sources:
        name = source.get('Name', '').strip()
        last_contact = str(source.get('Last contact date', '')).strip()

        # skip blank rows
        if not name:
            continue

        # no contact date at all — flag it
        if not last_contact:
            overdue.append(f"• *{name}* — never contacted")
            continue

        # try common date formats
        parsed = None
        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y', '%B %d, %Y', '%b %d, %Y'):
            try:
                parsed = datetime.strptime(last_contact, fmt)
                break
            except ValueError:
                continue

        if parsed is None:
            overdue.append(f"• *{name}* — unreadable date: {last_contact}")
            continue

        days_since = (today - parsed).days
        if days_since >= DAYS_THRESHOLD:
            overdue.append(
                f"• *{name}* — last contacted {days_since} days ago ({last_contact})"
            )

    return overdue


def send_reminder(overdue):
    """Post a check-in message to the Slack channel."""
    if not overdue:
        msg = (
            ":white_check_mark: *Source Check-In* — "
            "all sources have been contacted within the last 7 days. Great work!"
        )
    else:
        source_list = '\n'.join(overdue)
        msg = (
            ":rotating_light: *Source Check-In Reminder*\n"
            "The following sources haven't been contacted in 7+ days:\n\n"
            f"{source_list}\n\n"
            "Please reach out soon!"
        )

    try:
        client.chat_postMessage(
            channel=CHANNEL,
            text=msg,
            unfurl_links=True,
            unfurl_media=True
        )
        print("success!")
    except SlackApiError as e:
        assert e.response["ok"] is False
        print(f"Got an error: {e.response['error']}")


# run the check
sources = get_sources()
overdue = check_overdue(sources)
send_reminder(overdue)
