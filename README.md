# EventPlan — Integral University Event Management System

> **Team WunderBar** · Hackathon 2026 · Integral University, Lucknow

---

## Team

| Role | Name | GitHub |
|------|------|--------|
| **Team Lead** | Anas Khalid | [@Gitanaskhan26](https://github.com/Gitanaskhan26) |
| **Frontend Developer** | Ali Hasan | [@alihasan792](https://github.com/alihasan792) |
| **Backend Developer** | Ahmad Rahman | [@7moodal5oory](https://github.com/7moodal5oory) |

---

## Problem Statement

- Students at Integral University struggle to discover upcoming campus events.
- Organizers lack a centralised tool for participant management and real-time communication.
- Manual registration tracking is error-prone and wastes administrative time.

## Our Solution

**EventPlan** is a full-stack web application that streamlines the entire event lifecycle at Integral University:

| Capability | Description |
|---|---|
| **Discover** | Browse events by category with live countdown timers |
| **Register** | One-click signup → instant unique Ticket ID |
| **Track** | Visual 4-step progress bar showing registration status |
| **Notify** | Real-time WebSocket announcements (no page refresh) |
| **Manage** | Admin dashboard with bulk actions, analytics & CSV export |
| **Verify** | QR-code virtual ticket pass for confirmed participants |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | **Python 3.10+**, **FastAPI**, **SQLAlchemy**, **SQLite** | REST API, ORM, lightweight DB |
| Real-time | **WebSockets** (native FastAPI) | Live announcements |
| Server | **Uvicorn** | ASGI server |
| Templating | **Jinja2** | Server-side HTML rendering |
| Frontend | **Tailwind CSS**, **Alpine.js** | Utility-first styling, lightweight reactivity |
| Extras | **QRCode.js** | Virtual ticket QR codes |

---

## Application Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ DISCOVER  │────▶│ REGISTER │────▶│  TRACK   │────▶│  ATTEND  │
│ Browse by │     │ Get unique│     │ Visual   │     │ Show QR  │
│ category  │     │ Ticket ID │     │ stepper  │     │ at entry │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

### User Journey
1. **Homepage** → Browse events filtered by category, view countdown timers.
2. **Event Page** → Read details, register with name & IU email.
3. **Track Page** → Enter Ticket ID / email to see 4-step progress.
4. **Virtual Pass** → Confirmed users receive a QR-code ticket.

### Admin Journey
1. **Login** → Secure session-based authentication.
2. **Dashboard** → Analytics cards (total, confirmed, pending, approval rate).
3. **Event Management** → Approve / reject participants, bulk actions, CSV export.
4. **Announcements** → Broadcast messages via WebSocket to all connected users.

---

## Key Features

| # | Feature | Detail |
|---|---------|--------|
| 1 | **Real-Time Announcements** | WebSocket-powered toast notifications — no refresh needed |
| 2 | **Visual Status Stepper** | `Registered → Under Review → Shortlisted → Confirmed` |
| 3 | **Virtual Ticket Pass** | Gradient-styled pass with QR code + ticket ID |
| 4 | **Bulk Admin Actions** | Confirm / reject all participants in one click |
| 5 | **CSV Export** | Download participant lists as CSV |
| 6 | **Dark Premium UI** | Glassmorphism, gradient text, Bento grid, micro-animations |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Gitanaskhan26/EventPlaN.git
cd EventPlaN

# 2. Install dependencies
pip install fastapi sqlalchemy uvicorn jinja2 python-multipart

# 3. Run
python main.py
```

Open **http://localhost:8000** in your browser.

### Admin Credentials (demo)

| Username | Password |
|----------|----------|
| `admin` | `eventplan2026` |

---

## Project Structure

```
EventPlaN/
├── main.py                  # FastAPI application (routes, models, WebSocket)
├── campus_events.db         # SQLite database (auto-created on first run)
├── static/                  # Static assets
└── templates/
    ├── base.html            # Public layout
    ├── index.html           # Homepage — event discovery
    ├── event.html           # Event detail & registration
    ├── track.html           # Status tracker with visual stepper
    ├── ticket.html          # Virtual ticket / QR pass
    ├── admin_base.html      # Admin layout with sidebar
    ├── admin_login.html     # Admin authentication
    ├── admin_dashboard.html # Analytics & event list
    ├── admin_event.html     # Participant management
    └── admin_event_form.html# Create / edit event form
```

---

## License

MIT — Built with care by **Team WunderBar** for Integral University.
