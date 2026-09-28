# apps/reports/

Provides the analytics and accountability layer — a real-time operations dashboard, filterable registration reports, and a full audit trail of every action taken in the system.

## Model: `AuditLog`

Every significant CREATE, UPDATE, or SEND action in DCRS writes an audit entry.

| Field | Type | Notes |
|---|---|---|
| `actor` | ForeignKey → User (nullable) | Who performed the action |
| `action` | CharField | `CREATE`, `UPDATE`, `DELETE`, `SEND`, etc. |
| `entity_type` | CharField | What was affected (`User`, `Citizen`, `Issue`, `SMS`) |
| `entity_id` | CharField | The ID or name of the affected record |
| `summary` | CharField | Human-readable description of what changed |
| `metadata` | JSONField | Optional extra context (e.g. old/new values) |
| `created_at` | DateTimeField | When the action occurred |

## Views

### `DashboardView` — `/portal/reports/dashboard/`

The main staff landing page after login. Shows live counts and recent activity:

- Total citizens registered
- Pending approvals
- Open/active issues
- SMS sent today
- 5 most recent citizen registrations
- 5 most recent issues
- 8 most recent audit log entries

### `RegistrationReportView` — `/portal/reports/`

Filterable table of all citizen registrations. URL parameters:

| Param | Effect |
|---|---|
| `?ward=sinza` | Filter citizens by ward name (case-insensitive contains) |
| `?status=PENDING` | Filter by approval status |

Both filters can be combined: `?ward=kariakoo&status=APPROVED`

### `AuditLogView` — `/portal/reports/audit/`

Paginated (15 per page) list of all audit entries, newest first. Shows actor, action, entity type, entity ID, summary, and timestamp.

## Who writes audit logs?

Real-time audit logging is already wired via `post_save` signals — this app doesn't create `AuditLog` rows itself, it's purely the read side (dashboard, reports, audit trail list).

- `apps/citizens/signals.py::log_citizen_save` — logs every `Citizen` create/update
- `apps/issues/signals.py::log_issue_save` — logs every `Issue` create/update

Both use a lazy `apps.get_model("reports", "AuditLog")` lookup rather than a direct import, avoiding a circular dependency between `reports` and the apps it audits. The seed command also inserts a handful of illustrative entries so a fresh `seed --flush` has a populated Audit Trail page to demo immediately.

To extend audit logging to another model, add the same `post_save` pattern to that app's `signals.py` (see either file above for the template) — do not call `AuditLog.objects.create(...)` directly from views; keep it signal-driven so it can't be bypassed by a new code path.

Note: the same two signal files also create `notifications.Notification` rows on citizen approval/rejection and issue appointment/resolution — see `apps/notifications/README.md`. That's a separate concern from audit logging (user-facing notification vs. internal accountability trail), even though both are triggered from the same `post_save` receivers file.
