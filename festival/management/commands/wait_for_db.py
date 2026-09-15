"""Block until the database answers, with a readable message when it does not.

Run before migrate on deploy. A database that is merely waking up gets a few
retries; a database that is genuinely unreachable gets a diagnosis instead of
a hundred lines of driver traceback.
"""

import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Wait for the default database to accept connections."

    def add_arguments(self, parser):
        parser.add_argument("--retries", type=int, default=10)
        parser.add_argument("--delay", type=float, default=3.0)

    def handle(self, *args, **options):
        connection = connections["default"]
        settings_dict = connection.settings_dict
        host = settings_dict.get("HOST") or "(local socket)"
        port = settings_dict.get("PORT") or "default port"
        name = settings_dict.get("NAME")
        retries = options["retries"]
        delay = options["delay"]

        self.stdout.write(f"Connecting to database '{name}' at {host}:{port} ...")

        last_error = None
        for attempt in range(1, retries + 1):
            try:
                connection.ensure_connection()
            except OperationalError as exc:
                last_error = exc
                connection.close()
                if attempt < retries:
                    self.stdout.write(f"  attempt {attempt}/{retries} failed, retrying in {delay}s")
                    time.sleep(delay)
            else:
                self.stdout.write(self.style.SUCCESS("Database is up."))
                return

        self.stderr.write(self.style.ERROR(f"Database unreachable after {retries} attempts."))
        self.stderr.write(self.style.ERROR(f"  host  : {host}"))
        self.stderr.write(self.style.ERROR(f"  error : {last_error}"))

        if str(host).startswith("dpg-") and "." not in str(host):
            self.stderr.write("")
            self.stderr.write(self.style.WARNING("That is a Render INTERNAL database hostname."))
            self.stderr.write(
                "It only resolves from a service in the SAME region as the database.\n"
                "Open both pages in the Render dashboard and compare their Region:\n"
                "  - if they differ, delete the database and re-sync the blueprint so it is\n"
                "    recreated beside the service (a database region cannot be changed), or\n"
                "  - paste the database's External URL into DATABASE_URL as a stopgap.\n"
                "A database with no data yet is safe to delete."
            )

        raise SystemExit(1)
