"""DRF permissions and the API port of ``WardScopedQuerysetMixin``.

Important difference from the template mixin in ``apps/accounts/mixins.py``: that one
only scopes OFFICER rows and leaves CITIZEN rows unfiltered. That is tolerable when the
only entry points are staff templates (a citizen never gets a link to /list/), but as
soon as the SPA calls these endpoints directly a logged-in CITIZEN could enumerate every
citizen and issue in the system. The API therefore pairs the ward-scoping mixin with an
explicit staff permission class on every staff-only endpoint.
"""
from rest_framework import permissions
from rest_framework.exceptions import NotFound


class IsOfficerOrAdmin(permissions.BasePermission):
    """ADMIN / OFFICER (or Django staff) — the ``user.is_officer`` property."""

    message = "Staff access required."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return bool(user.is_superuser or user.is_staff or user.role in {"ADMIN", "OFFICER"})


class IsAdminRole(permissions.BasePermission):
    """ADMIN / superuser only."""

    message = "Administrator access required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role == "ADMIN")
        )


class IsCitizenRole(permissions.BasePermission):
    """CITIZEN accounts only."""

    message = "Citizen account required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "CITIZEN")


class IsOwnerCitizenOrStaff(permissions.BasePermission):
    """Object level: the owning citizen, or any staff member.

    Works for both ``Citizen`` (owner is ``obj.user``) and ``Issue`` (owner is
    ``obj.citizen.user``).
    """

    message = "You do not have access to this record."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser or user.is_staff or user.role in {"ADMIN", "OFFICER"}:
            return True
        owner = getattr(obj, "user", None)
        if owner is None:
            citizen = getattr(obj, "citizen", None)
            owner = getattr(citizen, "user", None)
        return owner is not None and owner == user


class WardScopedQuerysetMixin:
    """Restrict a queryset to the requesting officer's ward.

    Parity with ``apps/accounts/mixins.WardScopedQuerysetMixin``: only OFFICER accounts are
    scoped, admins/superusers see everything. Anonymous callers get an empty queryset.
    """

    ward_lookup = "ward"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not (user and user.is_authenticated):
            return qs.none()
        if user.role != "OFFICER" or user.is_superuser:
            return qs
        if user.ward_id:
            return qs.filter(**{self.ward_lookup: user.ward_id})
        return qs.none()


def enforce_ward_access(request, obj, ward_attr="ward_id"):
    """404 a non-admin officer acting on a row outside their ward.

    API equivalent of ``apps/citizens/views._guard_ward_access`` for the single-object
    action endpoints (approve / reject) that fetch by pk rather than via get_queryset().
    """
    user = request.user
    if user.role != "OFFICER" or user.is_superuser:
        return
    if not user.ward_id or user.ward_id != getattr(obj, ward_attr, None):
        raise NotFound("Not found.")