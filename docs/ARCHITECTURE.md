# Architecture

## Overview

```
 Frontend ──HTTP/JSON──▶ app.py (Flask routes)
                            │
         ┌──────────────────┼────────────────────────┐
         ▼                  ▼                        ▼
 UserAuthentication    FSRSManager              email_service
 (User_Authentication) (Flashcard_System)       (Reset_Password)
         │               │        │                  │
         │               ▼        ▼                  │  SendGrid API
         │             FSRS   DatabaseService        │
         │         (algorithm)    │                  │
         │                        ▼                  │
         │      FlashcardOperations, UserPerformanceOperations,
         │      DailyReviewLogOperations, UserSettingsOperations
         │                        │                  │
         └────────────────────────┼──────────────────┘
                                  ▼
                      physics_revision_app.db (SQLite)
```

- **`app.py`** reads request parameters, calls one of the service objects, and converts the result or exception into a JSON response. It creates a single `UserAuthentication`, `FSRSManager` and `DatabaseService` when it starts.
- **`DatabaseService`** is a facade that exposes one operations object per table (`flashcard_ops`, `user_performance_ops`, `daily_review_log_ops`, `user_settings_ops`).
- Every `*Operations` class inherits `fetch` / `fetch_one` / `insert` / `update` / `delete` from **`BaseDatabaseOperations`**. It adds logging and table-specific queries on top. Every query is parameterised (`?` placeholders), which prevents SQL injection.
- **`FSRS`** is the scheduling algorithm and knows nothing about the database. **`FSRSManager`** loads a card's state from the database into a `Card` object, runs `FSRS.review_card`, and writes the result back.

## Database schema

Everything is stored in `physics_revision_app.db`.

```
Users                       UserSettings
─────                       ────────────
user_id  PK AUTOINCREMENT   user_id  PK  ──▶ Users.user_id
email    TEXT               daily_review_limit INTEGER DEFAULT 200
username TEXT
password TEXT (bcrypt hash)

Flashcards                          UserPerformance  (one row per card)
──────────                          ───────────────
user_id  ┐ PK                       user_id  ┐ UNIQUE ──▶ Flashcards
card_id  ┘ (card_id is per-user)    card_id  ┘
set_name TEXT                       stability, difficulty   REAL  (FSRS memory state)
front    TEXT                       rating       INT  (last rating 1-4, 0 = never)
back     TEXT                       state        INT  (0 New, 1 Learning, 2 Review, 3 Relearning)
                                    scheduled_days, elapsed_days, reps, lapses  INT
                                    review_time      TEXT  (ISO datetime of last review)
                                    next_review_date TEXT  (YYYY-MM-DD)
                                    priority         INT   (see Priority system below)

DailyReviewLog                      otp
──────────────                      ───
user_id      ┐ PK                   email  PK
review_date  ┘ (YYYY-MM-DD)         otp    TEXT (6 digits)
reviewed_cards_count INT            expiry REAL (Unix timestamp)
```

Notes:
- **`card_id` is numbered separately for each user** (1, 2, 3, … for every user), so a card is identified by the pair `(user_id, card_id)`.
- **Sets are not a table.** A set is just the `set_name` shared by some cards, and it disappears when its last card is deleted.
- **There are no foreign-key constraints.** Relationships between tables are kept consistent by the application code. For example, `/delete_card` deletes from both `Flashcards` and `UserPerformance`.
- **`UserSettings` is created by `/register`.** A user inserted any other way needs a `UserSettings` row added by hand, otherwise `/get_due_flashcards` fails with "No daily review limit set".

## Lifecycle of a card

1. **Create.** `/create_flashcard` inserts a `Flashcards` row and a `UserPerformance` row with state New and `next_review_date` set to today, so the card is due immediately.
2. **Fetch.** `/get_due_flashcards`:
   1. Reads the daily limit and today's review count, and works out how many reviews are left.
   2. Runs `mark_cards_as_priority` (see below) to bring overdue cards forward.
   3. Selects cards with `next_review_date <= today`, highest priority first, up to the remaining limit.
