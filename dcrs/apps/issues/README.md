# apps/issues/

Manages community issues and service requests — both staff-logged community problems and citizen-filed One-Stop Centre requests. Supports full lifecycle tracking from open to closed, with officer assignment, technician/appointment scheduling, citizen feedback, district escalation, and comments.

## Models

### `Issue`

| Field | Type | Notes |
|---|---|---|
| `reference_no` | CharField (auto) | `ISS-XXXXXXXXXX` — generated on first save |
| `citizen` | ForeignKey → Citizen | Who reported the issue |
| `title` | CharField | Short description (max 180 chars) |
| `description` | TextField | Full details |
| `category` | CharField (choices) | `WATER`, `ELECTRICITY`, `SANITATION` ("Waste"), `ROAD` ("Roads"), `SECURITY`, `LIGHTING` (legacy), `OTHER` |
| `priority` | CharField (choices) | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `status` | CharField (choices) | See lifecycle below |
| `ward` | ForeignKey → Ward | Where the issue is located — this is what officer access is scoped by |
| `assigned_officer` | ForeignKey → User (nullable) | Officer handling the issue |
| `internal_notes` | TextField | Staff-only notes (not shown to citizens) |
| `escalated_to_district` | BooleanField | True when escalated beyond ward level |
| `closed_at` | DateTimeField | Set when status becomes CLOSED |
| `assigned_technician_name` | CharField | One-Stop Centre — who's been sent out (slide 21) |
| `appointment_at` | DateTimeField | One-Stop Centre — scheduled visit date/time; setting/changing this sends the citizen an SMS |
| `rating` | PositiveSmallIntegerField (1–5) | Citizen's star rating, settable once, only after `RESOLVED` |
| `feedback_comment` | TextField | Optional comment alongside the rating |

The first five categories (`WATER`, `ELECTRICITY`, `SANITATION`, `ROAD`, `SECURITY`) map directly onto the five **One-Stop Services Centre** tiles the citizen picks from; `LIGHTING` and `OTHER` remain available for staff-side logging but aren't tiles.

### `IssueComment`

| Field | Type | Notes |
|---|---|---|
| `issue` | ForeignKey → Issue | Parent issue |
| `author` | ForeignKey → User | Officer who wrote the comment |
| `body` | TextField | Comment text |
| `is_internal` | BooleanField | If True, only staff can see it |

## Status lifecycle

```
OPEN
 │
 ├──► IN_PROGRESS   (assigned to officer, technician/appointment may be set)
 │       │
 │       ├──► ESCALATED    (sent to district, beyond ward scope)
 │       │
 │       └──► RESOLVED     (problem fixed — citizen is prompted to rate the service)
 │                │
 │                └──► CLOSED    (confirmed resolved, record sealed)
 └──► CLOSED  (admin can force-close directly)
```

## Priority levels

| Priority | Meaning |
|---|---|
| LOW | Minor inconvenience, no urgency |
| MEDIUM | Affects some residents, should be addressed within weeks |
| HIGH | Significant impact, address within days |
| CRITICAL | Danger to life or property, immediate response required |

## Ward-scoped access

`IssueListView`, `IssueDetailView`, and `IssueUpdateView` mix in `apps.accounts.mixins.WardScopedQuerysetMixin` (`ward_lookup = "ward"`) — an `OFFICER` only sees/updates issues in their own ward; `ADMIN`/superuser accounts see everything. Citizens reach their own issues through the portal, unaffected by this restriction.

## Views

| View | URL | Access |
|---|---|---|
| `ServiceCentreView` | `/issues/services/` | Any logged-in user — the 5-tile One-Stop Centre landing page |
| `IssueListView` | `/issues/` | Staff — all issues, paginated, ward-scoped for officers |
| `IssueCreateView` | `/issues/submit/` | Staff or approved citizen — log a new issue. A citizen must have an `APPROVED` `Citizen` profile to reach this (enforced in `dispatch()`); `?category=WATER` etc. pre-fills the category, and the citizen's own profile/ward pre-fill when they're the one submitting |
| `IssueDetailView` | `/issues/<pk>/` | Staff (ward-scoped) or the reporting citizen — full issue, comments, SMS conversation thread |
| `IssueUpdateView` | `/issues/<pk>/update/` | Staff — change status, assign officer/technician/appointment; fires SMS on appointment changes and on transition into `RESOLVED` |
| `IssueFeedbackView` | `/issues/<pk>/feedback/` (POST only) | The reporting citizen only, and only once — sets `rating` + `feedback_comment` when `status == RESOLVED` and no rating exists yet |

## Signals (`signals.py`)

A `pre_save` receiver stashes the previous `status`, `assigned_technician_name`, and `appointment_at` so the post-save hooks can detect real transitions:

- **`log_issue_save`** — writes a `reports.AuditLog` entry on every create/update (unchanged behaviour).
- **`notify_issue_progress`** — creates a `notifications.Notification` for the reporting citizen's linked user when: (a) a technician/appointment is newly set or changed, or (b) status transitions into `RESOLVED`. This runs alongside, not instead of, the direct SMS sent from `IssueUpdateView`.
