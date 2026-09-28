class WardScopedQuerysetMixin:
    """Restrict a queryset to the requesting officer's ward.

    Only OFFICER accounts are scoped. Admins/superusers see everything, and citizens are left
    untouched here since they may need to reach their own record through these same views
    (e.g. from their status page) — access control for citizens is handled elsewhere.
    """

    ward_lookup = "ward"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role != user.Role.OFFICER or user.is_superuser:
            return qs
        if user.ward_id:
            return qs.filter(**{self.ward_lookup: user.ward_id})
        return qs.none()
