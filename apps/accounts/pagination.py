"""Pagination classes shared by the API layer.

The template views used Django's ``paginate_by``; these mirror those sizes so the
React pagination component renders the same number of rows per page. DRF returns
``{count, next, previous, results}`` and pages via ``?page=`` — the same query
parameter the Django templates used.
"""
from rest_framework.pagination import PageNumberPagination


class DcrsPagination(PageNumberPagination):
    """Default: matches ``paginate_by = 10`` on the citizen/issue list views."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class SmsLogPagination(DcrsPagination):
    """matches SMSLogListView.paginate_by = 12"""

    page_size = 12


class NotificationPagination(DcrsPagination):
    """matches NotificationListView.paginate_by = 20"""

    page_size = 20


class AuditLogPagination(DcrsPagination):
    """matches AuditLogView.paginate_by = 15"""

    page_size = 15