from django.apps import apps
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.notifications.services import send_issue_update_sms

from .models import Issue


@receiver(pre_save, sender=Issue)
def stash_previous_state(sender, instance, **kwargs):
    if instance.pk:
        previous = Issue.objects.filter(pk=instance.pk).values(
            "status", "assigned_officer_id", "assigned_technician_name", "appointment_at"
        ).first()
    else:
        previous = None
    instance._previous_state = previous


@receiver(post_save, sender=Issue)
def log_issue_save(sender, instance, created, **kwargs):
    try:
        AuditLog = apps.get_model("reports", "AuditLog")
    except LookupError:
        return

    AuditLog.objects.create(
        actor=instance.assigned_officer,
        action="created" if created else "updated",
        entity_type="Issue",
        entity_id=str(instance.pk),
        summary=instance.title,
        metadata={"status": instance.status, "reference_no": instance.reference_no},
    )


@receiver(post_save, sender=Issue)
def notify_issue_progress(sender, instance, created, **kwargs):
    """SMS + web notification for issue creation and progress updates.

    Signal-driven so the reporting citizen is always texted no matter who makes the
    change — a ward officer via the portal, or an admin via the Django admin.
    """
    try:
        Notification = apps.get_model("notifications", "Notification")
    except LookupError:
        Notification = None

    if created:
        send_issue_update_sms(
            instance, "Your request has been received and is now awaiting a ward officer."
        )
        return

    previous = getattr(instance, "_previous_state", None)
    if not previous:
        return

    notify_web = bool(Notification is not None and instance.citizen.user_id)
    recipient_id = instance.citizen.user_id if notify_web else None

    if instance.assigned_officer_id and instance.assigned_officer_id != previous["assigned_officer_id"]:
        name = instance.assigned_officer.get_full_name() or instance.assigned_officer.username
        send_issue_update_sms(instance, f"Officer {name} has been assigned to your request.")
        if notify_web:
            Notification.objects.create(
                recipient_id=recipient_id,
                message=f"Officer {name} has been assigned to {instance.reference_no}.",
                related_issue=instance,
            )

    appointment_newly_set = (
        instance.assigned_technician_name and instance.appointment_at
        and (instance.assigned_technician_name != previous["assigned_technician_name"]
             or instance.appointment_at != previous["appointment_at"])
    )
    if appointment_newly_set:
        send_issue_update_sms(
            instance,
            f"Technician {instance.assigned_technician_name} is scheduled to visit on "
            f"{instance.appointment_at.strftime('%d %b %Y, %H:%M')}.",
        )
        if notify_web:
            Notification.objects.create(
                recipient_id=recipient_id,
                message=(
                    f"Technician {instance.assigned_technician_name} scheduled to visit for "
                    f"{instance.reference_no} on {instance.appointment_at.strftime('%d %b %Y, %H:%M')}."
                ),
                related_issue=instance,
            )

    if instance.status != previous["status"]:
        status_messages = {
            Issue.Status.OPEN: "Your request has been reopened. Please check your DCRS portal for updates.",
            Issue.Status.IN_PROGRESS: "Your request is now being handled by the ward office.",
            Issue.Status.ESCALATED: "Your request has been escalated to district level for priority action.",
            Issue.Status.RESOLVED: "Your request has been resolved. Please rate your experience in your DCRS portal.",
            Issue.Status.CLOSED: "Your request has been closed.",
        }
        text = status_messages.get(instance.status)
        if text:
            send_issue_update_sms(instance, text)
        if notify_web:
            inbox_messages = {
                Issue.Status.OPEN: f"Your request {instance.reference_no} has been reopened.",
                Issue.Status.IN_PROGRESS: f"Your request {instance.reference_no} is now being handled by the ward office.",
                Issue.Status.ESCALATED: f"Your request {instance.reference_no} has been escalated to district level.",
                Issue.Status.RESOLVED: f"Your request {instance.reference_no} has been resolved. Please rate the service.",
                Issue.Status.CLOSED: f"Your request {instance.reference_no} has been closed.",
            }
            inbox = inbox_messages.get(instance.status)
            if inbox:
                Notification.objects.create(
                    recipient_id=recipient_id,
                    message=inbox,
                    related_issue=instance,
                )
