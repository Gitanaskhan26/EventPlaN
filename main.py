"""
Campus Event Manager - Unstop Edition
FastAPI + Jinja2 + SQLite + Tailwind CSS + WebSockets + Alpine.js
"""

from fastapi import FastAPI, Request, Form, HTTPException, WebSocket, WebSocketDisconnect, Query, Cookie, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
from typing import List, Optional
import enum
import random
import string
import json
import asyncio
import hashlib
import secrets

# ==================== DATABASE SETUP ====================

SQLALCHEMY_DATABASE_URL = "sqlite:///./campus_events.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== ENUMS ====================

class ParticipantStatus(str, enum.Enum):
    registered = "registered"
    under_review = "under_review"
    shortlisted = "shortlisted"
    confirmed = "confirmed"
    waitlisted = "waitlisted"
    rejected = "rejected"

class EventCategory(str, enum.Enum):
    hackathon = "hackathon"
    workshop = "workshop"
    cultural = "cultural"
    webinar = "webinar"
    competition = "competition"

class StageStatus(str, enum.Enum):
    locked = "locked"
    active = "active"
    completed = "completed"

# ==================== MODELS ====================

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    date = Column(DateTime, nullable=False)
    deadline = Column(DateTime, nullable=False)  # Registration deadline
    is_open = Column(Boolean, default=True)
    
    # Unstop-style fields
    banner_url = Column(String, default="/static/default-banner.jpg")
    logo_url = Column(String, default="/static/default-logo.png")
    category = Column(SQLEnum(EventCategory), default=EventCategory.hackathon)
    prize_pool = Column(String, default="Certificates")
    participant_limit = Column(Integer, default=500)
    organizer = Column(String, default="Campus Events Team")
    eligibility = Column(String, default="All students welcome")
    
    participants = relationship("Participant", back_populates="event")
    announcements = relationship("Announcement", back_populates="event", order_by="desc(Announcement.created_at)")
    stages = relationship("Stage", back_populates="event", order_by="Stage.order")

class Stage(Base):
    __tablename__ = "stages"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(SQLEnum(StageStatus), default=StageStatus.locked)
    order = Column(Integer, default=0)
    
    event = relationship("Event", back_populates="stages")

class Participant(Base):
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    ticket_id = Column(String, unique=True, nullable=False)
    status = Column(SQLEnum(ParticipantStatus), default=ParticipantStatus.registered)
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    event = relationship("Event", back_populates="participants")

class Announcement(Base):
    __tablename__ = "announcements"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    event = relationship("Event", back_populates="announcements")

# ==================== CREATE TABLES ====================

Base.metadata.create_all(bind=engine)

