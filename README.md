# MwananchiLink — District Citizen Response System

> MwananchiLink is a unified command centre for Tanzanian wards/districts: citizens self-register and track approval (CIT-XXXXXXXXXX), file service requests (ISS-XXXXXXXXXX) via a 5-tile One-Stop Centre, get automatic SMS at every step; ward officers approve/reject, assign technicians + appointments and log calls within their own ward only, while district admins see everything district-wide with full dashboard, reports and audit trail.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite%20%2F%20PostgreSQL-003B57?style=flat-square&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-Government%20Use-blue?style=flat-square)

---

## Overview

DCRS is a full-stack Django web application for Tanzanian district local government. It gives ward officers a single platform to approve citizens in their own locality, run a One-Stop Emergency & Services Centre (water, electricity, waste, roads, security), schedule technician appointments, collect citizen feedback, and send real SMS via the SendAfrica gateway — with a complete audit trail and in-app notification inbox throughout. Citizens get their own lightweight portal to register, check status, file service requests, track appointments, and rate the service they received.

---

## How It Works — Start to Finish

**1. A citizen registers.** Anyone visits the public site and fills in the registration form (name, national ID, phone, gender, DOB, Region → District → Ward → Mtaa, optional photo). The record is created with status `PENDING` and a unique `CIT-XXXXXXXXXX` ID.

**2. The ward officer reviews it.** Officers only ever see citizens (and issues) inside their **own ward** — an officer in Mwananyamala never sees a Kariakoo registration. On the citizen's detail page the officer clicks **Approve** or **Reject**:
   - **Approve** → status flips to `APPROVED`, and the citizen is sent an SMS confirming it plus a web notification (if they have a linked login).
   - **Reject** → the officer must type a reason in a modal; it's saved on the record and sent to the citizen by SMS, along with a notification.

**3. The citizen logs in to their portal** and, once approved, sees a **One-Stop Emergency & Services Centre** tile grid — Water, Electricity, Waste, Roads, Security. Picking one opens the issue form with that category pre-selected (and their own citizen/ward pre-filled).

**4. The request lands with staff** as an `Issue` (`ISS-XXXXXXXXXX`), ward-scoped the same way citizens are. An officer assigns a **technician name and appointment date/time** — this fires another SMS + notification to the citizen with the visit details.

**5. If the citizen calls or texts the officer's phone directly** (SendAfrica has no inbound/shortcode webhook), the officer logs what was said into the issue's **SMS Conversation** thread and can send a reply from the same screen — a "staff-relayed" two-way SMS log that sits right next to the automatic outbound messages.

**6. Once the technician visits and the officer marks the issue `RESOLVED`**, the citizen gets an SMS + notification asking them to rate it. Back in the portal, they leave a **1–5 star rating and comment**, visible to staff on the same page afterward.

**7. Every status change is audited** (`AuditLog`) and every SMS — outbound or staff-logged inbound — is recorded in the **SMS Log** with real delivery status. SendAfrica pushes delivery confirmations back to a webhook, flipping `SENT` → `DELIVERED`/`FAILED` automatically. Staff can also **Compose** a one-off SMS or **Broadcast** to an entire ward at any time, and everyone (staff and citizens) gets a bell-icon **notification inbox** for registration, appointment, and resolution updates.

Throughout, `admin_user` (ADMIN) sees and can act on everything district-wide, while `officer_*` accounts are locked to their assigned ward — the officer-locality model the whole approval and service flow is built around.

---

## Screenshots

### Public — Landing Page & Login

| Landing Page | Officer Login |
|---|---|
| ![Landing Page](screenshots/landing-page.png) | ![Login](screenshots/login.png) |

The public landing page shows live system stats (citizens, open issues, pending approvals, SMS count) and live issue feed. Officers sign in via the dedicated login form with role-based redirect.

---

### Staff — Operations Dashboard

![Dashboard](screenshots/dashboard.png)

The main staff landing page after login. Real-time stat cards, recent citizen registrations, recent issues with status badges, and the last 8 activity feed entries linking to the full audit trail.

---

### Citizen Management

| Citizens List | Citizen Detail |
|---|---|
| ![Citizens](screenshots/citizens-page.png) | ![Citizen Detail](screenshots/citizen-detail-page.png) |

The citizens list shows all registered citizens with ID, ward, gender, phone, and approval status badge. The detail page has a two-column layout: left sidebar with Quick Actions (Edit, Status Card, Send SMS, Log Issue, Delete), Identity, and Location cards; right column with linked issues table.

---

### Issue Tracking

| Issues List | Issue Detail |
|---|---|
| ![Issues](screenshots/issues-page.png) | ![Issue Detail](screenshots/issue-detail-page.png) |

The issue list shows all community reports with reference number, category, ward, priority badge, and status badge. The detail page shows the full description, internal notes (staff only), comment thread with per-comment delete, and a right sidebar with assignment details, citizen mini-profile, and quick actions.

