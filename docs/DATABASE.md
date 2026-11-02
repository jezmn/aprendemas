# Database

AprendeMas uses **SQLite**. No server or setup needed. File `aprendemas_chat.db` is created automatically in the app directory.

## Schema

**chat_sessions** — one row per conversation.

| Column | Type | Notes |
|---|---|---|
| session_id | TEXT UUID | Primary key |
| user_id | TEXT | Defaults to "anonymous" |
| title | TEXT | Auto-generated from first message |
| created_at | TIMESTAMP | Set on creation |
| last_activity | TIMESTAMP | Updated on every message |

**chat_messages** — messages within a session.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Auto-increment PK |
| session_id | TEXT | FK to chat_sessions |
| user_message | TEXT | User input |
| ai_response | TEXT | Model reply |
| timestamp | TIMESTAMP | When sent |

## How it works

1. New chat → UUID `session_id` in `chat_sessions`.
2. Each exchange → row in `chat_messages`.
3. Sidebar loads titles/counts via `LEFT JOIN`.
4. Clicking a session loads last 6 message pairs.
5. Deleting a session removes its session row and all messages.

Local only. No telemetry, sync, or cloud.