# ==================== WEBSOCKET CONNECTION MANAGER ====================

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, event_id: int):
        await websocket.accept()
        if event_id not in self.active_connections:
            self.active_connections[event_id] = []
        self.active_connections[event_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, event_id: int):
        if event_id in self.active_connections:
            self.active_connections[event_id].remove(websocket)
    
    async def broadcast(self, event_id: int, message: dict):
        if event_id in self.active_connections:
            for connection in self.active_connections[event_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

# ==================== HELPERS ====================

def generate_ticket_id():
    """Generate unique ticket ID like EVT-492"""
    return f"EVT-{random.randint(100, 999)}"

def get_db():
    return SessionLocal()

def get_status_step(status: ParticipantStatus) -> int:
    """Get step number for visual stepper"""
    steps = {
        ParticipantStatus.registered: 1,
        ParticipantStatus.under_review: 2,
        ParticipantStatus.shortlisted: 3,
        ParticipantStatus.confirmed: 4,
        ParticipantStatus.waitlisted: 3,
        ParticipantStatus.rejected: 2,
    }
    return steps.get(status, 1)

# ==================== APP SETUP ====================

app = FastAPI(title="Campus Event Manager - Unstop Edition")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add custom filters to Jinja2
templates.env.globals['get_status_step'] = get_status_step
templates.env.globals['now'] = datetime.utcnow

# ==================== ADMIN AUTHENTICATION ====================

# Simple admin credentials (in production, use environment variables and proper hashing)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("eventplan2026".encode()).hexdigest()
SECRET_KEY = secrets.token_hex(32)  # Session secret

# Simple session storage (in production, use Redis or database)
admin_sessions = {}

def hash_password(password: str) -> str:
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_admin(request: Request) -> bool:
    """Check if request has valid admin session"""
    session_token = request.cookies.get("admin_session")
    if session_token and session_token in admin_sessions:
        # Check if session is not expired (24 hours)
        session_data = admin_sessions[session_token]
        if datetime.utcnow() < session_data["expires"]:
            return True
        else:
            # Session expired, remove it
            del admin_sessions[session_token]
    return False

def require_admin(request: Request):
    """Dependency to require admin authentication"""
    if not verify_admin(request):
        raise HTTPException(status_code=303, headers={"Location": "/admin/login?next=" + request.url.path})

# ==================== MOCK DATA INITIALIZATION ====================

@app.on_event("startup")
def init_mock_data():
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(Event).count() > 0:
        db.close()
        return
    
    # Create Events with Unstop-style data
    event1 = Event(
        title="Hackathon 2026",
        description="48-hour coding marathon! Build innovative solutions to real-world problems. Form teams of up to 4 members and compete for amazing prizes. Mentors from top tech companies will guide you through the journey.",
        date=datetime(2026, 2, 15, 9, 0),
        deadline=datetime(2026, 2, 10, 23, 59),
        is_open=True,
        category=EventCategory.hackathon,
        prize_pool="$10,000 + Internships",
        participant_limit=500,
        organizer="Tech Club",
        eligibility="All undergraduate and graduate students",
        banner_url="https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=1200",
        logo_url="https://img.icons8.com/fluency/96/code.png"
    )
    event2 = Event(
        title="AI Workshop",
        description="Hands-on workshop on Machine Learning and AI. Learn to build your first neural network from scratch! No prior ML experience required. Bring your laptop with Python installed.",
        date=datetime(2026, 2, 20, 14, 0),
        deadline=datetime(2026, 2, 18, 23, 59),
        is_open=True,
        category=EventCategory.workshop,
        prize_pool="Certificates + Swag",
        participant_limit=100,
        organizer="AI Research Lab",
        eligibility="Anyone interested in AI/ML",
        banner_url="https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1200",
        logo_url="https://img.icons8.com/fluency/96/artificial-intelligence.png"
    )
    event3 = Event(
        title="Cultural Fest 2026",
        description="The biggest cultural extravaganza of the year! Dance, music, drama, and more. Showcase your talent and win exciting prizes.",
        date=datetime(2026, 3, 5, 10, 0),
        deadline=datetime(2026, 3, 1, 23, 59),
        is_open=True,
        category=EventCategory.cultural,
        prize_pool="$5,000 + Trophies",
        participant_limit=1000,
        organizer="Cultural Committee",
        eligibility="All students",
        banner_url="https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=1200",
        logo_url="https://img.icons8.com/fluency/96/theatre-mask.png"
    )
    
    db.add_all([event1, event2, event3])
    db.commit()
    db.refresh(event1)
    db.refresh(event2)
    
    # Create Stages for Hackathon
    stages1 = [
        Stage(event_id=event1.id, name="Registration", description="Sign up and form your team", order=1, status=StageStatus.active, start_date=datetime(2026, 1, 15), end_date=datetime(2026, 2, 10)),
        Stage(event_id=event1.id, name="Idea Submission", description="Submit your project idea", order=2, status=StageStatus.locked, start_date=datetime(2026, 2, 11), end_date=datetime(2026, 2, 12)),
        Stage(event_id=event1.id, name="Hacking Period", description="48 hours of coding", order=3, status=StageStatus.locked, start_date=datetime(2026, 2, 15), end_date=datetime(2026, 2, 17)),
        Stage(event_id=event1.id, name="Final Presentation", description="Demo your project to judges", order=4, status=StageStatus.locked, start_date=datetime(2026, 2, 17), end_date=datetime(2026, 2, 17)),
    ]
    
    # Create Stages for Workshop
    stages2 = [
        Stage(event_id=event2.id, name="Registration", description="Secure your spot", order=1, status=StageStatus.active, start_date=datetime(2026, 2, 1), end_date=datetime(2026, 2, 18)),
        Stage(event_id=event2.id, name="Pre-Workshop Setup", description="Install required software", order=2, status=StageStatus.locked, start_date=datetime(2026, 2, 19), end_date=datetime(2026, 2, 19)),
        Stage(event_id=event2.id, name="Workshop Day", description="Hands-on learning", order=3, status=StageStatus.locked, start_date=datetime(2026, 2, 20), end_date=datetime(2026, 2, 20)),
    ]
    
    db.add_all(stages1 + stages2)
    
    # Create Sample Participants
    participants = [
        Participant(event_id=event1.id, name="Alice Johnson", email="alice@university.edu", ticket_id="EVT-101", status=ParticipantStatus.confirmed),
        Participant(event_id=event1.id, name="Bob Smith", email="bob@university.edu", ticket_id="EVT-102", status=ParticipantStatus.under_review),
        Participant(event_id=event1.id, name="Carol White", email="carol@university.edu", ticket_id="EVT-103", status=ParticipantStatus.rejected),
        Participant(event_id=event1.id, name="Dan Brown", email="dan@university.edu", ticket_id="EVT-104", status=ParticipantStatus.shortlisted),
        Participant(event_id=event2.id, name="Eva Garcia", email="eva@university.edu", ticket_id="EVT-201", status=ParticipantStatus.confirmed),
        Participant(event_id=event2.id, name="Frank Lee", email="frank@university.edu", ticket_id="EVT-202", status=ParticipantStatus.registered),
    ]
    
    for p in participants:
        db.add(p)
    
    # Create Sample Announcements
    announcements = [
        Announcement(event_id=event1.id, message="Registration deadline extended to Feb 10th!"),
        Announcement(event_id=event1.id, message="New sponsor announcement: TechCorp is joining us with exclusive internship opportunities!"),
    ]
    for a in announcements:
        db.add(a)
    
    db.commit()
    db.close()
    print("Mock data initialized with Unstop-style content!")

# ==================== WEBSOCKET ENDPOINT ====================

@app.websocket("/ws/event/{event_id}")
async def websocket_endpoint(websocket: WebSocket, event_id: int):
    await manager.connect(websocket, event_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, event_id)

# ==================== PUBLIC ROUTES ====================

@app.get("/", response_class=HTMLResponse)
def home(request: Request, category: Optional[str] = None, search: Optional[str] = None):
    """Discovery Dashboard - List all open events with filters"""
    db = SessionLocal()
    query = db.query(Event).filter(Event.is_open == True)
    
    if category and category != "all":
        query = query.filter(Event.category == category)
    
    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
    
    events = query.all()
    
    # Get participant counts for each event
    event_data = []
    for event in events:
        count = db.query(Participant).filter(Participant.event_id == event.id).count()
        event_data.append({"event": event, "participant_count": count})
    
    db.close()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "event_data": event_data,
        "current_category": category or "all",
        "search_query": search or ""
    })