---

### SMS Communications

| Compose SMS | Broadcast to Ward | SMS Log |
|---|---|---|
| ![Compose SMS](screenshots/compose-sms.png) | ![Broadcast](screenshots/broadcast-sms.png) | ![SMS Log](screenshots/sms-logs.png) |

**Compose** sends a direct message to a single phone number. **Broadcast** targets all approved citizens in a specified ward. **SMS Log** shows the full delivery history with stat cards (total / delivered / pending / failed) and status-coded badges per message.

---

### Analytics & Reports

| Registration Report | Audit Trail |
|---|---|
| ![Reports](screenshots/reports-page.png) | ![Audit Trail](screenshots/audit-trail.png) |

The **Registration Report** has live stat cards with quick-filter shortcuts, a filter form (ward + status), and a full citizen table with region, district, and View links. The **Audit Trail** logs every CREATE / UPDATE / DELETE / SEND action with colour-coded badges, entity icons, actor avatars, and split date/time columns.

---

### Citizen Portal

| My Portal | My Status Card | Report Issue |
|---|---|---|
| ![Citizen Portal](screenshots/citizen-portal.png) | ![Status](screenshots/citizen-status-page.png) | ![Report Issue](screenshots/citizen-report-page.png) |

Citizens have a completely separate portal (no staff sidebar). The portal shows a registration card, 4 stat cards, two quick-action cards (Report Issue, My Status), and a full issues table. The Status Card shows the approval state with a coloured alert banner and all registration details. The Report Issue form is clean and role-aware — Back/Cancel returns to the portal.

---

## Features

| Module | Capability |
|---|---|
| **Citizen Registration** | Full profiles — national ID, DOB, gender, photo, Region→District→Ward→Mtaa, approval workflow (Pending / Approved / Rejected / Suspended) |
| **Ward-Scoped Approval** | Officers only see/act on citizens and issues in their own ward (admins see all); dedicated Approve/Reject actions with a required rejection reason, both SMS + notification on the outcome |
| **One-Stop Services Centre** | Citizen-facing tile grid — Water, Electricity, Waste, Roads, Security — that pre-fills a service request in the right category |
| **Appointments & Feedback** | Officers assign a technician name + appointment date/time (SMS on assignment); once resolved, the citizen leaves a 1–5 star rating + comment, visible to staff |
| **Issue Tracking** | Log, categorise, prioritise (Low→Critical), assign to officer, escalate to district, resolve, close |
| **Comments** | Staff thread on each issue with internal (staff-only) flag and per-comment delete |
| **Real SMS via SendAfrica** | Live outbound SMS (not simulated) with delivery-status webhook, error handling, and a Kiswahili template library |
| **Staff-Relayed Two-Way SMS** | Officers log what a citizen said over a phone call directly on the issue, threaded next to the automatic outbound messages, with an optional instant reply |
| **Notification Inbox** | Bell-icon dropdown + full inbox for both staff and citizens — registration, appointment, and resolution updates, read/unread |
| **Role-Based Access** | ADMIN, OFFICER, CITIZEN — separate UIs, separate post-login redirects, role-aware page elements |
| **Reports** | Registration report filterable by ward and status; quick-filter shortcut cards |
| **Audit Trail** | Every citizen/issue action logged in real time (via model signals) with actor, entity type, entity ID, summary, and timestamp |
| **Geographic Hierarchy** | Region → District → Ward → Mtaa mirroring Tanzania's official administrative boundaries |
| **Dark Mode** | Full light/dark theme toggle persisted in localStorage |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 5.2 |
| Database | SQLite (dev) / PostgreSQL (production) |
| Frontend | Bootstrap 5.3, Bootstrap Icons 1.11, Inter font, vanilla JS |
| Auth | Django auth with custom User model (role + phone + ward) |
| SMS | **SendAfrica** (`api.sendafrica.online`) — real outbound send + delivery webhook; falls back to an internal simulator automatically when no API key is configured |
| Deployment | Gunicorn + Nginx + Let's Encrypt on Ubuntu 22.04 |

---

## Quick Start

```bash
# 1. Clone and enter
git clone <repo-url>
cd DCRS

# 2. Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements/development.txt

# 4. Migrate and seed
python manage.py migrate
python manage.py seed

# 5. Run
python manage.py runserver
```

Visit `http://127.0.0.1:8000`

---

## SMS Configuration (SendAfrica)

SMS works out of the box with **no setup** — leave `SENDAFRICA_API_KEY` blank in `.env` and every send falls back to an internal simulator that logs messages instantly as `SENT` (no real network calls, safe for local dev/demo).

To send real SMS:

```bash
# .env
SENDAFRICA_BASE_URL=https://api.sendafrica.online
SENDAFRICA_API_KEY=your-key-from-the-sendafrica-dashboard
SENDAFRICA_SENDER_ID=                       # optional — leave blank for default
```

