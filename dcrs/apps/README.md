# apps/

This directory contains every Django application in the DCRS project. Each app is a self-contained module with its own models, views, URLs, forms, admin registration, and templates.

## App summary

| App | Responsibility |
|---|---|
| `accounts` | Custom User model, login/logout, OTP stub, password reset, `WardScopedQuerysetMixin` |
| `localities` | Geographic hierarchy: Region → District → Ward → Mtaa |
| `citizens` | Citizen registration, profiles, ward-scoped approve/reject workflow, citizen portal |
| `issues` | Issue logging, One-Stop Services Centre, technician appointments, citizen feedback, escalation |
| `notifications` | Real SendAfrica SMS send + delivery webhook, notification inbox, staff-relayed two-way SMS |
| `reports` | Real-time dashboard, registration reports, audit trail |

`accounts.WardScopedQuerysetMixin` is the shared building block behind officer-locality access control: both `citizens` and `issues` list/detail/update views mix it in so an OFFICER only ever sees records in their own ward, while ADMIN/superuser accounts see everything.

## App load order

Apps are registered in `config/settings.py` in this order:

```
accounts → localities → citizens → issues → notifications → reports
```

The order matters because `citizens` has a ForeignKey to `localities`, and `issues` has ForeignKeys to both `citizens` and `localities`. Django resolves these at migration time, but the order avoids circular import surprises.

## Adding a new app

```bash
python manage.py startapp myapp apps/myapp
```

Then add `"apps.myapp"` to `INSTALLED_APPS` in `config/settings.py` and create `apps/myapp/urls.py`, then wire it into `config/urls.py`.
