"""
Seed script — run with:  .venv/bin/python seed.py
Populates the DB with realistic Tanzanian test data covering all roles and features.
"""

import os
import sys
import django
from datetime import date, timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth import get_user_model
from apps.localities.models import Region, District, Ward, Mtaa
from apps.citizens.models import Citizen
from apps.issues.models import Issue, IssueComment
from apps.notifications.models import SMSTemplate, SMSLog
from apps.reports.models import AuditLog

User = get_user_model()

def banner(msg):
    print(f"\n{'='*55}")
    print(f"  {msg}")
    print('='*55)

# ─────────────────────────────────────────────
# 1. LOCALITIES
# ─────────────────────────────────────────────
banner("1/6  Localities")

dar = Region.objects.get_or_create(name="Dar es Salaam")[0]
mwanza = Region.objects.get_or_create(name="Mwanza")[0]
dodoma = Region.objects.get_or_create(name="Dodoma")[0]

kinondoni   = District.objects.get_or_create(name="Kinondoni",   region=dar)[0]
ilala       = District.objects.get_or_create(name="Ilala",       region=dar)[0]
temeke      = District.objects.get_or_create(name="Temeke",      region=dar)[0]
nyamagana   = District.objects.get_or_create(name="Nyamagana",   region=mwanza)[0]
dodoma_dist = District.objects.get_or_create(name="Dodoma Urban", region=dodoma)[0]

ward_mwananyamala = Ward.objects.get_or_create(name="Mwananyamala", district=kinondoni)[0]
ward_sinza        = Ward.objects.get_or_create(name="Sinza",         district=kinondoni)[0]
ward_kariakoo     = Ward.objects.get_or_create(name="Kariakoo",      district=ilala)[0]
ward_mbagala      = Ward.objects.get_or_create(name="Mbagala",       district=temeke)[0]
ward_isamilo      = Ward.objects.get_or_create(name="Isamilo",       district=nyamagana)[0]
ward_dodoma       = Ward.objects.get_or_create(name="Dodoma Central",district=dodoma_dist)[0]

mtaa_a = Mtaa.objects.get_or_create(name="Mwananyamala Mashariki", ward=ward_mwananyamala)[0]
mtaa_b = Mtaa.objects.get_or_create(name="Sinza Palestina",         ward=ward_sinza)[0]
mtaa_c = Mtaa.objects.get_or_create(name="Kariakoo Kati",           ward=ward_kariakoo)[0]
mtaa_d = Mtaa.objects.get_or_create(name="Mbagala Rangi Tatu",      ward=ward_mbagala)[0]
mtaa_e = Mtaa.objects.get_or_create(name="Isamilo Juu",             ward=ward_isamilo)[0]

print("  Regions:   ", Region.objects.count())
print("  Districts: ", District.objects.count())
print("  Wards:     ", Ward.objects.count())
print("  Mitaa:     ", Mtaa.objects.count())

# ─────────────────────────────────────────────
# 2. USERS (one per role)
# ─────────────────────────────────────────────
banner("2/6  Users")

USERS = [
    {
        "username": "admin_user",
        "password": "Admin@1234",
        "role":     "ADMIN",
        "first_name": "System",
        "last_name":  "Administrator",
        "email":      "admin@dcrs.go.tz",
        "phone_number": "+255700000001",
        "national_id":  "19850101-00001-00001-1",
        "is_staff": True,
        "is_superuser": True,
        "ward": None,
    },
    {
        "username": "officer_kinondoni",
        "password": "Officer@1234",
        "role":     "OFFICER",
        "first_name": "Juma",
        "last_name":  "Mwalimu",
        "email":      "juma.mwalimu@dcrs.go.tz",
        "phone_number": "+255700000002",
        "national_id":  "19900215-00002-00002-2",
        "is_staff": True,
        "ward": ward_mwananyamala,
    },
    {
        "username": "officer_ilala",
        "password": "Officer@1234",
        "role":     "OFFICER",
        "first_name": "Fatuma",
        "last_name":  "Salehe",
        "email":      "fatuma.salehe@dcrs.go.tz",
        "phone_number": "+255700000003",
        "national_id":  "19921108-00003-00003-3",
        "is_staff": True,
        "ward": ward_kariakoo,
    },
    {
        "username": "citizen_user",
        "password": "Citizen@1234",
        "role":     "CITIZEN",
        "first_name": "Amina",
        "last_name":  "Hassan",
        "email":      "amina.hassan@example.com",
        "phone_number": "+255700000004",
        "national_id":  "19950320-00004-00004-4",
        "is_staff": False,
        "ward": None,
    },
]

