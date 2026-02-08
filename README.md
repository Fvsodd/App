# Zhetisu University AI Marketplace — Beta UI Demo

This repository now contains a **Material UI-based beta interface** designed for clear presentation to university administration and teachers.

## What changed

- Replaced raw prototype UI with Material UI components and layout system.
- Added clear left-side navigation for role-based flows.
- Added a "What to do" guidance panel to make user actions obvious.
- Kept core MVP functionality:
  - role-based login (student/teacher/admin)
  - marketplace browsing + semantic-style search
  - student upload (guided modal)
  - AI navigator recommendations
  - student portfolio
  - teacher dashboard
  - admin moderation queue
- Hidden/removed unfinished advanced controls for cleaner demo behavior.

## Run locally

```bash
npm install
npm run dev
```

Then open the printed localhost URL.

## Demo accounts

- `student1 / pass123`
- `student2 / pass123`
- `teacher1 / pass123`
- `admin1 / admin123`

## Notes

- This is a frontend-focused beta presentation build.
- Data is seeded in-memory for demo simplicity.
- No production auth or deployment logic is included.
