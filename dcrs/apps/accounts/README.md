# apps/accounts/

Handles authentication and the custom User model for all DCRS users.

## Model: `User`

Extends Django's `AbstractUser` with the following extra fields:

| Field | Type | Purpose |
|---|---|---|
| `role` | CharField (choices) | `ADMIN`, `OFFICER`, or `CITIZEN` |
| `phone_number` | CharField (unique) | Used for SMS and OTP |
| `national_id` | CharField (unique) | Officer/admin identity verification |
| `ward` | ForeignKey → Ward | The ward an officer is responsible for |
| `is_phone_verified` | BooleanField | Whether OTP has been confirmed |
| `failed_login_attempts` | PositiveSmallIntegerField | Brute-force tracking |
| `locked_until` | DateTimeField | Null until account is temporarily locked |

### Role behaviour

```python
user.is_officer      # True if role is ADMIN or OFFICER (or is_staff)
user.is_citizen_profile  # True if role is CITIZEN
```

## Views

| View | URL | What it does |
|---|---|---|
| `OfficerLoginPageView` | `/accounts/login/` | Renders login form; redirects CITIZEN to portal, staff to dashboard |
| `OfficerLogoutView` | `/accounts/logout/` | Clears session, redirects to public home |
| `OTPVerifyView` | `/accounts/otp-verify/` | Stub page for future OTP verification flow |
| `OfficerPasswordResetView` | `/accounts/password-reset/` | Django built-in password reset with custom template |

### Role-based redirect after login

`OfficerLoginPageView.get_success_url()` checks `user.role`:
- `CITIZEN` → `citizens:portal`
- Anything else → `reports:dashboard`

## Forms

- `OfficerLoginForm` — extends `AuthenticationForm` with Bootstrap-styled widgets
- `OTPVerificationForm` — single 6-character OTP input (UI only, not yet wired to a provider)

## Settings used

```python
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "reports:dashboard"   # fallback; overridden per role in view
LOGOUT_REDIRECT_URL = "citizens:home"
SESSION_COOKIE_AGE = 1800                  # 30-minute idle timeout
```

## `mixins.py` — `WardScopedQuerysetMixin`

The officer-locality access control used across `apps/citizens` and `apps/issues`:

```python
class WardScopedQuerysetMixin:
    ward_lookup = "ward"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role != user.Role.OFFICER or user.is_superuser:
            return qs
        if user.ward_id:
            return qs.filter(**{self.ward_lookup: user.ward_id})
        return qs.none()
```

- Only `OFFICER` accounts are restricted — an officer only sees rows where `ward_id` matches their own `User.ward`.
- `ADMIN` and superuser accounts bypass the filter entirely and see every record.
- `CITIZEN` accounts are also left unfiltered here deliberately — citizens reach their own records through separate views/URLs (e.g. their status page), so this mixin isn't the access-control layer for them.
- Any `ListView`/`DetailView`/`UpdateView` can opt in by mixing it in first (`class MyView(WardScopedQuerysetMixin, LoginRequiredMixin, ListView)`) and setting `ward_lookup` if the model's ward field isn't named `ward`.
- Single-object action views that don't go through `get_queryset()` (e.g. `CitizenApproveView`, `CitizenRejectView`) replicate the same check manually via a small `_guard_ward_access()` helper in `apps/citizens/views.py` — see that app's README.
