"""
Usage:
    python manage.py seed              # seed, skip existing rows
    python manage.py seed --flush      # wipe all seeded tables first, then re-seed

Works with any DATABASE backend configured in settings.py (SQLite or PostgreSQL).
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.citizens.models import Citizen
from apps.issues.models import Issue, IssueComment
from apps.localities.models import District, Mtaa, Region, Ward
from apps.notifications.models import Notification, SMSLog, SMSTemplate
from apps.reports.models import AuditLog

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with test data (idempotent)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all seeded data before re-seeding",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        localities = self._seed_localities()
        users = self._seed_users(localities)
        citizens = self._seed_citizens(localities, users)
        issues = self._seed_issues(citizens, localities, users)
        self._seed_issue_comments(issues, users)
        self._seed_one_stop_demo_data(issues)
        self._seed_sms(users, issues)
        self._seed_notifications(users, issues)
        self._seed_audit_logs(users)
        self._print_summary()

    # ─────────────────────────────────────────────
    def _flush(self):
        self.stdout.write(self.style.WARNING("Flushing seeded data…"))
        AuditLog.objects.all().delete()
        Notification.objects.all().delete()
        SMSLog.objects.all().delete()
        SMSTemplate.objects.all().delete()
        IssueComment.objects.all().delete()
        Issue.objects.all().delete()
        Citizen.objects.all().delete()
        User.objects.filter(username__in=[
            "admin_user", "officer_kinondoni", "officer_ilala", "citizen_user",
        ]).delete()
        Mtaa.objects.all().delete()
        Ward.objects.all().delete()
        District.objects.all().delete()
        Region.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Flush complete.\n"))

    # ─────────────────────────────────────────────
    def _seed_localities(self):
        self.stdout.write("1/7  Localities")

        dar    = Region.objects.get_or_create(name="Dar es Salaam")[0]
        mwanza = Region.objects.get_or_create(name="Mwanza")[0]
        dodoma = Region.objects.get_or_create(name="Dodoma")[0]

        kinondoni   = District.objects.get_or_create(name="Kinondoni",    region=dar)[0]
        ilala       = District.objects.get_or_create(name="Ilala",        region=dar)[0]
        temeke      = District.objects.get_or_create(name="Temeke",       region=dar)[0]
        nyamagana   = District.objects.get_or_create(name="Nyamagana",    region=mwanza)[0]
        District.objects.get_or_create(name="Dodoma Urban", region=dodoma)

        ward_mwananyamala = Ward.objects.get_or_create(name="Mwananyamala",   district=kinondoni)[0]
        ward_sinza        = Ward.objects.get_or_create(name="Sinza",           district=kinondoni)[0]
        ward_kariakoo     = Ward.objects.get_or_create(name="Kariakoo",        district=ilala)[0]
        ward_mbagala      = Ward.objects.get_or_create(name="Mbagala",         district=temeke)[0]
        ward_isamilo      = Ward.objects.get_or_create(name="Isamilo",         district=nyamagana)[0]

        mtaa_a = Mtaa.objects.get_or_create(name="Mwananyamala Mashariki", ward=ward_mwananyamala)[0]
        mtaa_b = Mtaa.objects.get_or_create(name="Sinza Palestina",         ward=ward_sinza)[0]
        mtaa_c = Mtaa.objects.get_or_create(name="Kariakoo Kati",           ward=ward_kariakoo)[0]
        mtaa_d = Mtaa.objects.get_or_create(name="Mbagala Rangi Tatu",      ward=ward_mbagala)[0]
        mtaa_e = Mtaa.objects.get_or_create(name="Isamilo Juu",             ward=ward_isamilo)[0]

        self.stdout.write(f"   Regions: {Region.objects.count()}  Districts: {District.objects.count()}  "
                          f"Wards: {Ward.objects.count()}  Mitaa: {Mtaa.objects.count()}")

        return dict(
            dar=dar, mwanza=mwanza,
            kinondoni=kinondoni, ilala=ilala, temeke=temeke, nyamagana=nyamagana,
            ward_mwananyamala=ward_mwananyamala, ward_sinza=ward_sinza,
            ward_kariakoo=ward_kariakoo, ward_mbagala=ward_mbagala, ward_isamilo=ward_isamilo,
            mtaa_a=mtaa_a, mtaa_b=mtaa_b, mtaa_c=mtaa_c, mtaa_d=mtaa_d, mtaa_e=mtaa_e,
        )

    # ─────────────────────────────────────────────
    def _seed_users(self, loc):
        self.stdout.write("2/7  Users")

        USERS = [
            dict(username="admin_user",         password="test1234",     role="ADMIN",
                 first_name="System",  last_name="Administrator", email="admin@dcrs.go.tz",
                 phone_number="+255700000001", national_id="19850101-00001-00001-1",
                 is_staff=True, is_superuser=True, ward=None),
            dict(username="officer_kinondoni",  password="test1234", role="OFFICER",
                 first_name="Juma",   last_name="Mwalimu",        email="juma.mwalimu@dcrs.go.tz",
                 phone_number="+255700000002", national_id="19900215-00002-00002-2",
                 is_staff=True, ward=loc["ward_mwananyamala"]),
            dict(username="officer_ilala",      password="test1234", role="OFFICER",
                 first_name="Fatuma", last_name="Salehe",          email="fatuma.salehe@dcrs.go.tz",
                 phone_number="+255700000003", national_id="19921108-00003-00003-3",
                 is_staff=True, ward=loc["ward_kariakoo"]),
            dict(username="citizen_user",       password="test1234", role="CITIZEN",
                 first_name="Amina",  last_name="Hassan",          email="amina.hassan@example.com",
                 phone_number="+255700000004", national_id="19950320-00004-00004-4",
                 is_staff=False, ward=None),
        ]

        created = {}
        for u in USERS:
            ward = u.pop("ward", None)
            pwd  = u.pop("password")
            obj, new = User.objects.get_or_create(username=u["username"], defaults=u)
            if new:
                obj.set_password(pwd)
                obj.ward = ward
                obj.save()
                self.stdout.write(f"   [+] {obj.username} ({obj.role})")
            else:
                self.stdout.write(f"   [=] {obj.username} already exists")
            created[obj.username] = obj

        return created

    # ─────────────────────────────────────────────
    def _seed_citizens(self, loc, users):
        self.stdout.write("3/7  Citizens")

        CITIZENS_DATA = [
            ("Amina Hassan",     "CM-19950320-0001", "+255710001001", "FEMALE", date(1995,3,20),
             loc["dar"],    loc["kinondoni"],  loc["ward_mwananyamala"], loc["mtaa_a"], "APPROVED", users["citizen_user"]),
            ("Baraka Omari",     "CM-19880612-0002", "+255710001002", "MALE",   date(1988,6,12),
             loc["dar"],    loc["kinondoni"],  loc["ward_sinza"],        loc["mtaa_b"], "APPROVED", None),
            ("Chausiku Nyundo",  "CM-20000101-0003", "+255710001003", "FEMALE", date(2000,1,1),
             loc["dar"],    loc["ilala"],      loc["ward_kariakoo"],     loc["mtaa_c"], "PENDING",  None),
            ("Daudi Kamanga",    "CM-19751130-0004", "+255710001004", "MALE",   date(1975,11,30),
             loc["dar"],    loc["temeke"],     loc["ward_mbagala"],      loc["mtaa_d"], "PENDING",  None),
            ("Esther Mfaume",    "CM-19920805-0005", "+255710001005", "FEMALE", date(1992,8,5),
             loc["mwanza"], loc["nyamagana"],  loc["ward_isamilo"],      loc["mtaa_e"], "APPROVED", None),
            ("Fredrick Lugendo", "CM-19830417-0006", "+255710001006", "MALE",   date(1983,4,17),
             loc["dar"],    loc["kinondoni"],  loc["ward_mwananyamala"], loc["mtaa_a"], "REJECTED", None),
            ("Grace Mwita",      "CM-19991225-0007", "+255710001007", "FEMALE", date(1999,12,25),
             loc["mwanza"], loc["nyamagana"],  loc["ward_isamilo"],      loc["mtaa_e"], "SUSPENDED",None),
            ("Hassan Kigogo",    "CM-19870901-0008", "+255710001008", "MALE",   date(1987,9,1),
             loc["dar"],    loc["ilala"],      loc["ward_kariakoo"],     loc["mtaa_c"], "APPROVED", None),
            ("Halima Ramadhani", "CM-19961115-0009", "+255710001009", "FEMALE", date(1996,11,15),
             loc["dar"],    loc["kinondoni"],  loc["ward_mwananyamala"], loc["mtaa_a"], "PENDING",  None),
        ]

        result = []
        for full_name, nat_id, phone, gender, dob, region, district, ward, mtaa, status, user in CITIZENS_DATA:
            obj, new = Citizen.objects.get_or_create(
                national_id=nat_id,
                defaults=dict(
                    full_name=full_name, phone_number=phone, gender=gender,
                    date_of_birth=dob, region=region, district=district,
                    ward=ward, mtaa=mtaa, status=status, user=user,
                ),
            )
            result.append(obj)
            self.stdout.write(f"   {'[+]' if new else '[=]'} {obj.full_name} ({obj.citizen_id}) — {obj.status}")

        return result

    # ─────────────────────────────────────────────
    def _seed_issues(self, citizens, loc, users):
        self.stdout.write("4/7  Issues")

        o1 = users["officer_kinondoni"]
        o2 = users["officer_ilala"]

        ISSUES_DATA = [
            (0, "Broken water pipe on Msimbazi Street",     "WATER",      "HIGH",     "IN_PROGRESS", loc["ward_mwananyamala"], o1, False, "Pipe burst reported by 3 residents"),
            (0, "Street lights out at Mwananyamala",        "LIGHTING",   "MEDIUM",   "OPEN",        loc["ward_mwananyamala"], None, False, ""),
            (1, "Garbage not collected for 2 weeks",        "SANITATION", "HIGH",     "OPEN",        loc["ward_sinza"],        o1, False, ""),
            (1, "Pothole causing accidents on Sinza road",  "ROAD",       "CRITICAL", "ESCALATED",   loc["ward_sinza"],        o1, True,  "Escalated after 3 accident reports"),
            (2, "Illegal dumping near Kariakoo market",     "SANITATION", "MEDIUM",   "OPEN",        loc["ward_kariakoo"],     o2, False, ""),
            (2, "Suspicious activity near school",          "SECURITY",   "HIGH",     "IN_PROGRESS", loc["ward_kariakoo"],     o2, False, "Police notified"),
            (3, "Road flooded during rain",                 "ROAD",       "HIGH",     "OPEN",        loc["ward_mbagala"],      None, False, ""),
            (4, "Water supply cut for 5 days",              "WATER",      "CRITICAL", "RESOLVED",    loc["ward_isamilo"],      o1, False, "Supply restored on 2026-05-28"),
            (5, "Broken manhole cover on main road",        "SANITATION", "MEDIUM",   "CLOSED",      loc["ward_mwananyamala"], o1, False, "Fixed and verified"),
            (7, "Street vendor blocking emergency exit",    "OTHER",      "LOW",      "OPEN",        loc["ward_kariakoo"],     o2, False, ""),
        ]

        result = []
        for cidx, title, cat, pri, status, ward, officer, escalated, notes in ISSUES_DATA:
            citizen = citizens[cidx]
            obj, new = Issue.objects.get_or_create(
                title=title,
                defaults=dict(
                    citizen=citizen,
                    description=f"Reported by {citizen.full_name}. {notes}".strip(),
                    category=cat, priority=pri, status=status,
                    ward=ward, assigned_officer=officer,
                    escalated_to_district=escalated, internal_notes=notes,
                ),
            )
            result.append(obj)
            self.stdout.write(f"   {'[+]' if new else '[=]'} {obj.reference_no} [{pri}] {title[:45]}")

        return result

    # ─────────────────────────────────────────────
    def _seed_issue_comments(self, issues, users):
        o1 = users["officer_kinondoni"]
        o2 = users["officer_ilala"]

        COMMENTS = [
            (0, o1, "Maintenance team dispatched, ETA 3 hours",  False),
            (0, o1, "Internal: budget code #WTR-2026-088",        True),
            (3, o1, "Reported to district road engineer",         False),
            (3, o1, "Awaiting response from district office",     True),
            (7, o2, "Verbal warning issued to vendor",            False),
        ]
        for cidx, author, body, internal in COMMENTS:
            IssueComment.objects.get_or_create(
                issue=issues[cidx], author=author, body=body,
                defaults={"is_internal": internal},
            )
        self.stdout.write("   [+] Issue comments seeded")

    # ─────────────────────────────────────────────
    def _seed_one_stop_demo_data(self, issues):
        """One-Stop Centre demo touches: technician/appointment on an in-progress issue,
        rating/feedback on a resolved issue (slides 20-24)."""
        appointment_issue = issues[0]  # Broken water pipe on Msimbazi Street — IN_PROGRESS
        if not appointment_issue.assigned_technician_name:
            appointment_issue.assigned_technician_name = "John Mwakasege"
            appointment_issue.appointment_at = timezone.now() + timedelta(days=2)
            appointment_issue.save()

        rated_issue = issues[7]  # Water supply cut for 5 days — RESOLVED
        if rated_issue.rating is None:
            rated_issue.rating = 5
            rated_issue.feedback_comment = "Fixed quickly, very satisfied with the response time."
            rated_issue.save()

        self.stdout.write("   [+] One-Stop Centre demo data (technician/appointment + rating)")

    # ─────────────────────────────────────────────
    def _seed_sms(self, users, issues):
        self.stdout.write("5/7  SMS Templates & Logs")

        templates = [
            ("registration_approved", "Registration Approved",
             "Habari {name}, usajili wako wa DCRS umeidhinishwa. Nambari yako: {citizen_id}."),
            ("registration_rejected", "Registration Rejected",
             "Habari {name}, ombi lako la usajili limekataliwa. Wasiliana na ofisi yetu."),
            ("issue_received",  "Issue Received",
             "Tatizo lako (Ref: {ref_no}) limepokelewa. Tutakujulisha mabadiliko. Asante."),
            ("issue_resolved",  "Issue Resolved",
             "Tatizo lako (Ref: {ref_no}) limeshughulikiwa. Tuarifu iwapo bado linaendelea."),
            ("broadcast_general", "General Broadcast",
             "Taarifa kwa wakazi wa {ward}: {message}"),
        ]
        for slug, name, body in templates:
            SMSTemplate.objects.get_or_create(slug=slug, defaults={"name": name, "body": body, "is_active": True})

        SMS_LOGS = [
            ("+255710001001", "Habari Amina, usajili wako umeidhinishwa. Nambari: CIT-001.", "DELIVERED"),
            ("+255710001002", "Habari Baraka, usajili wako umeidhinishwa. Nambari: CIT-002.", "DELIVERED"),
            ("+255710001003", "Tatizo lako ISS-001 limepokelewa. Tutakujulisha.", "SENT"),
            ("+255710001004", "Tatizo lako ISS-004 limepandishwa hadhi. Tunafanya kazi.", "SENT"),
            ("+255710001001", "Tatizo lako ISS-008 limeshughulikiwa. Maji yamerudi.", "DELIVERED"),
            ("+255710001006", "Ombi lako limekataliwa. Wasiliana nasi kwa maelezo.", "DELIVERED"),
            ("+255710001007", "Akaunti yako imesimamishwa kwa ukaguzi wa ziada.", "FAILED"),
        ]
        for i, (recipient, msg, status) in enumerate(SMS_LOGS):
            SMSLog.objects.get_or_create(
                recipient=recipient, message_body=msg,
                defaults=dict(
                    status=status, provider="Internal Simulator",
                    sent_at=timezone.now() - timedelta(hours=len(SMS_LOGS) - i),
                ),
            )
        self.stdout.write(f"   [+] {len(templates)} templates, {len(SMS_LOGS)} SMS logs")

        # Staff-relayed two-way SMS thread demo (slide 22) — tied to the water pipe issue
        appointment_issue = issues[0]
        SMSLog.objects.get_or_create(
            recipient=appointment_issue.citizen.phone_number,
            message_body="The technician has not arrived yet, is he still coming today?",
            defaults=dict(
                status="SENT", provider="Staff-logged (phone)", direction="INBOUND",
                issue=appointment_issue, logged_by=users["officer_kinondoni"],
            ),
        )
        SMSLog.objects.get_or_create(
            recipient=appointment_issue.citizen.phone_number,
            message_body="Apologies for the delay — the technician is on the way and will arrive within the hour.",
            defaults=dict(
                status="SENT", provider="SendAfrica", direction="OUTBOUND",
                issue=appointment_issue,
                sent_at=timezone.now() - timedelta(hours=1, minutes=45),
            ),
        )
        self.stdout.write("   [+] SMS conversation thread seeded")

    # ─────────────────────────────────────────────
    def _seed_notifications(self, users, issues):
        self.stdout.write("6/7  Notifications")

        citizen_user = users["citizen_user"]
        officer1 = users["officer_kinondoni"]

        NOTIFICATIONS = [
            (citizen_user, "Your DCRS registration (CIT-001) has been approved.", None, True),
            (citizen_user, f"Your request {issues[0].reference_no} has a technician scheduled.", issues[0], False),
            (citizen_user, f"Your request {issues[7].reference_no} has been resolved. Please rate the service.", issues[7], False),
            (officer1, "New citizen registration pending approval in your ward.", None, False),
        ]
        for recipient, message, related_issue, is_read in NOTIFICATIONS:
            Notification.objects.get_or_create(
                recipient=recipient, message=message,
                defaults={"related_issue": related_issue, "is_read": is_read},
            )
        self.stdout.write(f"   [+] {len(NOTIFICATIONS)} notifications seeded")

    # ─────────────────────────────────────────────
    def _seed_audit_logs(self, users):
        self.stdout.write("7/7  Audit Logs")

        admin   = users["admin_user"]
        officer1 = users["officer_kinondoni"]
        officer2 = users["officer_ilala"]

        ENTRIES = [
            (admin,    "CREATE", "User",    "admin_user",        "Created admin account"),
            (admin,    "CREATE", "User",    "officer_kinondoni", "Created officer account for Kinondoni"),
            (admin,    "CREATE", "User",    "officer_ilala",     "Created officer account for Ilala"),
            (officer1, "CREATE", "Citizen", "Amina Hassan",      "New citizen registration submitted"),
            (officer1, "UPDATE", "Citizen", "Amina Hassan",      "Status changed to APPROVED"),
            (officer2, "UPDATE", "Citizen", "Fredrick Lugendo",  "Status changed to REJECTED — duplicate national ID"),
            (officer1, "CREATE", "Issue",   "ISS-WATER-001",     "Water pipe issue logged"),
            (officer1, "UPDATE", "Issue",   "ISS-ROAD-004",      "Issue escalated to district"),
            (officer2, "UPDATE", "Issue",   "ISS-SECURITY-006",  "Police notified, status set to IN_PROGRESS"),
            (officer1, "UPDATE", "Issue",   "ISS-WATER-008",     "Issue resolved — water supply restored"),
            (admin,    "SEND",   "SMS",     "+255710001007",     "SMS delivery failed — invalid number"),
            (admin,    "UPDATE", "Citizen", "Grace Mwita",       "Account suspended pending investigation"),
        ]
        for actor, action, entity_type, entity_id, summary in ENTRIES:
            AuditLog.objects.get_or_create(
                actor=actor, action=action, entity_type=entity_type,
                entity_id=str(entity_id), summary=summary,
                defaults={"metadata": {}},
            )
        self.stdout.write(f"   [+] {len(ENTRIES)} audit log entries")

    # ─────────────────────────────────────────────
    def _print_summary(self):
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 55))
        self.stdout.write(self.style.SUCCESS("  DONE — Login Credentials"))
        self.stdout.write(self.style.SUCCESS("=" * 55))
        self.stdout.write("""
  ROLE        USERNAME              PASSWORD
  ─────────────────────────────────────────────
  Superuser   admin                 test1234
  Admin       admin_user            test1234
  Officer     officer_kinondoni     test1234
  Officer     officer_ilala         test1234
  Citizen     citizen_user          test1234
""")
