# Gym Management System

A Python + Streamlit web app for managing multiple gyms, member registrations, and expenditure tracking — all backed by SQLite for permanent local storage.

## Run & Operate

- `cd gym-app && streamlit run app.py` — run the Streamlit app (port 5000)
- The workflow "Start application" handles this automatically

## Stack

- Python 3.11, Streamlit 1.57, Pillow
- **Database**: Replit-managed Postgres in production (and dev — `DATABASE_URL` is set automatically). Falls back to SQLite at `gym-app/gym_pro.db` only when `DATABASE_URL` is unset (e.g. fresh clone with no DB provisioned).
- SQLAlchemy 2.x ORM with `psycopg2-binary` driver
- Member photos stored locally in `gym-app/uploads/` (note: ephemeral on Autoscale — see Gotchas)

## Where things live

- `gym-app/app.py` — main entry point, sidebar navigation, page routing
- `gym-app/database.py` — all SQLite operations (gyms, members, expenses)
- `gym-app/pages/dashboard.py` — overview metrics and charts
- `gym-app/pages/setup.py` — gym name management
- `gym-app/pages/members.py` — member registration with photo upload
- `gym-app/pages/expenses.py` — expenditure tracking
- `gym-app/uploads/` — member photos
- `gym-app/gym_management.db` — SQLite database (auto-created on first run)

## Product

- **Dashboard** — per-gym member counts, expense totals, monthly bar chart, recent activity
- **Setup** — add/edit/delete named gyms with address, phone, email; shows member count and spend per gym
- **Members** — register members with auto-generated serial numbers (e.g. PF-00001), photo upload, membership type, join/expiry dates, status; edit and delete with confirmation
- **Expenses** — record expenses per gym with categories (Equipment, Maintenance, Utilities, etc.), optional member link, date range filtering; bar chart breakdown by category

## User preferences

- Python + Streamlit preferred for web UI
- Replit-managed Postgres for permanent storage (SQLite fallback only)
- Sidebar navigation pattern

## Gotchas

- **Database selection** is automatic via `DATABASE_URL`. In Replit (dev and deployed), Postgres is used. The `gym_pro.db` SQLite file is only used as a fallback for environments without `DATABASE_URL`.
- **Default seed users** are `admin/admin123`, `staff/staff123`, `auditor/auditor123`. Override in production by setting `ADMIN_DEFAULT_PASSWORD`, `STAFF_DEFAULT_PASSWORD`, `AUDITOR_DEFAULT_PASSWORD` env vars *before* the first deploy (after the seed runs, change passwords via the UI).
- **Autoscale deployment notes**: filesystem is ephemeral, so member photo uploads in `gym-app/uploads/` do NOT persist across instance restarts. If photos must persist in production, migrate uploads to Replit Object Storage (see `object-storage` skill).
- Serial numbers are generated per-gym: initials + 5-digit count (e.g. "PF-00001" for "PowerFit"). `add_member` retries on serial collision (autoscale safety).
- Photo files persist in `gym-app/uploads/` (dev) — deleting a member also removes their photo file.