@app.get("/event/{event_id}", response_class=HTMLResponse)
def event_detail(request: Request, event_id: int, tab: str = "overview"):
    """Event Microsite with Tabs"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        db.close()
        raise HTTPException(status_code=404, detail="Event not found")
    
    participant_count = db.query(Participant).filter(Participant.event_id == event_id).count()
    announcements = db.query(Announcement).filter(Announcement.event_id == event_id).order_by(Announcement.created_at.desc()).all()
    stages = db.query(Stage).filter(Stage.event_id == event_id).order_by(Stage.order).all()
    
    db.close()
    return templates.TemplateResponse("event.html", {
        "request": request, 
        "event": event,
        "participant_count": participant_count,
        "announcements": announcements,
        "stages": stages,
        "active_tab": tab,
        "success": request.query_params.get("success"),
        "ticket_id": request.query_params.get("ticket_id")
    })

@app.post("/event/{event_id}/register", response_class=HTMLResponse)
def register_for_event(request: Request, event_id: int, name: str = Form(...), email: str = Form(...)):
    """Submit registration and get ticket ID"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        db.close()
        raise HTTPException(status_code=404, detail="Event not found")
    
    if not event.is_open:
        db.close()
        raise HTTPException(status_code=400, detail="Event registration is closed")
    
    # Check deadline
    if datetime.utcnow() > event.deadline:
        db.close()
        raise HTTPException(status_code=400, detail="Registration deadline has passed")
    
    # Check for duplicate registration
    existing_registration = db.query(Participant).filter(
        Participant.event_id == event_id,
        Participant.email == email.lower().strip()
    ).first()
    if existing_registration:
        db.close()
        return RedirectResponse(
            url=f"/event/{event_id}?error=duplicate&ticket_id={existing_registration.ticket_id}", 
            status_code=303
        )
    
    # Check event capacity
    current_count = db.query(Participant).filter(Participant.event_id == event_id).count()
    if current_count >= event.participant_limit:
        db.close()
        return RedirectResponse(url=f"/event/{event_id}?error=capacity_full", status_code=303)
    
    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email.strip()):
        db.close()
        return RedirectResponse(url=f"/event/{event_id}?error=invalid_email", status_code=303)
    
    # Generate unique ticket ID
    while True:
        ticket_id = generate_ticket_id()
        existing = db.query(Participant).filter(Participant.ticket_id == ticket_id).first()
        if not existing:
            break
    
    participant = Participant(
        event_id=event_id,
        name=name.strip(),
        email=email.lower().strip(),
        ticket_id=ticket_id,
        status=ParticipantStatus.registered
    )
    db.add(participant)
    db.commit()
    db.close()
    
    return RedirectResponse(url=f"/event/{event_id}?success=1&ticket_id={ticket_id}", status_code=303)

