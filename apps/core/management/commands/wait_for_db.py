import time

import psycopg2
import psycopg2.sql
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Waits until the database is available, creating it if it does not exist."

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=60,
            help="Maximum seconds to wait (default: 60).",
        )
        parser.add_argument(
            "--interval",
            type=float,
            default=1.0,
            help="Seconds between retries (default: 1).",
        )

    def handle(self, *args, **options):
        timeout = options["timeout"]
        interval = options["interval"]
        elapsed = 0.0

        db = connection.settings_dict
        host = db["HOST"]
        port = db["PORT"] or 5432
        user = db["USER"]
        password = db["PASSWORD"]
        dbname = db["NAME"]

        self.stdout.write("Waiting for database server...")

        # ── Step 1: wait for the Postgres server itself ──────────────────────
        while elapsed < timeout:
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    dbname="postgres",
                    connect_timeout=5,
                )
                conn.autocommit = True

                # ── Step 2: create the target DB if it doesn't exist ─────────
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM pg_database WHERE datname = %s",
                        [dbname],
                    )
                    if not cur.fetchone():
                        self.stdout.write(f"  Database '{dbname}' not found — creating...")
                        cur.execute(
                            psycopg2.sql.SQL("CREATE DATABASE {}").format(
                                psycopg2.sql.Identifier(dbname)
                            )
                        )
                        self.stdout.write(self.style.SUCCESS(f"  Database '{dbname}' created."))

                conn.close()
                break

            except psycopg2.OperationalError:
                self.stdout.write(
                    f"  Server not ready — retrying in {interval}s... ({elapsed:.0f}s elapsed)"
                )
                time.sleep(interval)
                elapsed += interval
        else:
            self.stderr.write(self.style.ERROR(f"Database server not available after {timeout}s."))
            raise SystemExit(1)

        # ── Step 3: confirm Django can connect to the target DB ──────────────
        connection.close()
        while elapsed < timeout:
            try:
                connection.ensure_connection()
                self.stdout.write(self.style.SUCCESS("Database is ready."))
                return
            except OperationalError:
                self.stdout.write(f"  Not ready — retrying... ({elapsed:.0f}s elapsed)")
                time.sleep(interval)
                elapsed += interval

        self.stderr.write(self.style.ERROR(f"Database not available after {timeout}s. Exiting."))
        raise SystemExit(1)
