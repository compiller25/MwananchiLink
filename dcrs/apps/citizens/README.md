# apps/citizens/

Manages citizen records — the core entity of the DCRS system. Handles registration, profile storage, the ward-scoped approval workflow, and the citizen-facing portal.

## Model: `Citizen`

| Field | Type | Notes |
|---|---|---|
| `citizen_id` | CharField (auto) | `CIT-XXXXXXXXXX` — hex UUID prefix, generated on first save |
| `user` | OneToOneField → User | Optional link to a DCRS user account (`related_name="citizen_profile"`) |
| `full_name` | CharField | Full legal name |
| `national_id` | CharField (unique) | Tanzania national ID number |
| `phone_number` | CharField (unique) | Mobile number for SMS |
| `gender` | CharField (choices) | `FEMALE`, `MALE`, `OTHER` |
| `date_of_birth` | DateField | Optional |
| `region` | ForeignKey → Region | Top-level geography |
| `district` | ForeignKey → District | Sub-region |
| `ward` | ForeignKey → Ward | Local ward — this is what officer access is scoped by |
| `mtaa` | ForeignKey → Mtaa | Street/neighbourhood (optional) |
| `profile_photo` | ImageField | Uploaded to `media/citizens/photos/` |
| `registration_notes` | TextField | Officer notes on the record |
| `status` | CharField (choices) | `PENDING` → `APPROVED` / `REJECTED` / `SUSPENDED` |
| `rejection_reason` | TextField | Set when an officer rejects the registration; sent to the citizen by SMS |

## Status workflow

```
PENDING (default on registration)
   │
   ├──► APPROVED   (officer clicks Approve)
   ├──► REJECTED   (officer clicks Reject, must type a reason)
   └──► SUSPENDED  (post-approval account action, via edit form)
```

Status is **not** editable through the generic edit form anymore — `CitizenEditForm` explicitly excludes `status` and `rejection_reason`. The only way to move a citizen from `PENDING` is the dedicated Approve/Reject actions below, which each fire an SMS (via `apps.notifications.services.send_sms`) and, if the citizen has a linked login, an in-app `Notification`.

## Ward-scoped access

`CitizenListView`, `CitizenDetailView`, and `CitizenUpdateView` all mix in `apps.accounts.mixins.WardScopedQuerysetMixin` (`ward_lookup = "ward"`): an `OFFICER` only ever sees/edits citizens in their own `User.ward`; `ADMIN`/superuser accounts see everyone.

`CitizenApproveView` and `CitizenRejectView` are plain `View`s (they fetch by `pk` directly, not through `get_queryset()`), so they replicate the same restriction via a small `_guard_ward_access(request, citizen)` helper at the top of `views.py` — it raises `Http404` if a non-admin officer's ward doesn't match the citizen's ward.

## Views

| View | URL | Access |
|---|---|---|
| `CitizenHomeView` | `/` | Public — landing page with system stats |
| `CitizenPortalView` | `/portal/` | CITIZEN only — shows own profile + their issues |
| `CitizenRegistrationView` | `/register/` | Public — create a new citizen record + linked login account, auto-logs in |
| `CitizenListView` | `/list/` | Staff — paginated list, ward-scoped for officers |
| `CitizenDetailView` | `/<pk>/` | Staff — full citizen profile, ward-scoped for officers |
| `CitizenUpdateView` | `/<pk>/edit/` | Staff — edit profile fields (not status), ward-scoped for officers |
| `CitizenApproveView` | `/<pk>/approve/` (POST only) | Staff — sets `APPROVED`, sends SMS + notification |
| `CitizenRejectView` | `/<pk>/reject/` (POST only, requires `reason`) | Staff — sets `REJECTED` + `rejection_reason`, sends SMS + notification |
| `CitizenStatusView` | `/<pk>/status/` | Staff — status summary card |

`CitizenRegistrationForm` adds `password1`/`password2` fields (not model fields — validated via `django.contrib.auth.password_validation.validate_password` and a match check) on top of the `Citizen` fields. `CitizenRegistrationView.form_valid()` creates the `Citizen`, then creates a matching `User` (`role=CITIZEN`, `username=phone_number`, `national_id` copied from the citizen record so it's never blank/colliding), links `citizen.user`, and logs the new account in immediately via `django.contrib.auth.login()` — the citizen lands straight in `/portal/` and can track their (likely still-`PENDING`) status without a separate signup step.

## Management command: `seed`

Located at `management/commands/seed.py`. Populates the database with realistic Tanzanian test data covering all roles and features. Safe to run multiple times (uses `get_or_create`).

```bash
python manage.py seed              # seed, skip existing rows
python manage.py seed --flush      # wipe all seeded tables first, then re-seed
```

### What gets seeded

1. Localities — 3 regions, 5 districts, 6 wards, 5 mitaa
2. Users — admin, 2 officers (each assigned a ward), 1 citizen (all password: `test1234`)
3. Citizens — 9 records across different wards and statuses, including at least one `PENDING` citizen per officer's ward so Approve/Reject is demoable immediately
4. Issues — 10 issues with varying priorities/statuses + comments
5. One-Stop Centre demo data — a technician/appointment assigned on one issue, a 5-star rating + feedback on another
6. SMS Templates & Logs — 5 Kiswahili templates, 7 SMS log entries, plus a staff-relayed inbound/outbound conversation thread on one issue
7. Notifications — a handful of read/unread inbox entries for a citizen and an officer
8. Audit logs — 12 entries covering all action types

## Signals (`signals.py`)

Three `post_save` receivers on `Citizen`, plus a `pre_save` receiver that stashes the previous status so the post-save hooks can detect a real transition:

- **`log_citizen_save`** — writes a `reports.AuditLog` entry on every create/update (unchanged behaviour).
- **`notify_citizen_status_change`** — when `status` transitions into `APPROVED` or `REJECTED` (and the citizen has a linked `user`), creates a `notifications.Notification` for that user. This is separate from — and in addition to — the SMS sent directly from `CitizenApproveView`/`CitizenRejectView`.
- **`notify_officers_of_new_registration`** — on every new registration (`created=True`), notifies every `OFFICER` whose `ward` matches the citizen's ward, plus every `ADMIN` (unfiltered by ward — admins oversee every ward), via a web `Notification` deep-linked to the citizen's detail page (`Notification.related_citizen`). Every one of those recipients — matching officer(s) and all admins — also gets a real SMS via `send_sms()` to their own `User.phone_number`, if set.