@app.get("/track", response_class=HTMLResponse)
def track_page(request: Request):
    """Status tracker with visual stepper and virtual ticket"""
    query = request.query_params.get("q", "").strip()
    registrations = []
    
    db = SessionLocal()
    if query:
        registrations = db.query(Participant).filter(
            (Participant.email == query) | (Participant.ticket_id == query.upper())
        ).all()
        # Eagerly load event data to avoid DetachedInstanceError
        for reg in registrations:
            _ = reg.event  # Force load the relationship
    
    response = templates.TemplateResponse("track.html", {
        "request": request,
        "query": query,
        "registrations": registrations
    })
    db.close()
    return response

@app.get("/ticket/{ticket_id}", response_class=HTMLResponse)
def virtual_ticket(request: Request, ticket_id: str):
    """Virtual ticket page with QR code"""
    db = SessionLocal()
    participant = db.query(Participant).filter(Participant.ticket_id == ticket_id.upper()).first()
    
    if not participant:
        db.close()
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    event = db.query(Event).filter(Event.id == participant.event_id).first()
    db.close()
    
    return templates.TemplateResponse("ticket.html", {
        "request": request,
        "participant": participant,
        "event": event
    })

# ==================== ADMIN ROUTES ====================

@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    """Show admin login page"""
    # If already logged in, redirect to dashboard
    if verify_admin(request):
        return RedirectResponse(url="/admin", status_code=303)
    
    error = request.query_params.get("error")
    next_url = request.query_params.get("next", "/admin")
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "error": error,
        "next": next_url
    })

@app.post("/admin/login", response_class=HTMLResponse)
def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next_url: str = Form("/admin")
):
    """Handle admin login"""
    if username == ADMIN_USERNAME and hash_password(password) == ADMIN_PASSWORD_HASH:
        # Create session
        session_token = secrets.token_urlsafe(32)
        admin_sessions[session_token] = {
            "username": username,
            "created": datetime.utcnow(),
            "expires": datetime.utcnow() + timedelta(hours=24)
        }
        
        response = RedirectResponse(url=next_url, status_code=303)
        response.set_cookie(
            key="admin_session",
            value=session_token,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite="lax"
        )
        return response
    
    return RedirectResponse(url="/admin/login?error=invalid", status_code=303)

