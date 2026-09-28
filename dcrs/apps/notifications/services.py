import requests
from django.conf import settings
from django.utils import timezone

from .models import SMSLog

SENDAFRICA_PROVIDER = "SendAfrica"
SIMULATOR_PROVIDER = "Internal Simulator"


class SendAfricaError(Exception):
    pass


def _send_via_sendafrica(recipient, message_body):
    payload = {"to": recipient, "message": message_body}
    if settings.SENDAFRICA_SENDER_ID:
        payload["from"] = settings.SENDAFRICA_SENDER_ID

    response = requests.post(
        f"{settings.SENDAFRICA_BASE_URL}/v1/sms/",
        json=payload,
        headers={"X-API-Key": settings.SENDAFRICA_API_KEY},
        timeout=10,
    )
    data = response.json()
    if not data.get("success"):
        error = data.get("error", {})
        raise SendAfricaError(f"[{error.get('code', 'unknown')}] {error.get('message', 'SMS send failed')}")
    return data["data"]


def send_sms(recipient, message_body, reference_id=""):
    """Send an SMS via SendAfrica, or the internal simulator if no API key is configured."""
    if not settings.SENDAFRICA_API_KEY:
        return SMSLog.objects.create(
            recipient=recipient,
            message_body=message_body,
            status=SMSLog.Status.SENT,
            provider=SIMULATOR_PROVIDER,
            reference_id=reference_id,
            sent_at=timezone.now(),
        )

    log = SMSLog.objects.create(
        recipient=recipient,
        message_body=message_body,
        status=SMSLog.Status.QUEUED,
        provider=SENDAFRICA_PROVIDER,
        reference_id=reference_id,
    )
    try:
        result = _send_via_sendafrica(recipient, message_body)
    except (SendAfricaError, requests.RequestException) as exc:
        log.status = SMSLog.Status.FAILED
        log.error_message = str(exc)
        log.save(update_fields=["status", "error_message"])
        return log

    log.status = SMSLog.Status.SENT
    log.reference_id = result.get("message_id", "")
    log.sent_at = timezone.now()
    log.save(update_fields=["status", "reference_id", "sent_at"])
    return log


def broadcast_sms(recipients, message_body):
    return [send_sms(recipient, message_body) for recipient in recipients]


def send_issue_update_sms(issue, message):
    """SMS the reporting citizen about their issue.

    Only fires for citizens whose registration has been APPROVED — pending/rejected
    registrations are not yet active users. No-op (returns None) when there is no
    citizen, no approved status, or no phone number to reach.
    """
    citizen = getattr(issue, "citizen", None)
    if citizen is None:
        return None
    if citizen.status != citizen.Status.APPROVED:
        return None
    if not citizen.phone_number:
        return None
    return send_sms(
        citizen.phone_number,
        f"DCRS {issue.reference_no}: {message}",
        reference_id=issue.reference_no,
    )
