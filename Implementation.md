# DCRS — Digital Citizen Response System

A full-stack Django web application for Tanzanian district local government. Gives ward officers a single platform for citizen registration, a One-Stop Emergency & Services Centre, technician scheduling, citizen feedback, and real SMS communications via SendAfrica — with a complete audit trail and in-app notification inbox.

**Context:** RIDC PT Innovation Hackathon 2026 — Software Category, Smart Governance & Public Service Delivery.

## Tech Stack

- **Backend:** Python 3.12 / Django 5.2
- **Database:** PostgreSQL (production) / SQLite (development)
- **Frontend:** Server-rendered, Bootstrap-based responsive UI with minimal client-side JavaScript (light/dark mode)
- **Communication:** SendAfrica SMS gateway (real API in production, internal simulator in dev)
- **Deployment:** Gunicorn + Nginx, served over SSL (see DEPLOY.md)

## Project Structure

```
DCRS/
├── Implementation.md                  # This file
├── manage.py                  # Django management entry point
├── seed.py                    # Demo data seeder
├── .env.example               # Environment variable template
├── config/                    # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                      # All Django apps (flat namespace)
│   ├── accounts/              # Custom User model, auth backends, login views
│   ├── localities/            # Region → District → Ward → Mtaa hierarchy
│   ├── citizens/              # Citizen registration, approval workflow
│   ├── issues/                # Service requests, technician scheduling, feedback
│   ├── notifications/         # In-app notification inbox, SMS templates, SMS log
│   └── reports/               # Dashboard, registration reports, audit trail
├── templates/                 # Project-level templates (base, auth, landing)
├── static/                    # CSS, JS, images
├── screenshots/               # README screenshots
├── requirements/              # Pip requirements files
├── DOCS/                      # Concept brief and design documents
│   ├── DCRS_Concept_Brief.docx
│   ├── DCRS Concept Brief.pdf
│   └── DCRS_Hackathon_Concept_Note.md
├── DCRS_SRS_Lodrick_Mushi.docx  # Software Requirements Specification
└── DEPLOY.md                  # Deployment guide (Nginx + Gunicorn + SSL)
```

## Core Domain

### Administrative Hierarchy (Tanzania)
```
Region → District → Ward → Mtaa (Street)
```
All data is scoped to this hierarchy. Ward officers only see citizens and issues within their own ward.

### User Roles
| Role | Capabilities |
|---|---|
| **Citizen** | Register, file service requests, track status, rate service, receive SMS updates |
| **Ward Officer** | Approve/reject registrations, assign technicians, manage issues within their ward, view dashboard |
| **District Admin** | Cross-ward visibility, escalation handling, system-wide reports and dashboards |

### Service Request Categories
1. Water
2. Electricity
3. Waste (Sanitation)
4. Roads
5. Security
6. Lighting
7. Other

## Key Features

- **Citizen Registration & Approval** — Self-registration with national ID, phone, full location (Region → District → Ward → Mtaa); ward officer approves/rejects with automatic SMS notification
- **Ward-Scoped Access Control** — Officers only see and act on data within their own ward
- **One-Stop Services Centre** — Category tile interface for filing service requests
- **Appointment & Technician Scheduling** — Officers assign technician + visit time; citizen notified automatically
- **Citizen Feedback Loop** — 1–5 star rating + comment after issue resolution
- **Automatic SMS Notifications** — Every state change triggers an SMS to the citizen via SendAfrica
- **Staff-Assisted SMS Log** — Officers log and reply to calls/texts, keeping communication history against each issue
- **In-App Notification Inbox** — Bell-icon inbox for staff and citizens (alongside SMS)
- **Escalation Path** — Issues exceeding ward capacity escalate to district level
- **Real-Time Dashboard & Reports** — Live counts, filterable registration reports by ward/status
- **Full Audit Trail** — Every action logged with actor, timestamp, and human-readable summary

## Data Models

### `apps.accounts.User` (extends AbstractUser)
- `role`: ADMIN / OFFICER / CITIZEN
- `phone_number`, `national_id`, `ward` (FK to localities.Ward)
- Custom auth backend: `UsernameOrPhoneBackend` (sign in with username or phone)

### `apps.localities` — Region, District, Ward, Mtaa
- FK chain: Region → District → Ward → Mtaa
- Each level is unique within its parent

### `apps.citizens.Citizen`
- Auto-generated `citizen_id` (CIT-XXXXXXXXXX)
- Full name, national ID, phone, gender, DOB, location FKs, profile photo
- `status`: PENDING → APPROVED / REJECTED / SUSPENDED
- `rejection_reason` field for rejected registrations

### `apps.issues.Issue`
- Auto-generated `reference_no` (ISS-XXXXXXXXXX)
- Linked to Citizen and Ward, category, priority, status
- `assigned_officer`, `assigned_technician_name`, `appointment_at`
- `rating` (1–5), `feedback_comment`, `internal_notes`
- `escalated_to_district` flag
- `IssueComment` model for threaded comments

### `apps.notifications`
- `Notification`: In-app bell-icon inbox (recipient, message, is_read, links to issue/citizen)
- `SMSTemplate`: Reusable SMS message templates
- `SMSLog`: Full delivery history with status (QUEUED/SENT/DELIVERED/FAILED), direction (OUTBOUND/INBOUND), linked to issue

## Development

### Setting Up Locally

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements/<file>

# Copy environment template and configure
cp .env.example .env
# Edit .env as needed (defaults work for SQLite dev)

# Run migrations
python manage.py migrate

# Seed demo data
python manage.py seed   # or: python seed.py

# Create superuser
python manage.py createsuperuser

# Run dev server
python manage.py runserver
```

### Key Environment Variables (.env)
- `SECRET_KEY` — Django secret key
- `DEBUG` — True/False
- `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` — Database config
- `SENDAFRICA_API_KEY`, `SENDAFRICA_SENDER_ID` — SMS gateway (leave blank for internal simulator)
- `CSRF_TRUSTED_ORIGINS` — Comma-separated trusted origins for production

## Design Principles

- **SMS-first:** Every status update is pushed via SMS — works for citizens with only a basic feature phone
- **Lightweight pages:** Minimal JS/CSS; loads on 2G/3G connections and low-end Android devices
- **No app install required:** Standard mobile browser
- **Ward-level isolation:** Data access is strictly scoped — officers never see cross-ward data
- **Full accountability:** Every create, update, and send action is logged with actor, timestamp, and summary

## Conventions

- Custom User model at `apps.accounts.User` with role-based choices (ADMIN/OFFICER/CITIZEN)
- Authentication via `UsernameOrPhoneBackend` — sign in with username or phone number
- Administrative hierarchy modelled as separate Region/District/Ward/Mtaa models with FKs
- All citizen-facing notifications go through the SMS module — never bypass it for status changes
- Audit logging via signals — every citizen/issue action emits an audit entry
- Bootstrap for all templates; consistent light/dark mode
- Class-based views; Django forms for form handling
- UUID-based auto-generated IDs: CIT-XXXXXXXXXX for citizens, ISS-XXXXXXXXXX for issues

## References

- [Concept Note (Markdown)](DOCS/DCRS_Hackathon_Concept_Note.md)
- [Concept Brief (PDF)](DOCS/DCRS%20Concept%20Brief.pdf)
- [SRS Document](DCRS_SRS_Lodrick_Mushi.docx)
- [Deployment Guide](DEPLOY.md)