@app.get("/admin/logout")
def admin_logout(request: Request):
    """Handle admin logout"""
    session_token = request.cookies.get("admin_session")
    if session_token and session_token in admin_sessions:
        del admin_sessions[session_token]
    
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    return response

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Admin Control Center with Analytics"""
    # Check authentication
    if not verify_admin(request):
        return RedirectResponse(url="/admin/login?next=/admin", status_code=303)
    
    db = SessionLocal()
    events = db.query(Event).all()
    
    # Calculate analytics
    total_registrations = db.query(Participant).count()
    total_confirmed = db.query(Participant).filter(Participant.status == ParticipantStatus.confirmed).count()
    total_pending = db.query(Participant).filter(Participant.status.in_([
        ParticipantStatus.registered, 
        ParticipantStatus.under_review
    ])).count()
    
    approval_rate = round((total_confirmed / total_registrations * 100) if total_registrations > 0 else 0, 1)
    
    # Get per-event stats
    event_stats = []
    for event in events:
        total = db.query(Participant).filter(Participant.event_id == event.id).count()
        confirmed = db.query(Participant).filter(
            Participant.event_id == event.id,
            Participant.status == ParticipantStatus.confirmed
        ).count()
        pending = db.query(Participant).filter(
            Participant.event_id == event.id,
            Participant.status.in_([ParticipantStatus.registered, ParticipantStatus.under_review])
        ).count()
        event_stats.append({
            "event": event,
            "total": total,
            "confirmed": confirmed,
            "pending": pending
        })
    
    db.close()
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "event_stats": event_stats,
        "analytics": {
            "total_registrations": total_registrations,
            "total_confirmed": total_confirmed,
            "total_pending": total_pending,
            "approval_rate": approval_rate
        }
    })

# Event creation routes - must come before /admin/event/{event_id} to avoid route collision
@app.get("/admin/event/create", response_class=HTMLResponse)
def create_event_page(request: Request):
    """Show event creation form"""
    if not verify_admin(request):
        return RedirectResponse(url="/admin/login?next=/admin/event/create", status_code=303)
    
    return templates.TemplateResponse("admin_event_form.html", {
        "request": request,
        "event": None,
        "categories": [cat.value for cat in EventCategory],
        "is_edit": False
    })

@app.post("/admin/event/create", response_class=HTMLResponse)
def create_event(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    date: str = Form(...),
    deadline: str = Form(...),
    category: str = Form(...),
    prize_pool: str = Form("Certificates"),
    participant_limit: int = Form(500),
    organizer: str = Form("Campus Events Team"),
    eligibility: str = Form("All students welcome"),
    banner_url: str = Form("/static/default-banner.jpg"),
    logo_url: str = Form("/static/default-logo.png")
):
    """Create a new event"""
    if not verify_admin(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    
    db = SessionLocal()
    
    event = Event(
        title=title.strip(),
        description=description.strip(),
        date=datetime.strptime(date, "%Y-%m-%dT%H:%M"),
        deadline=datetime.strptime(deadline, "%Y-%m-%dT%H:%M"),
        category=EventCategory(category),
        prize_pool=prize_pool.strip(),
        participant_limit=participant_limit,
        organizer=organizer.strip(),
        eligibility=eligibility.strip(),
        banner_url=banner_url.strip() or "/static/default-banner.jpg",
        logo_url=logo_url.strip() or "/static/default-logo.png",
        is_open=True
    )
    db.add(event)
    db.commit()
    new_event_id = event.id
    db.close()
    
    return RedirectResponse(url=f"/admin/event/{new_event_id}?success=event_created", status_code=303)


@app.get("/admin/event/{event_id}", response_class=HTMLResponse)
def admin_event(request: Request, event_id: int):
    """Participant management with bulk actions"""
    if not verify_admin(request):
        return RedirectResponse(url=f"/admin/login?next=/admin/event/{event_id}", status_code=303)
    
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        db.close()
        raise HTTPException(status_code=404, detail="Event not found")
    
    participants = db.query(Participant).filter(Participant.event_id == event_id).order_by(Participant.registered_at.desc()).all()
    announcements = db.query(Announcement).filter(Announcement.event_id == event_id).order_by(Announcement.created_at.desc()).all()
    
    # Analytics for this event
    total = len(participants)
    confirmed = sum(1 for p in participants if p.status == ParticipantStatus.confirmed)
    pending = sum(1 for p in participants if p.status in [ParticipantStatus.registered, ParticipantStatus.under_review])
    
    db.close()
    
    return templates.TemplateResponse("admin_event.html", {
        "request": request,
        "event": event,
        "participants": participants,
        "announcements": announcements,
        "stats": {"total": total, "confirmed": confirmed, "pending": pending},
        "success": request.query_params.get("success")
    })

@app.post("/admin/event/{event_id}/update_status", response_class=HTMLResponse)
def update_participant_status(
    request: Request, 
    event_id: int, 
    participant_id: int = Form(...), 
    status: str = Form(...)
):
    """Update single participant status"""
    db = SessionLocal()
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        db.close()
        raise HTTPException(status_code=404, detail="Participant not found")
    
    participant.status = ParticipantStatus(status)
    db.commit()
    db.close()
    
    return RedirectResponse(url=f"/admin/event/{event_id}?success=status_updated", status_code=303)

@app.post("/admin/event/{event_id}/bulk_update", response_class=HTMLResponse)
def bulk_update_status(
    request: Request,
    event_id: int,
    participant_ids: str = Form(...),
    action: str = Form(...)
):
    """Bulk update participant statuses"""
    db = SessionLocal()
    
    ids = [int(id.strip()) for id in participant_ids.split(",") if id.strip()]
    
    status_map = {
        "confirm_all": ParticipantStatus.confirmed,
        "reject_all": ParticipantStatus.rejected,
        "review_all": ParticipantStatus.under_review,
    }
    
    if action in status_map:
        db.query(Participant).filter(Participant.id.in_(ids)).update(
            {"status": status_map[action]}, 
            synchronize_session=False
        )
        db.commit()
    
    db.close()
    return RedirectResponse(url=f"/admin/event/{event_id}?success=bulk_updated", status_code=303)

@app.post("/admin/event/{event_id}/announce", response_class=HTMLResponse)
async def post_announcement(request: Request, event_id: int, message: str = Form(...)):
    """Post announcement and broadcast via WebSocket"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        db.close()
        raise HTTPException(status_code=404, detail="Event not found")
    
    announcement = Announcement(
        event_id=event_id,
        message=message
    )
    db.add(announcement)
    db.commit()
    
    # Broadcast to WebSocket clients
    await manager.broadcast(event_id, {
        "type": "announcement",
        "message": message,
        "timestamp": datetime.utcnow().strftime("%b %d at %I:%M %p")
    })
    
    db.close()
    
    return RedirectResponse(url=f"/admin/event/{event_id}?success=announcement_posted", status_code=303)

