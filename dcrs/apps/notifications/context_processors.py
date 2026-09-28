from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {}
    qs = Notification.objects.filter(recipient=request.user)
    return {
        "unread_notifications": qs.filter(is_read=False).select_related("related_issue")[:6],
        "unread_notifications_count": qs.filter(is_read=False).count(),
    }
