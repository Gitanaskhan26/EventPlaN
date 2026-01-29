# 🎯 EventPlan - Campus Event Management System

> **Team WunderBar** | Hackathon 2026

![EventPlan Banner](https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=1200&h=400&fit=crop)

---

## 👥 Team WunderBar

| Role | Name | GitHub ID |
|------|------|-----------|
| **Team Lead** | Anas Khalid | [@gitanaskhan26](https://github.com/gitanaskhan26) |
| **Frontend Developer** | Ali Hasan | [@alihasan792](https://github.com/alihasan792) |
| **Backend Developer** | Ahmad Rahman | [@7moodal5oory](https://github.com/7moodal5oory) |

---

## 💡 Proposed Solution

**EventPlan** is a comprehensive campus event management platform designed to streamline the entire event lifecycle — from discovery to participation.

### The Problem
- Students struggle to find relevant campus events
- Event organizers lack tools for efficient participant management
- No real-time communication between organizers and participants
- Manual tracking of registrations is error-prone

### Our Solution
A one-stop platform that:
- **Discovers** — Browse events by category with countdown timers
- **Registers** — Quick signup with instant ticket ID generation
- **Tracks** — Visual progress bar showing registration status
- **Notifies** — Real-time WebSocket announcements
- **Manages** — Admin dashboard with bulk actions and analytics

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Core language |
| **FastAPI** | High-performance web framework |
| **SQLAlchemy** | ORM for database operations |
| **SQLite** | Lightweight database |
| **WebSockets** | Real-time announcements |
| **Uvicorn** | ASGI server |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Jinja2** | Server-side templating |
| **Tailwind CSS** | Utility-first styling |
| **Alpine.js** | Lightweight reactivity |
| **QRCode.js** | Virtual ticket QR codes |

### Design
- Dark theme (`#0a0a0a`)
- Multi-color gradient text effects
- Glassmorphism panels
- Bento grid layouts

---

## 🔄 Project Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      USER JOURNEY                           │
└─────────────────────────────────────────────────────────────┘

  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │    01    │     │    02    │     │    03    │     │    04    │
  │ DISCOVER │────▶│ REGISTER │────▶│  TRACK   │────▶│  ATTEND  │
  │          │     │          │     │          │     │          │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
       │                │                │                │
       ▼                ▼                ▼                ▼
   Browse by       Get unique       Visual status    Show QR code
   category &      Ticket ID        progress bar     virtual pass
   countdown       instantly        updates          at entry
```

### User Flow
1. **Homepage** → Browse events by category, view countdown timers
2. **Event Page** → Read details, register with name/email
3. **Track Page** → Enter ticket ID to see 4-step progress
4. **Virtual Pass** → Confirmed users get QR code ticket

### Admin Flow
1. **Dashboard** → View analytics (total, confirmed, pending, rate)
2. **Event Management** → Approve/reject participants, bulk actions
3. **Announcements** → Broadcast messages via WebSocket

---

## ✨ Uniqueness

### 1. Real-Time WebSocket Announcements
When admins post announcements, connected users receive **instant toast notifications** — no page refresh needed.

### 2. Visual Status Stepper
Instead of plain text status, users see a **4-step progress bar**:
```
Registered → Under Review → Shortlisted → Confirmed
```

### 3. Virtual Ticket Pass
Confirmed participants get a **gradient-styled virtual pass** with:
- Event details
- QR code linking to verification URL
- Unique ticket ID

### 4. EventPlan Dark Theme
Premium UI inspired by modern event platforms:
- Multi-color gradient text
- Glassmorphism effects
- Bento grid layouts
- Smooth micro-animations

### 5. Bulk Admin Actions
Organizers can **confirm or reject all participants** with one click, plus export to CSV.

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Gitanaskhan26/EventPlaN.git
cd EventPlaN

# Install dependencies
pip install fastapi sqlalchemy uvicorn jinja2 python-multipart

# Run the server
python main.py
```

Visit **http://localhost:3000** 🎉

---

## 📁 Project Structure

```
EventPlaN/
├── main.py                 # FastAPI application
├── campus_events.db        # SQLite database
├── static/
│   └── favicon.ico         # App icon
└── templates/
    ├── base.html           # Base layout
    ├── index.html          # Homepage
    ├── event.html          # Event details
    ├── track.html          # Status tracker
    ├── admin_base.html     # Admin layout
    ├── admin_dashboard.html
    └── admin_event.html
```

---

## 📸 Screenshots

| Homepage | Event Page | Track Status |
|----------|------------|--------------|
| Dark hero with gradient text | Tabbed content with timeline | Visual progress stepper |

| Admin Dashboard | Virtual Ticket |
|-----------------|----------------|
| Analytics cards | QR code pass |

---

## 📄 License

MIT License — Built with ❤️ by **Team WunderBar**

---

<p align="center">
  <b>EventPlan</b> — Precision planning for perfect campus events
</p>