@app.get("/admin/event/{event_id}/export")
def export_participants(event_id: int):
    """Export participants as CSV"""
    db = SessionLocal()
    participants = db.query(Participant).filter(Participant.event_id == event_id).all()
    
    import csv
    from io import StringIO
    from fastapi.responses import Response
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Ticket ID", "Name", "Email", "Status", "Registered At"])
    
    for p in participants:
        writer.writerow([p.ticket_id, p.name, p.email, p.status.value, p.registered_at.strftime("%Y-%m-%d %H:%M")])
    
    db.close()
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=event_{event_id}_participants.csv"}
    )
# ==================== OTHER EVENT MANAGEMENT ROUTES ====================


@app.get("/admin/event/{event_id}/edit", response_class=HTMLResponse)
def edit_event_page(request: Request, event_id: int):
    """Show event edit form"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        db.close()
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.close()
    return templates.TemplateResponse("admin_event_form.html", {
        "request": request,
        "event": event,
        "categories": [cat.value for cat in EventCategory],
        "is_edit": True
    })

@app.post("/admin/event/{event_id}/edit", response_class=HTMLResponse)
def update_event(
    request: Request,
    event_id: int,
    title: str = Form(...),
    description: str = Form(...),
    date: str = Form(...),
    deadline: str = Form(...),
    category: str = Form(...),
    prize_pool: str = Form("Certificates"),
    participant_limit: int = Form(500),
    organizer: str = Form("Campus Events Team"),
    eligibility: str = Form("All students welcome"),
    banner_url: str = Form("/static/default-banner.jpg"),
    logo_url: str = Form("/static/default-logo.png"),
    is_open: bool = Form(True)
):
    """Update an existing event"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        db.close()
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.title = title.strip()
    event.description = description.strip()
    event.date = datetime.strptime(date, "%Y-%m-%dT%H:%M")
    event.deadline = datetime.strptime(deadline, "%Y-%m-%dT%H:%M")
    event.category = EventCategory(category)
    event.prize_pool = prize_pool.strip()
    event.participant_limit = participant_limit
    event.organizer = organizer.strip()
    event.eligibility = eligibility.strip()
    event.banner_url = banner_url.strip() or "/static/default-banner.jpg"
    event.logo_url = logo_url.strip() or "/static/default-logo.png"
    event.is_open = is_open
    
    db.commit()
    db.close()
    
    return RedirectResponse(url=f"/admin/event/{event_id}?success=event_updated", status_code=303)

@app.post("/admin/event/{event_id}/delete", response_class=HTMLResponse)
def delete_event(request: Request, event_id: int):
    """Delete an event and all its participants"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        db.close()
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete all related data
    db.query(Participant).filter(Participant.event_id == event_id).delete()
    db.query(Announcement).filter(Announcement.event_id == event_id).delete()
    db.query(Stage).filter(Stage.event_id == event_id).delete()
    db.delete(event)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin?success=event_deleted", status_code=303)

@app.post("/admin/event/{event_id}/toggle", response_class=HTMLResponse)
def toggle_event_status(request: Request, event_id: int):
    """Toggle event open/closed status"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        db.close()
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.is_open = not event.is_open
    db.commit()
    db.close()
    
    return RedirectResponse(url=f"/admin/event/{event_id}?success=status_toggled", status_code=303)

# ==================== RUN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