created_users = {}
for u in USERS:
    ward = u.pop("ward", None)
    obj, created = User.objects.get_or_create(
        username=u["username"],
        defaults={k: v for k, v in u.items() if k != "password"},
    )
    if created:
        obj.set_password(u["password"])
        obj.ward = ward
        obj.save()
        print(f"  [+] {obj.username} ({obj.role})")
    else:
        print(f"  [=] {obj.username} already exists")
    created_users[obj.username] = obj
    u["password"] = u.get("password", "")  # restore for summary

officer1 = created_users["officer_kinondoni"]
officer2 = created_users["officer_ilala"]
citizen_user = created_users["citizen_user"]

# ─────────────────────────────────────────────
# 3. CITIZENS
# ─────────────────────────────────────────────
banner("3/6  Citizens")

CITIZENS_DATA = [
    # (full_name, national_id, phone, gender, dob, region, district, ward, mtaa, status, user_link)
    ("Amina Hassan",     "CM-19950320-0001", "+255710001001", "FEMALE", date(1995,3,20),  dar,    kinondoni, ward_mwananyamala, mtaa_a, "APPROVED", citizen_user),
    ("Baraka Omari",     "CM-19880612-0002", "+255710001002", "MALE",   date(1988,6,12),  dar,    kinondoni, ward_sinza,        mtaa_b, "APPROVED", None),
    ("Chausiku Nyundo",  "CM-20000101-0003", "+255710001003", "FEMALE", date(2000,1,1),   dar,    ilala,     ward_kariakoo,     mtaa_c, "PENDING",  None),
    ("Daudi Kamanga",    "CM-19751130-0004", "+255710001004", "MALE",   date(1975,11,30), dar,    temeke,    ward_mbagala,      mtaa_d, "PENDING",  None),
    ("Esther Mfaume",    "CM-19920805-0005", "+255710001005", "FEMALE", date(1992,8,5),   mwanza, nyamagana, ward_isamilo,      mtaa_e, "APPROVED", None),
    ("Fredrick Lugendo", "CM-19830417-0006", "+255710001006", "MALE",   date(1983,4,17),  dar,    kinondoni, ward_mwananyamala, mtaa_a, "REJECTED", None),
    ("Grace Mwita",      "CM-19991225-0007", "+255710001007", "FEMALE", date(1999,12,25), mwanza, nyamagana, ward_isamilo,      mtaa_e, "SUSPENDED",None),
    ("Hassan Kigogo",    "CM-19870901-0008", "+255710001008", "MALE",   date(1987,9,1),   dar,    ilala,     ward_kariakoo,     mtaa_c, "APPROVED", None),
]

created_citizens = []
for row in CITIZENS_DATA:
    full_name, nat_id, phone, gender, dob, region, district, ward, mtaa, status, user = row
    obj, created = Citizen.objects.get_or_create(
        national_id=nat_id,
        defaults=dict(
            full_name=full_name, phone_number=phone, gender=gender,
            date_of_birth=dob, region=region, district=district,
            ward=ward, mtaa=mtaa, status=status, user=user,
        )
    )
    created_citizens.append(obj)
    print(f"  {'[+]' if created else '[=]'} {obj.full_name} ({obj.citizen_id}) — {obj.status}")

# ─────────────────────────────────────────────
# 4. ISSUES
# ─────────────────────────────────────────────
banner("4/6  Issues")

