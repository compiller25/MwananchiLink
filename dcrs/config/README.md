# config/

The Django project configuration package. Contains settings, root URL dispatcher, and WSGI/ASGI entry points.

## Files

### `settings.py`

Central configuration for the entire project. Key sections:

| Section | Notes |
|---|---|
| `SECRET_KEY` | **Must be changed for production.** Currently a hardcoded dev key. |
| `DEBUG` | `True` in dev. Set to `False` in production. |
| `ALLOWED_HOSTS` | Add your domain here for production. |
| `INSTALLED_APPS` | All six DCRS apps plus Django built-ins. |
| `DATABASES` | SQLite by default. See root README for PostgreSQL config. |
| `AUTH_USER_MODEL` | `"accounts.User"` — custom user with role field. |
| `LOGIN_URL` | `"accounts:login"` |
| `LOGIN_REDIRECT_URL` | `"reports:dashboard"` — fallback, overridden per role in `accounts/views.py`. |
| `LOGOUT_REDIRECT_URL` | `"citizens:home"` |
| `SESSION_COOKIE_AGE` | `1800` seconds (30 minutes idle timeout). |
| `TIME_ZONE` | `"Africa/Dar_es_Salaam"` |
| `STATIC_URL` / `STATICFILES_DIRS` | Served from `static/` in dev. |
| `MEDIA_URL` / `MEDIA_ROOT` | User uploads stored in `media/`. |
| `EMAIL_BACKEND` | Console backend in dev — emails print to terminal. |
| `SENDAFRICA_BASE_URL` / `SENDAFRICA_API_KEY` / `SENDAFRICA_SENDER_ID` | Real SMS gateway config, read from env. Leave `SENDAFRICA_API_KEY` blank to use the internal simulator (default for dev). Account balance is checked via `GET {BASE}/v1/credits/balance`; a drained account fails sends gracefully as `FAILED` `SMSLog` rows. See `apps/notifications/README.md`. |
| `TEMPLATES[0]["OPTIONS"]["context_processors"]` | Includes `apps.notifications.context_processors.notifications`, which injects `unread_notifications`/`unread_notifications_count` into every template for the bell-icon dropdown. |

### `urls.py`

Root URL dispatcher. Mounts each app's URL config:

| Prefix | App |
|---|---|
| `""` | `citizens.urls` — home, register, list, detail, portal, approve/reject |
| `"accounts/"` | `accounts.urls` — login, logout, OTP, password reset |
| `"api/localities/"` | `localities.urls` — cascading dropdown API |
| `"issues/"` | `issues.urls` — services centre, submit, list, detail, update, feedback |
| `"portal/sms/"` | `notifications.urls` — compose, broadcast, log, log-incoming, delivery callback, notification inbox |
| `"portal/reports/"` | `reports.urls` — dashboard, report, audit |
| `"admin/"` | Django built-in admin site |

In `DEBUG` mode, media files are also served via `django.conf.urls.static`.

Note: `portal/sms/callback/` is a **public webhook endpoint** (CSRF-exempt, no login required) — it's how SendAfrica pushes delivery-status updates back into the app. Everything else under `portal/sms/` requires an authenticated session as normal.

### `wsgi.py`

WSGI entry point for production servers (gunicorn, uWSGI).

```bash
gunicorn config.wsgi:application
```

### `asgi.py`

ASGI entry point for async servers (uvicorn, Daphne). Not yet used — DCRS is a synchronous Django app — but available if WebSockets or async views are added later.
