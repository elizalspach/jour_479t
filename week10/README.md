# Source Check-In Slackbot

A Slack bot that automatically reminds reporters to stay in touch with their sources.

## What it does

The bot reads a Google Sheet containing a list of sources — including each source's name and the date they were last contacted. It checks every entry against a 7-day threshold and posts a summary message to a designated Slack channel:

- If all sources have been contacted within the past week, it posts a confirmation that everything is on track.
- If any sources haven't been contacted in 7 or more days (or have no contact date on record), it posts an alert listing those sources by name along with how long it has been since they were last reached.

## How it helps reporters

Maintaining regular contact with sources is essential for beat reporters. It's easy to lose track of who you've spoken to recently, especially when managing a large roster of contacts. This bot surfaces that information automatically, so reporters don't have to audit their notes manually. A daily or weekly run of the script keeps the whole team accountable and ensures no source goes cold.

## Setup

**Requirements:** `slack_sdk`, `gspread`

```
pip install slack-sdk gspread
```

**Environment variables:**

| Variable | Description |
|---|---|
| `SLACK_API_TOKEN` | Bot token for your Slack app (starts with `xoxb-`) |
| `GOOGLE_API_KEY` | Google API key with access to the Sheets API |

**Configuration** (top of `slackbot.py`):

| Variable | Description |
|---|---|
| `SHEET_ID` | The ID of your Google Sheet (from its URL) |
| `CHANNEL` | The Slack channel name to post to |
| `DAYS_THRESHOLD` | Number of days before a source is flagged (default: `7`) |

## Usage

```bash
python slackbot.py
```

Run this manually or schedule it with a cron job to get automatic reminders on a regular cadence.