Get a key at `https://sendafrica.online` → Settings → API Keys. Then, in the SendAfrica dashboard under **SMS → Settings → Callback URLs**, point delivery reports at your deployed domain:

```
https://<your-domain>/portal/sms/callback/
```

This lets `SMSCallbackView` flip `SENT` → `DELIVERED`/`FAILED` automatically as the network confirms delivery. See `apps/notifications/README.md` for the full integration details.

### Where SMS goes out — every trigger

Communication is deliberate: whenever something about a citizen's registration or a service request changes, the right person gets a text. Issue-flow messages go through `send_issue_update_sms` (in `apps/notifications/services.py`); everything else goes through `send_sms`.

| Event | Who is texted | Message covers |
|---|---|---|
| Citizen registration created | The ward's officer(s) **and every admin** | "New citizen registration awaiting your approval" |
| Registration approved | The citizen | Approval + "log in to your citizen portal" |
| Registration rejected | The citizen | The rejection reason |
| Issue submitted | The citizen | Confirmation with reference no. |
| Issue → `IN_PROGRESS` | The citizen | "now being handled by the ward office" |
| Issue → `ESCALATED` | The citizen | "escalated to district level for priority action" |
| Issue → `RESOLVED` | The citizen | "resolved — please rate your experience" |
| Issue → `CLOSED` | The citizen | "has been closed" |
| Issue reopened (→ `OPEN`) | The citizen | "has been reopened" |
| Officer assigned | The citizen | Assignee's name |
| Technician appointment set | The citizen | Technician name + visit date/time |
| Staff posts a public comment | The citizen | The comment text |
| Citizen rates a resolved issue | The citizen | Thank-you for the feedback |
| Staff Compose / Broadcast | The recipient(s) | Ad-hoc one-off and ward-wide messages |

**Guard:** `send_issue_update_sms` only texts citizens whose registration is `APPROVED` and who have a phone number — pending/rejected registrations never get issue SMS (their approval/rejection text is the SMS for them).

**Credits:** if the SendAfrica account runs out of credits, sends fail with `[insufficient_credits]` and land in the SMS Log as `FAILED` — never a crash. Check the balance with `GET https://api.sendafrica.online/v1/credits/balance` (header `X-API-Key: <key>`) and top up from the dashboard. Typical cost per message: TZS 22 (1 credit).

---

## Test Credentials

All accounts use password **`test1234`**.

| Role | Username | Ward | Lands on |
|---|---|---|---|
| Superuser / Officer | `admin` | — (sees all) | Staff dashboard |
| Admin | `admin_user` | — (sees all) | Staff dashboard |
| Officer | `officer_kinondoni` | Mwananyamala | Staff dashboard |
| Officer | `officer_ilala` | Kariakoo | Staff dashboard |
| Citizen | `citizen_user` | Mwananyamala | Citizen portal |

Login: `http://127.0.0.1:8000/accounts/login/`

Each officer's ward has at least one `PENDING` citizen seeded so the Approve/Reject flow is demoable immediately after a fresh seed (`officer_kinondoni` → Halima Ramadhani, `officer_ilala` → Chausiku Nyundo).

Re-seed at any time:
```bash
python manage.py seed          # safe, skips existing rows
python manage.py seed --flush  # wipe and re-seed fresh — resets to the pristine demo state above
```

---

## Project Structure

```
DCRS/
├── apps/
│   ├── accounts/        # Custom User model, login, OTP stub, WardScopedQuerysetMixin
│   ├── citizens/        # Citizen profiles, ward-scoped approve/reject, portal, seed command
│   ├── issues/          # Issues, One-Stop Services Centre, appointments, feedback, escalation
│   ├── localities/      # Region → District → Ward → Mtaa
│   ├── notifications/   # SendAfrica SMS, delivery webhook, notification inbox, two-way SMS relay
│   └── reports/         # Dashboard, registration report, audit trail
├── config/              # settings.py, urls.py, wsgi.py
├── screenshots/         # App screenshots (this README)
├── static/css/app.css   # All custom styles + dark mode
├── static/js/app.js     # Theme toggle, sidebar, cascading dropdowns
├── templates/           # All HTML — base.html with 3 shells (public/citizen/staff)
├── requirements/
│   ├── base.txt         # Django, Pillow
│   └── development.txt  # + dev tools
├── manage.py
├── seed.py              # Legacy (use: python manage.py seed)
├── README.md
└── DEPLOY.md            # Full production deployment guide
```

---

## Switching to PostgreSQL

Update `DATABASES` in `config/settings.py` (see `DEPLOY.md` for the exact block), then:

```bash
pip install psycopg2-binary
python manage.py migrate
python manage.py seed
```

No application code changes needed — the seed command and all views are database-agnostic.
