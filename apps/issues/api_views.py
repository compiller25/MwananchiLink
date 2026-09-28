"""Issue endpoints for the SPA.

Scoping (see ``_scope_for_user``): citizens see only their own requests, officers only their
own ward, admins everything. Status/technician changes always go through ``Model.save()`` so
the signals in ``apps/issues/signals.py`` fire the citizen's SMS + web notification.
"""
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    DestroyAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.drf_permissions import IsOfficerOrAdmin
from apps.accounts.pagination import DcrsPagination
from apps.notifications.services import send_issue_update_sms

from .constants import SERVICE_TILES
from .models import Issue, IssueComment
from .serializers import (
    IssueCommentSerializer,
    IssueCreateSerializer,
    IssueDetailSerializer,
    IssueFeedbackSerializer,
    IssueListSerializer,
    IssueUpdateSerializer,
    is_staff_user,
)


def _scope_for_user(user, qs):
    """Citizens → own requests; officers → own ward; admins → everything."""
    if user.role == "CITIZEN":
        return qs.filter(citizen__user=user)
    if user.role == "OFFICER" and not user.is_superuser:
        if not user.ward_id:
            return qs.none()
        return qs.filter(ward_id=user.ward_id)
    return qs


def _visible_issues(user):
    return _scope_for_user(
        user, Issue.objects.select_related("citizen", "ward", "assigned_officer")
    )


class IssueListCreateView(ListCreateAPIView):
    """GET /api/v1/issues/ — scoped list. POST /api/v1/issues/ — file a service request."""

    permission_classes = [IsAuthenticated]
    pagination_class = DcrsPagination
    filter_backends = [SearchFilter]
    search_fields = ("title", "reference_no", "description", "citizen__full_name")

    def get_queryset(self):
        qs = _visible_issues(self.request.user)
        params = self.request.query_params
        for field in ("status", "category", "priority"):
            value = params.get(field)
            if value:
                qs = qs.filter(**{field: value})
        ward = params.get("ward")
        if ward and str(ward).isdigit():
            qs = qs.filter(ward_id=int(ward))
        return qs

    def get_serializer_class(self):
        return IssueCreateSerializer if self.request.method == "POST" else IssueListSerializer

    @extend_schema(request=IssueCreateSerializer, responses={201: IssueDetailSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issue = serializer.save()  # signals → "request received" SMS to the citizen
        return Response(
            {
                "detail": f"Issue {issue.reference_no} submitted.",
                "issue": IssueDetailSerializer(issue, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class IssueDetailView(RetrieveUpdateDestroyAPIView):
    """GET / PATCH / DELETE /api/v1/issues/{id}/.

    GET is allowed for anyone who can already see the issue; PATCH/DELETE are ward actions
    (assigning a technician, changing status), so they are staff-only.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _visible_issues(self.request.user)

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsOfficerOrAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return IssueUpdateSerializer
        return IssueDetailSerializer

    @extend_schema(request=IssueUpdateSerializer, responses={200: IssueDetailSerializer})
    def update(self, request, *args, **kwargs):
        issue = self.get_object()
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(issue, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "detail": f"Issue {issue.reference_no} updated.",
                "issue": IssueDetailSerializer(issue, context={"request": request}).data,
            }
        )

    def destroy(self, request, *args, **kwargs):
        issue = self.get_object()
        detail = f"Issue {issue.reference_no} has been deleted."
        self.perform_destroy(issue)
        return Response({"detail": detail}, status=status.HTTP_200_OK)


class ServiceCentreView(APIView):
    """GET /api/v1/issues/services/ — the One-Stop Emergency & Services Centre tiles."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"services": SERVICE_TILES})


class IssueFeedbackView(APIView):
    """POST /api/v1/issues/{id}/feedback/ — owner only, RESOLVED, and not yet rated."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=IssueFeedbackSerializer, responses={200: IssueDetailSerializer})
    def post(self, request, pk):
        # The get_object_or_404 filters *are* the guard, exactly as in IssueFeedbackView.
        issue = get_object_or_404(
            Issue,
            pk=pk,
            citizen__user=request.user,
            status=Issue.Status.RESOLVED,
            rating__isnull=True,
        )
        serializer = IssueFeedbackSerializer(
            issue, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_issue_update_sms(
            issue, "Thank you for your feedback. It helps us serve your community better."
        )
        return Response(
            {
                "detail": "Thanks for your feedback!",
                "issue": IssueDetailSerializer(issue, context={"request": request}).data,
            }
        )


class IssueCommentListCreateView(APIView):
    """GET / POST /api/v1/issues/{id}/comments/ — threaded comments on an issue."""

    permission_classes = [IsAuthenticated]

    def get_issue(self, pk):
        return get_object_or_404(_visible_issues(self.request.user), pk=pk)

    def get(self, request, pk):
        issue = self.get_issue(pk)
        qs = issue.comments.select_related("author")
        if not is_staff_user(request.user):
            qs = qs.filter(is_internal=False)  # ward-internal notes stay internal
        serializer = IssueCommentSerializer(qs, many=True, context={"request": request})
        return Response({"results": serializer.data})

    @extend_schema(request=IssueCommentSerializer, responses={201: IssueCommentSerializer})
    def post(self, request, pk):
        issue = self.get_issue(pk)
        serializer = IssueCommentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(issue=issue, author=request.user)
        # Parity with IssueDetailView.post: a ward (non-internal) reply is texted to the citizen.
        if is_staff_user(request.user) and not comment.is_internal:
            send_issue_update_sms(issue, f"New update from the ward: {comment.body[:120]}")
        return Response(
            {"detail": "Comment added.", "comment": serializer.data},
            status=status.HTTP_201_CREATED,
        )


class IssueCommentDeleteView(DestroyAPIView):
    """DELETE /api/v1/issues/comments/{id}/ — staff, or the comment's own author."""

    permission_classes = [IsAuthenticated]
    queryset = IssueComment.objects.select_related("issue", "author")

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if not (is_staff_user(request.user) or obj.author_id == request.user.id):
            self.permission_denied(request, message="You can only delete your own comment.")

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        issue_pk = comment.issue_id
        self.perform_destroy(comment)
        return Response(
            {"detail": "Comment deleted.", "issue": issue_pk}, status=status.HTTP_200_OK
        )