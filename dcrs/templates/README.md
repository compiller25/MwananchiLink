# templates/

All HTML templates for DCRS. Django is configured to look here first (`DIRS = [BASE_DIR / "templates"]`).

## Layout

```
templates/
├── base.html                   # Root layout — three shells (public/citizen/staff), bell dropdown in citizen header
├── partials/
│   ├── sidebar.html            # Staff left navigation
│   ├── navbar.html             # Staff top bar with user menu + notification bell
│   ├── messages.html           # Django flash message renderer
│   └── pagination.html         # Reusable pagination controls
├── accounts/
│   ├── login.html              # Login page (public)
│   ├── otp_verify.html         # OTP entry page (stub)
│   ├── password_reset.html     # Password reset request form
│   └── password_reset_email.txt # Plain-text reset email body
├── citizens/
│   ├── home.html               # Public landing page
│   ├── portal.html             # Citizen portal — includes One-Stop Services Centre quick-action card
│   ├── register.html           # Citizen registration form
│   ├── citizen_list.html       # Staff — paginated citizen list (ward-scoped for officers)
│   ├── citizen_detail.html     # Staff — full profile, Approve/Reject actions + rejection-reason modal
│   └── citizen_status.html     # Staff — status summary card
├── issues/
│   ├── service_centre.html     # One-Stop Emergency & Services Centre — 5 tile grid
│   ├── issue_submit.html       # Log a new issue (category pre-fillable via ?category=)
│   ├── issue_list.html         # Issue table with filters (ward-scoped for officers)
│   ├── issue_detail.html       # Full issue — comments, SMS Conversation card, feedback/rating widget
│   └── issue_update.html       # Change status / assign officer / technician / appointment
├── notifications/
│   ├── sms_compose.html        # Compose SMS to individual (supports ?recipient= and ?issue= prefill)
│   ├── sms_broadcast.html      # Broadcast to ward
│   ├── sms_log.html            # Delivery log table
│   └── inbox.html              # Notification inbox — full read/unread history
└── reports/
    ├── dashboard.html          # Main staff dashboard
    ├── registration_report.html # Filterable citizen report
    └── audit_log.html          # Paginated audit trail
```

## base.html — three shells

`base.html` renders a different outer layout depending on the authenticated state and role of the current user:

| Condition | Shell rendered |
|---|---|
| `user.is_authenticated` and `user.role == 'CITIZEN'` | **Citizen shell** — header with logo, notification bell dropdown, and sign-out button, no sidebar |
| `user.is_authenticated` (ADMIN or OFFICER) | **Staff shell** — full sidebar + top navbar (with its own bell dropdown) |
| Not authenticated | **Public shell** — minimal header with DCRS logo and Officer Login link |

All three shells share the same `{% block content %}` so individual templates do not need to know which shell they are in.

## Partials

### `sidebar.html`
Staff-only left navigation. Sections: Main (Dashboard, Citizens, Issues), Communications (Compose SMS, Broadcast, SMS Log), Analytics (Reports, Audit Trail). Includes user name and role in the footer.

### `navbar.html`
Top bar for staff shell. Shows breadcrumb, page title (`{% block page_title %}`), theme toggle, **notification bell dropdown** (unread count badge, latest 6, link to full inbox), role badge, and user dropdown with sign-out. The bell's context (`unread_notifications`, `unread_notifications_count`) comes from `apps.notifications.context_processors.notifications`, not from each view — it's available on every page automatically, including the matching bell in the citizen shell header in `base.html`.

### `messages.html`
Renders Django's `messages` framework alerts (success, warning, error, info) using Bootstrap alert classes.

### `pagination.html`
Include this partial in any list view that uses Django's `Paginator`:
```html
{% include 'partials/pagination.html' with page_obj=page_obj %}
```

## Extending base.html

Every page template should start with:

```html
{% extends 'base.html' %}
{% block title %}Page Title — DCRS{% endblock %}
{% block page_title %}Page Title{% endblock %}  {# staff navbar only #}

{% block content %}
  ... your content ...
{% endblock %}
```
