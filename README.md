# Zhetisu University AI Marketplace (Desktop MVP)

This repository contains a **desktop MVP** for an internal university AI marketplace.

## What this MVP includes

- Desktop app UI (Tkinter) for Windows/Linux/macOS
- Mock authentication with role-based access (`student`, `teacher`, `admin`)
- Marketplace with categories and semantic search
- Mock install flow with download counters
- Student app upload and admin moderation
- AI Navigator recommendation panel
- Student digital portfolio
- Teacher dashboard for usage insights
- Admin panel for approvals and system control

## Quick start

```bash
python3 app.py
```

No external dependencies are required beyond Python 3.

## Demo accounts

- Student: `student1 / pass123`
- Student: `student2 / pass123`
- Teacher: `teacher1 / pass123`
- Admin: `admin1 / admin123`

## Data storage

The app uses a local SQLite database file:

- `marketplace.db` (auto-created on first run)

## Notes

- This is an MVP for internal pilot use and demo purposes.
- Install action is simulated (no executable deployment).
- Authentication is mock and not integrated with university SSO.
