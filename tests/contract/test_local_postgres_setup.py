"""Contract checks for the native Windows PostgreSQL setup workflow."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
SETUP_SCRIPT = BACKEND_ROOT / "scripts" / "setup_local_postgres.ps1"
ENVIRONMENT_EXAMPLE = BACKEND_ROOT / ".env.example"
README = PROJECT_ROOT / "README.md"
WALKTHROUGH = PROJECT_ROOT / "docs" / "guides" / "PostgreSQL Implementation Walkthrough.md"
ARCHITECTURE = PROJECT_ROOT / "docs" / "inception" / "ARCHITECTURE.md"


class LocalPostgresSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SETUP_SCRIPT.read_text(encoding="utf-8")
        cls.environment_example = ENVIRONMENT_EXAMPLE.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")
        cls.walkthrough = WALKTHROUGH.read_text(encoding="utf-8")
        cls.architecture = ARCHITECTURE.read_text(encoding="utf-8")

    def test_environment_urls_use_one_local_postgres_cluster(self) -> None:
        self.assertIn(
            "DATABASE_URL=postgresql+psycopg://skillproof:skillproof@localhost:5432/skillproof",
            self.environment_example,
        )
        self.assertIn(
            "TEST_DATABASE_URL=postgresql+psycopg://skillproof_test:skillproof_test"
            "@localhost:5432/skillproof_test",
            self.environment_example,
        )
        self.assertIn("low value", self.environment_example)

    def test_admin_password_is_securely_prompted_and_scoped(self) -> None:
        self.assertRegex(
            self.script,
            r"\[System\.Security\.SecureString\]\s+\$PostgresAdminPassword",
        )
        self.assertRegex(self.script, r"Read-Host[\s\S]+?-AsSecureString")
        self.assertIn('$env:PGPASSWORD = $PlainTextAdminPassword', self.script)
        self.assertRegex(
            self.script,
            r"finally\s*\{[\s\S]+?\$env:PGPASSWORD = \$PreviousPgPassword"
            r"[\s\S]+?Remove-Item -LiteralPath \"Env:PGPASSWORD\"",
        )
        self.assertNotRegex(
            self.script,
            r"(?i)(PostgresAdminPassword|PlainTextAdminPassword).*Write-(Host|Output|Verbose)",
        )

    def test_roles_databases_and_schemas_are_least_privilege(self) -> None:
        for role in ("skillproof", "skillproof_test"):
            with self.subTest(role=role):
                self.assertIn(f"ALTER ROLE {role} WITH", self.script)
                self.assertIn(f"ALTER SCHEMA public OWNER TO {role};", self.script)
                self.assertIn(f"GRANT USAGE, CREATE ON SCHEMA public TO {role};", self.script)

        for database in ("skillproof", "skillproof_test"):
            with self.subTest(database=database):
                self.assertIn(f"ALTER DATABASE {database} OWNER TO {database};", self.script)
                self.assertIn(
                    f"REVOKE ALL PRIVILEGES ON DATABASE {database} FROM PUBLIC;",
                    self.script,
                )

        self.assertGreaterEqual(
            self.script.count("REVOKE CREATE ON SCHEMA public FROM PUBLIC;"),
            2,
        )
        for restriction in (
            "NOSUPERUSER",
            "NOCREATEDB",
            "NOCREATEROLE",
            "NOINHERIT",
            "NOREPLICATION",
            "NOBYPASSRLS",
        ):
            self.assertIn(restriction, self.script)
        self.assertIn("SET password_encryption TO 'scram-sha-256';", self.script)

    def test_setup_uses_backend_python_and_verifies_migrations(self) -> None:
        self.assertIn('"C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe"', self.script)
        self.assertIn('Get-Command "psql.exe"', self.script)
        self.assertIn('".venv\\Scripts\\python.exe"', self.script)
        self.assertRegex(
            self.script,
            re.compile(
                r'Invoke-Alembic -Arguments @\("upgrade", "head"\)'
                r'[\s\S]+?Invoke-Alembic -Arguments @\("current"\)'
                r'[\s\S]+?Invoke-Alembic -Arguments @\("check"\)'
            ),
        )
        self.assertIn("Copy-Item -LiteralPath $EnvironmentExamplePath", self.script)

    def test_native_postgres_is_the_documented_primary_runtime(self) -> None:
        for document in (self.readme, self.walkthrough, self.architecture):
            with self.subTest(document=document[:40]):
                self.assertIn("postgresql-x64-18", document)
                self.assertIn("backend/scripts/setup_local_postgres.ps1", document)
                self.assertIn("skillproof_test", document)
                self.assertIn("`public`", document)

        self.assertIn("The primary local database is the installed Windows PostgreSQL 18", self.readme)
        self.assertIn("optional fallback", self.readme)
        self.assertIn("0001_evidence_ledger", self.readme)
        self.assertIn("pg_isready.exe", self.walkthrough)
        self.assertIn("-Reset", self.walkthrough)


if __name__ == "__main__":
    unittest.main()