3. **Review.** `/submit_rating` with Again, Hard, Good or Easy calls `FSRSManager.process_rating`, which:
   1. Loads the `UserPerformance` row into a `Card`.
   2. Calls `FSRS.review_card(card, rating)`, which updates stability, difficulty, state, reps and lapses and works out the new due date.
   3. **Adds a small random delay.** If another card reviewed today ended up with exactly the same stability and difficulty, the due date is pushed back by 0 or 1 days at random. This spreads identical cards over different days.
   4. Saves the new state with `INSERT OR REPLACE`, which also resets `priority` to 0.
   5. Increments today's `DailyReviewLog` count.
   6. Moves any cards still due today with priority 0 to tomorrow and sets their priority to 1.

## FSRS scheduling

`Flashcard_System/fsrs.py` implements the FSRS (Free Spaced Repetition Scheduler) algorithm, using the 19-weight parameter set. Each card has three values that describe how well it is remembered:

| Value | Meaning |
|---|---|
| **Stability (S)** | Days until the chance of recalling the card falls to 90% |
| **Difficulty (D)** | How hard the card is, from 1 to 10. Again and Hard ratings raise it; Easy lowers it |
| **Retrievability (R)** | The current chance of recall, calculated from S and the time since the last review |

The settings are in `models/parameters.py`: 19 model weights `w`, a target retention (`request_retention`) of **0.9**, and a `maximum_interval` of **36500 days**. For a card in the Review state, the next interval is the time it takes for R to fall to the target retention. That time grows with S, so each successful review spaces the card further out.

Changes from standard FSRS:
- **Reviews are scheduled by day, not by time.** `schedule_next_review` rounds every due date to midnight UTC. If the result is still today, the card is moved to tomorrow. Standard FSRS uses short "learning steps" (1, 5 or 10 minutes) for new cards; here they all become "tomorrow", so a card is never shown twice on the same day.
- **Scheduling uses the server's date.** The review date passed in is the server's `today`, and FSRS treats the card's due date as the moment of review.

## Priority system

This scheme is specific to this app. It stops overdue cards piling up and ensures cards the user skipped are shown first next time.

- **`/get_due_flashcards`** moves every card with `next_review_date < today` to **tomorrow** and increases its `priority` by 1. The more days a card has been missed, the higher its priority.
- **After each `/submit_rating`**, any card still due today with priority 0 is moved to **tomorrow** with priority 1.
- **`fetch_due_cards`** sorts by `priority DESC`, then `next_review_date ASC`, so the cards that have waited longest come first.
- **Reviewing a card** resets its priority to 0.

Because of these rules, a card is only returned if it is due **exactly today** at the moment of the request. If the user leaves a session partway through, the cards they didn't reach show up first the next day.

## Password reset flow

```
Frontend                          Server                          SendGrid
   │ POST /send_verification_code   │                                │
   │───────────────────────────────▶│ generate 6-digit OTP            │
   │                                │ store (email, otp, now+60s)     │
   │                                │──── email from template ───────▶│
   │ POST /verify_otp               │                                │
   │───────────────────────────────▶│ compare + expiry check          │
   │                                │ delete OTP on success           │
   │ POST /update_password          │                                │
   │───────────────────────────────▶│ bcrypt hash + UPDATE Users      │
```

Codes are stored in the `otp` table, one per email. Requesting a new code replaces the old one. `/update_password` trusts the frontend to have verified the code first (see Known issues in the README).

## Logging

Each module calls `logging.basicConfig(filename="application.log", level=INFO)`. Only the first call takes effect, so every module writes to the same file in the directory the server was started from. `Flashcard_System/test.py` is the exception: it is meant to be run from inside `Flashcard_System/` and logs to `../physics_server_log.log`.