ISSUES_DATA = [
    # (citizen_idx, title, category, priority, status, ward, officer, escalated, notes)
    (0, "Broken water pipe on Msimbazi Street",    "WATER",      "HIGH",     "IN_PROGRESS", ward_mwananyamala, officer1, False, "Pipe burst reported by 3 residents"),
    (0, "Street lights out at Mwananyamala junction","LIGHTING",  "MEDIUM",   "OPEN",        ward_mwananyamala, None,     False, ""),
    (1, "Garbage not collected for 2 weeks",       "SANITATION", "HIGH",     "OPEN",        ward_sinza,        officer1, False, ""),
    (1, "Pothole causing accidents on Sinza road", "ROAD",       "CRITICAL", "ESCALATED",   ward_sinza,        officer1, True,  "Escalated after 3 accident reports"),
    (2, "Illegal dumping near Kariakoo market",    "SANITATION", "MEDIUM",   "OPEN",        ward_kariakoo,     officer2, False, ""),
    (2, "Suspicious activity near school",         "SECURITY",   "HIGH",     "IN_PROGRESS", ward_kariakoo,     officer2, False, "Police notified"),
    (3, "Road flooded during rain",                "ROAD",       "HIGH",     "OPEN",        ward_mbagala,      None,     False, ""),
    (4, "Water supply cut for 5 days",             "WATER",      "CRITICAL", "RESOLVED",    ward_isamilo,      officer1, False, "Supply restored on 2026-05-28"),
    (5, "Broken manhole cover on main road",       "SANITATION", "MEDIUM",   "CLOSED",      ward_mwananyamala, officer1, False, "Fixed and verified"),
    (7, "Street vendor blocking emergency exit",   "OTHER",      "LOW",      "OPEN",        ward_kariakoo,     officer2, False, ""),
]

created_issues = []
for row in ISSUES_DATA:
    cidx, title, cat, pri, status, ward, officer, escalated, notes = row
    citizen = created_citizens[cidx]
    obj, created = Issue.objects.get_or_create(
        title=title,
        defaults=dict(
            citizen=citizen, description=f"Reported by {citizen.full_name}. {notes}".strip(),
            category=cat, priority=pri, status=status,
            ward=ward, assigned_officer=officer,
            escalated_to_district=escalated, internal_notes=notes,
        )
    )
    created_issues.append(obj)
    print(f"  {'[+]' if created else '[=]'} {obj.reference_no} [{pri}] {title[:45]}")

# Issue comments
COMMENTS = [
    (0, officer1, "Maintenance team dispatched, ETA 3 hours", False),
    (0, officer1, "Internal: budget code #WTR-2026-088",       True),
    (3, officer1, "Reported to district road engineer",        False),
    (3, officer1, "Awaiting response from district office",    True),
    (7, officer2, "Verbal warning issued to vendor",           False),
]
for cidx, author, body, internal in COMMENTS:
    issue = created_issues[cidx]
    IssueComment.objects.get_or_create(
        issue=issue, author=author, body=body,
        defaults={"is_internal": internal}
    )
print(f"  [+] Issue comments seeded")

# ─────────────────────────────────────────────
# 5. SMS
# ─────────────────────────────────────────────
banner("5/6  SMS Templates & Logs")

templates = [
    ("registration_approved", "Registration Approved",
     "Habari {name}, usajili wako wa DCRS umeidhinishwa. Nambari yako ya utambulisho: {citizen_id}."),
    ("registration_rejected", "Registration Rejected",
     "Habari {name}, kwa bahati mbaya ombi lako la usajili limekataliwa. Wasiliana na ofisi yetu kwa maelezo."),
    ("issue_received",  "Issue Received",
     "Tatizo lako (Ref: {ref_no}) limepokelewa. Tutakujulisha mabadiliko yoyote. Asante."),
    ("issue_resolved",  "Issue Resolved",
     "Tatizo lako (Ref: {ref_no}) limeshughulikiwa. Tafadhali tuarifu iwapo tatizo bado linaendelea."),
    ("broadcast_general", "General Broadcast",
     "Taarifa kwa wakazi wa {ward}: {message}"),
]
for slug, name, body in templates:
    SMSTemplate.objects.get_or_create(slug=slug, defaults={"name": name, "body": body, "is_active": True})
