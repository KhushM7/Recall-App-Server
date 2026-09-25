# Physics Revision App — Server

The backend for a physics revision flashcard app, built for my A-Level Computer Science NEA. It is a Flask REST API backed by SQLite that handles:

- **User accounts**: registration, login (bcrypt-hashed passwords), and changing email, username and password.
- **Password reset**: 6-digit one-time codes sent by email through SendGrid.
- **Flashcards**: creating, editing and deleting cards, organised into named sets.
- **Spaced repetition**: cards are scheduled with the **FSRS** (Free Spaced Repetition Scheduler) algorithm, implemented from scratch in `Flashcard_System/`.
- **Statistics**: data for the frontend's graphs (review history, upcoming reviews, card states, stability, difficulty, ratings, lapses).
- **Settings**: a per-user daily review limit.

The frontend is a separate project that calls this API over HTTP.

## Contents

- [Requirements](#requirements)
- [Setup](#setup)
- [Running the server](#running-the-server)
- [Configuration](#configuration)
- [Test accounts](#test-accounts)
- [Project structure](#project-structure)
- [Logging](#logging)
- [Known issues and limitations](#known-issues-and-limitations)
- [Further documentation](#further-documentation)

## Requirements

- **Python 3.12** (tested). Newer versions may work, but the pinned dependencies date from 2024.
- A **SendGrid** account, only if you need password-reset emails.

## Setup

All commands are run from the project root (the folder containing `app.py`).

**Windows (PowerShell):**

```powershell
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3.12 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The `venv/` folder is git-ignored.

> `requirements.txt` is saved as UTF-16. pip reads it fine, but some editors and tools may show it as garbled text.

## Running the server

```bash
python app.py
```

The server starts in debug mode (auto-reload on) at **http://127.0.0.1:5000**. There is no route at `/`, so opening that address in a browser returns 404. That is expected. Every endpoint is listed in [docs/API.md](docs/API.md).

Quick check that the server is working:

```bash
curl -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d "{\"email_username\": \"demo\", \"password\": \"Demo1234!\"}"
# {"message": "Login successful"}
```

**Important:**
- **Always start the server from the project root.** The database path (`physics_revision_app.db`), the log file and the email template are all relative paths.
- **Restart the server each day.** "Today's date" is read once, when `app.py` starts, so a server left running past midnight keeps using the previous day's date for due cards and review logging.
- **To reach the server from another device** (for example a phone running the frontend), change the last line of `app.py` to `app.run(host="0.0.0.0", debug=True)` and use the computer's LAN IP address.

## Configuration

Password-reset emails need two environment variables:

| Variable | Description |
|---|---|
| `SENDGRID_API_KEY` | API key for your SendGrid account |
| `SENDER_EMAIL` | A verified sender address in SendGrid |

`.env` is git-ignored, so you can keep these values in a `.env` file in the project root:

```
SENDGRID_API_KEY=SG.your-api-key-here
SENDER_EMAIL=verified-sender@example.com
```

However, **the app does not load `.env` files automatically** (`python-dotenv` is installed but never called). Either set the variables in your shell before starting the server:

```powershell
$env:SENDGRID_API_KEY = "SG.xxxxx"
$env:SENDER_EMAIL = "you@example.com"
python app.py
```

or add `from dotenv import load_dotenv; load_dotenv()` at the top of `Reset_Password/email_service.py`.

Without these variables, everything except `/send_verification_code` works. That endpoint returns `500 {"error": "Failed to send email"}`.

## Test accounts

The committed database (`physics_revision_app.db`) contains test data. The main account for frontend testing is:

| Username | Email | Password |
|---|---|---|
| `demo` | `demo@physicsapp.test` | `Demo1234!` |

`demo` (user ID 30) has 31 physics cards in five sets: Mechanics, Electricity, Waves, Quantum Physics and Thermal Physics. It also has about a month of review history, so every statistics graph has data. On the day it was seeded (25 Sep 2026), 6 cards were due, and more come due over the following weeks.

Other earlier test users also exist in the database. You can log in with either the username or the email address.

## Project structure

```
Physics-App-Server/
├── app.py                         # Flask app: all HTTP routes
├── physics_revision_app.db        # SQLite database (schema + test data)
├── requirements.txt
├── application.log                # Runtime log (all modules write here)
│
├── User_Authentication/
│   └── user_auth.py               # UserAuthentication: register, login, account updates
│
├── Reset_Password/
│   ├── email_service.py           # OTP generation/storage/verification, SendGrid email
│   └── email_template.html        # HTML email body ("otp" is replaced with the code)
│
├── Flashcard_System/
│   ├── fsrs.py                    # FSRS scheduling algorithm
│   ├── fsrs_manager.py            # FSRSManager: links FSRS to the database
│   ├── test.py                    # Interactive command-line tool for testing reviews
│   ├── models/
│   │   ├── card.py                # Card: FSRS memory state for one card
│   │   ├── enums.py               # State (New/Learning/Review/Relearning), Rating (Again..Easy)
│   │   ├── parameters.py          # FSRS weights, target retention (0.9), max interval
│   │   ├── review_log.py          # ReviewLog: record of a single review
│   │   └── scheduler.py           # SchedulingCards / SchedulingInfo helpers
│   └── database_operations/
│       ├── base_database_operations.py   # Abstract base: fetch / insert / update / delete
│       ├── database_service.py           # DatabaseService: one object holding all *_ops
│       ├── flashcard_operations.py       # Flashcards table
│       ├── user_performance_operations.py# UserPerformance table (FSRS state, statistics)
│       ├── daily_review_log_operations.py# DailyReviewLog table
│       └── user_settings_operations.py   # UserSettings table
│
└── docs/
    ├── API.md                     # Endpoint reference
    └── ARCHITECTURE.md            # Database schema, review flow, scheduling details
```

## Logging

Every module logs to `application.log` in the project root, at INFO level. Flask's request log still prints to the console, but application messages (logins, reviews, errors) only go to the file. Check it first when debugging:

```powershell
Get-Content application.log -Tail 50 -Wait
```

## Known issues and limitations

These are behaviours of the current code worth knowing about while testing or writing up the NEA evaluation:

1. **No session tokens.** `/login` only returns a success message. After that, every endpoint trusts whatever `user_id` it is sent, so any client can read or change any user's data. A production version would issue a token (for example a JWT) on login and check it on every request.
2. **`/update_password` does not check that the OTP was verified.** The server relies on the frontend calling `/verify_otp` first.
3. **Reaching the daily review limit causes a 500 error.** When a user has reviewed `daily_review_limit` cards, `/get_due_flashcards` asks the database for 0 cards, which `fetch_due_cards` rejects as an invalid limit. The response is `500` rather than an empty list.
4. **`/update_daily_review_limit` always returns 500**, even though the limit is saved. `update_daily_review_limit` in `user_settings_operations.py` returns `None`, and the route treats that as a failure.
5. **The date is fixed at startup** (see [Running the server](#running-the-server)).
6. **`.env` is not loaded automatically** (see [Configuration](#configuration)).
7. **TLS certificate checks are disabled** in `email_service.py` (`ssl._create_unverified_context`). This works around certificate problems on some networks, but it should not be used in production.
8. **One-time codes expire after 60 seconds.** This is set in `send_verification_code`.
9. **`/create_flashcard` returns `{"card_id": null}`**, because `create_flashcard` does not return the new ID.
10. **The Users table has no UNIQUE constraints.** Duplicate emails and usernames are prevented by the application checks in `/register`, not by the database. `/update_email` and `/update_username` skip those checks.
11. **Leftover files:** `Reset_Password/otp_db.sqlite3` is no longer used (codes are stored in the `otp` table of the main database), and `emails` is a scratch list of throwaway test addresses.

## Further documentation

- **[docs/API.md](docs/API.md)**: every endpoint, with parameters, example requests and responses.
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: database schema, how a review is processed, FSRS scheduling and the priority system.
