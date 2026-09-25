# API Reference

Base URL (local development): `http://127.0.0.1:5000`

## Conventions

- **GET** endpoints take **query-string** parameters.
- **POST** endpoints take a **JSON body**. Send the header `Content-Type: application/json`.
- All responses are JSON. Errors have the form `{"error": "<message>"}`.
- There is **no authentication token**. Endpoints identify the user by the `user_id` they are sent. Call `/get_user_id` after a successful login to get it.
- The **current date** used for scheduling is the date the server was started (see the README).

Status codes used:

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created (`/register`, `/create_flashcard`) |
| 400 | A required parameter is missing, or the OTP is wrong or expired |
| 401 | Login failed |
| 404 | User not found |
| 409 | Email or username already taken |
| 500 | Server or database error (the message comes from the exception) |

## Endpoint summary

| Method | Path | Purpose |
|---|---|---|
| **Accounts** | | |
| POST | [`/register`](#post-register) | Create a user |
| POST | [`/login`](#post-login) | Check credentials |
| GET | [`/get_user_id`](#get-get_user_id) | Email or username → user ID |
| GET | [`/get_username`](#get-get_username) | User ID → username |
| GET | [`/get_email`](#get-get_email) | User ID → email |
| GET | [`/is_email_taken`](#get-is_email_taken) | Check whether an email is available |
| GET | [`/is_username_taken`](#get-is_username_taken) | Check whether a username is available |
| POST | [`/update_email`](#post-update_email) | Change email |
| POST | [`/update_username`](#post-update_username) | Change username |
| **Password reset** | | |
| POST | [`/send_verification_code`](#post-send_verification_code) | Email a 6-digit code |
| POST | [`/verify_otp`](#post-verify_otp) | Check the code |
| POST | [`/update_password`](#post-update_password) | Set a new password |
| **Flashcards** | | |
| GET | [`/get_sets`](#get-get_sets) | List set names |
| GET | [`/get_flashcards_by_set`](#get-get_flashcards_by_set) | Cards in one set |
| POST | [`/create_flashcard`](#post-create_flashcard) | Add a card |
| POST | [`/update_flashcard`](#post-update_flashcard) | Edit a card's front/back |
| POST | [`/delete_card`](#post-delete_card) | Delete one card |
| POST | [`/delete_set`](#post-delete_set) | Delete a whole set |
| **Reviewing** | | |
| GET | [`/get_due_flashcards`](#get-get_due_flashcards) | Cards due today |
| POST | [`/submit_rating`](#post-submit_rating) | Rate a reviewed card |
| **Statistics** | | |
| GET | [`/get_review_log_by_month`](#get-get_review_log_by_month) | Reviews done per day |
| GET | [`/get_next_reviews_by_month`](#get-get_next_reviews_by_month) | Reviews due per day |
| GET | [`/get_all_current_card_states`](#get-get_all_current_card_states) | Card count by state |
| GET | [`/get_current_ratings`](#get-get_current_ratings) | Card count by last rating |
| GET | [`/get_stability_data`](#get-get_stability_data) | Stability for each card |
| GET | [`/get_difficulty_data`](#get-get_difficulty_data) | Difficulty for each card |
| GET | [`/get_total_lapses`](#get-get_total_lapses) | Total number of lapses |
| **Settings** | | |
| GET | [`/get_daily_review_limit`](#get-get_daily_review_limit) | Current limit |
| POST | [`/update_daily_review_limit`](#post-update_daily_review_limit) | Change limit |

---

## Accounts

### POST `/register`

Creates a user and a `UserSettings` row (daily limit 200). The password is hashed with bcrypt.

```json
{ "email": "alice@example.com", "username": "alice", "password": "secret" }
```

| Status | Body |
|---|---|
| 201 | `{"message": "User registered successfully"}` |
| 400 | `{"error": "Email, username, and password are required"}` |
| 409 | `{"error": "Email is already taken"}` / `{"error": "Username is already taken"}` |

### POST `/login`

`email_username` is treated as an email if it contains `@`, otherwise as a username.

```json
{ "email_username": "demo", "password": "Demo1234!" }
```

| Status | Body |
|---|---|
| 200 | `{"message": "Login successful"}` |
| 400 | `{"error": "Email/Username and password are required"}` |
| 401 | `{"error": "Incorrect password!"}` / `{"error": "Username or email does not exist!"}` |

### GET `/get_user_id`

`?email_or_username=demo` → `200 {"user_id": 30}`, or `404 {"error": "User not found"}`

### GET `/get_username`

`?user_id=30` → `200 {"username": "demo"}`, or `404`

### GET `/get_email`

`?user_id=30` → `200 {"email": "demo@physicsapp.test"}`, or `404`

### GET `/is_email_taken`

`?email=demo@physicsapp.test` → `200 {"email_taken": true}`

### GET `/is_username_taken`

`?username=nobody` → `200 {"username_taken": false}`

### POST `/update_email`

```json
{ "user_id": 30, "email": "new@example.com" }
```

→ `200 {"message": "Email updated successfully"}`, or `500 {"error": "Failed to update email"}`

> Does not check whether the new email is already in use. Call `/is_email_taken` first.

### POST `/update_username`

```json
{ "user_id": 30, "username": "newname" }
```

→ `200 {"message": "Username updated successfully"}`, or `500`

> Does not check whether the new username is already in use. Call `/is_username_taken` first.

---

## Password reset

The expected flow is: `/send_verification_code` → the user types in the code → `/verify_otp` → `/update_password`.

### POST `/send_verification_code`

Generates a 6-digit code, stores it in the `otp` table with a **60-second** expiry, and emails it through SendGrid. Requires `SENDGRID_API_KEY` and `SENDER_EMAIL` (see the README).

```json
{ "email": "alice@example.com" }
```

| Status | Body |
|---|---|
| 200 | `{"status": "Verification code sent"}` |
| 400 | `{"error": "Email is required"}` |
| 500 | `{"error": "Failed to send email"}` |

> A code is generated whether or not the email belongs to a registered user.

### POST `/verify_otp`

```json
{ "email": "alice@example.com", "otp": "123456" }
```

| Status | Body |
|---|---|
| 200 | `{"status": "OTP verified"}` (the code is then deleted) |
| 400 | `{"error": "OTP not found"}` / `{"error": "OTP expired"}` / `{"error": "Invalid OTP"}` |

### POST `/update_password`

```json
{ "email": "alice@example.com", "password": "newSecret" }
```

→ `200 {"message": "Password updated successfully"}`, or `500`

> The server does **not** check that `/verify_otp` succeeded first.

---

## Flashcards

### GET `/get_sets`

`?user_id=30` →

```json
{ "sets": ["Mechanics", "Electricity", "Waves", "Quantum Physics", "Thermal Physics"] }
```

A set exists only while it contains at least one card. There is no separate "sets" table.

### GET `/get_flashcards_by_set`

`?user_id=30&set_name=Waves` →

```json
{
  "flashcards": [
    { "card_id": 16, "front": "Wave speed equation?", "back": "v = fλ" },
    { "card_id": 17, "front": "What is a transverse wave?", "back": "Oscillations are perpendicular to ..." }
  ]
}
```

### POST `/create_flashcard`

Creating a card with a new `set_name` creates that set. The new card gets the next free `card_id` for this user and is **due today**.

```json
{
  "user_id": 30,
  "flashcard_data": { "set_name": "Waves", "front": "Define wavelength.", "back": "Distance between adjacent crests." }
}
```

→ `201 {"card_id": null}`. The ID is not returned; use `/get_flashcards_by_set` to find it.

### POST `/update_flashcard`

Changes only the front and back. A card cannot be moved to a different set.

```json
{ "user_id": 30, "flashcard": { "card_id": 16, "front": "New front", "back": "New back" } }
```

→ `200 {"message": "Flashcard updated successfully"}`

### POST `/delete_card`

Deletes the card and its review state.

```json
{ "user_id": 30, "card_id": 16 }
```

→ `200 {"message": "Flashcard deleted successfully"}`

### POST `/delete_set`

Deletes every card in the set, along with their review state.

```json
{ "user_id": 30, "set_name": "Waves" }
```

→ `200 {"message": "Flashcard set deleted successfully"}`

---

## Reviewing

### GET `/get_due_flashcards`

Returns the cards due on or before today. Overdue cards come first (ordered by priority, then due date). The number returned is capped at `daily_review_limit` minus the number of cards already reviewed today.

`?user_id=30` →

```json
{
  "flashcards": [
    { "card_id": 24, "set_name": "Quantum Physics", "front": "Define the work function.", "back": "Minimum energy needed ..." },
    { "card_id": 27, "set_name": "Thermal Physics", "front": "Specific heat capacity equation?", "back": "Q = mcΔθ" }
  ]
}
```

> **This call modifies the database.** Overdue cards are moved to tomorrow and their priority is increased. See [ARCHITECTURE.md](ARCHITECTURE.md#priority-system).
>
> **Known bug:** once the user has reviewed their full daily limit, this returns `500 {"error": "Invalid limit: 0"}` instead of an empty list.

### POST `/submit_rating`

Records one review. `rating` must be one of the strings **`"Again"`, `"Hard"`, `"Good"` or `"Easy"`** (case-sensitive).

```json
{ "user_id": 30, "card_id": 24, "rating": "Good" }
```

| Status | Body |
|---|---|
| 200 | `{"success": true}` |
| 400 | `{"error": "User ID, card ID, and rating are required"}` |
| 500 | `{"error": "Failed to process rating"}` (includes an invalid rating string) |

This updates the card's FSRS state and next review date, and increments today's count in `DailyReviewLog`.

---

## Statistics

All statistics endpoints take `?user_id=`. The month endpoints also take `month` (the **full English month name**, e.g. `September`) and `year` (e.g. `2026`).

### GET `/get_review_log_by_month`

Number of cards reviewed on each day of the month. Days with no reviews are left out.

`?user_id=30&month=September&year=2026` →

```json
{ "review_log": { "2": 1, "4": 3, "7": 20, "8": 7, "24": 2 } }
```

### GET `/get_next_reviews_by_month`

Number of cards scheduled for each day of the month.

`?user_id=30&month=October&year=2026` →

```json
{ "next_reviews": { "1": 3, "3": 3, "4": 3, "10": 1 } }
```

### GET `/get_all_current_card_states`

States with no cards are left out.

```json
{ "card_states": { "New": 5, "Review": 26 } }
```

The possible keys are `New`, `Learning`, `Review` and `Relearning`.

### GET `/get_current_ratings`

Each card counted by its most recent rating.

```json
{ "current_ratings": { "Easy": 7, "Good": 18, "Hard": 1, "Not Reviewed": 5 } }
```

The possible keys are `Not Reviewed`, `Again`, `Hard`, `Good` and `Easy`.

### GET `/get_stability_data`

Maps each `card_id` to its stability (the number of days until recall probability drops to 90%).

```json
{ "stability_data": { "1": 32.33, "2": 32.45, "3": 23.13 } }
```

### GET `/get_difficulty_data`

Maps each `card_id` to its difficulty (1 = easiest, 10 = hardest).

```json
{ "difficulty_data": { "1": 7.72, "2": 7.19, "3": 5.34 } }
```

### GET `/get_total_lapses`

The total number of times any of the user's cards was forgotten (rated Again) while in the Review state.

```json
{ "total_lapses": 4 }
```

---

## Settings

### GET `/get_daily_review_limit`

`?user_id=30` → `200 {"daily_review_limit": 200}`, or `404`

### POST `/update_daily_review_limit`

```json
{ "user_id": 30, "new_limit": 50 }
```

→ Intended response: `200 {"message": "Daily review limit updated successfully"}`

> **Known bug:** the database is updated correctly, but the endpoint always returns `500 {"error": "Failed to update daily review limit"}`. The route checks the return value of `UserSettingsOperations.update_daily_review_limit`, which returns `None`. Until this is fixed, the frontend should confirm the change with `/get_daily_review_limit`.
>
> `new_limit` must be a positive integer. A value of `0` is rejected with `400` as a "missing" parameter.