print(f"  [+] {len(templates)} SMS templates")

SMS_LOGS = [
    ("+255710001001", "Amina Hassan", "Habari Amina, usajili wako umeidhinishwa. Nambari: CIT-001.", "DELIVERED"),
    ("+255710001002", "Baraka Omari", "Habari Baraka, usajili wako umeidhinishwa. Nambari: CIT-002.",  "DELIVERED"),
    ("+255710001003", "Chausiku Nyundo", "Tatizo lako ISS-001 limepokelewa. Tutakujulisha.", "SENT"),
    ("+255710001004", "Daudi Kamanga",  "Tatizo lako ISS-004 limepandishwa hadhi. Tunafanya kazi.", "SENT"),
    ("+255710001001", "Amina Hassan",  "Tatizo lako ISS-008 limeshughulikiwa. Maji yamerudi.", "DELIVERED"),
    ("+255710001006", "Fredrick Lugendo","Ombi lako limekataliwa. Wasiliana nasi kwa maelezo.", "DELIVERED"),
    ("+255710001007", "Grace Mwita",    "Akaunti yako imesimamishwa kwa ukaguzi wa ziada.", "FAILED"),
]
admin_user = created_users["admin_user"]
for i, (recipient, name, msg, status) in enumerate(SMS_LOGS):
    SMSLog.objects.get_or_create(
        recipient=recipient,
        message_body=msg,
        defaults=dict(
            status=status,
            provider="Internal Simulator",
            sent_at=timezone.now() - timedelta(hours=len(SMS_LOGS) - i),
        )
    )
print(f"  [+] {len(SMS_LOGS)} SMS log entries")

# ─────────────────────────────────────────────
# 6. AUDIT LOGS
# ─────────────────────────────────────────────
banner("6/6  Audit Logs")

AUDIT_ENTRIES = [
    (admin_user,   "CREATE", "User",    "admin_user",          "Created admin account"),
    (admin_user,   "CREATE", "User",    "officer_kinondoni",   "Created officer account for Kinondoni"),
    (admin_user,   "CREATE", "User",    "officer_ilala",       "Created officer account for Ilala"),
    (officer1,     "CREATE", "Citizen", "Amina Hassan",        "New citizen registration submitted"),
    (officer1,     "UPDATE", "Citizen", "Amina Hassan",        "Status changed to APPROVED"),
    (officer2,     "UPDATE", "Citizen", "Fredrick Lugendo",    "Status changed to REJECTED — duplicate national ID"),
    (officer1,     "CREATE", "Issue",   "ISS-WATER-001",       "Water pipe issue logged"),
    (officer1,     "UPDATE", "Issue",   "ISS-ROAD-004",        "Issue escalated to district"),
    (officer2,     "UPDATE", "Issue",   "ISS-SECURITY-006",    "Police notified, status set to IN_PROGRESS"),
    (officer1,     "UPDATE", "Issue",   "ISS-WATER-008",       "Issue resolved — water supply restored"),
    (admin_user,   "SEND",   "SMS",     "+255710001007",        "SMS delivery failed — invalid number"),
    (admin_user,   "UPDATE", "Citizen", "Grace Mwita",         "Account suspended pending investigation"),
]

for actor, action, entity_type, entity_id, summary in AUDIT_ENTRIES:
    AuditLog.objects.get_or_create(
        actor=actor, action=action, entity_type=entity_type,
        entity_id=str(entity_id), summary=summary,
        defaults={"metadata": {}},
    )
print(f"  [+] {len(AUDIT_ENTRIES)} audit log entries")

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
banner("DONE — Login Credentials")

print("""
  ROLE        USERNAME              PASSWORD
  ─────────────────────────────────────────────
  Admin       admin_user            Admin@1234
  Officer     officer_kinondoni     Officer@1234
  Officer     officer_ilala         Officer@1234
  Citizen     citizen_user          Citizen@1234

  (original 'admin' superuser account unchanged)
""")
