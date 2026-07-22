[CmdletBinding()]
param(
    [Parameter()]
    [System.Security.SecureString] $PostgresAdminPassword,

    [Parameter()]
    [switch] $Reset
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$DatabaseHost = "localhost"
$DatabasePort = 5432
$PostgresAdminUser = "postgres"
# These fixed credentials are intentionally low value and are only for local development.
$ApplicationRole = "skillproof"
$ApplicationPassword = "skillproof"
$ApplicationDatabase = "skillproof"
$TestRole = "skillproof_test"
$TestPassword = "skillproof_test"
$TestDatabase = "skillproof_test"

$BackendRoot = Split-Path -Parent $PSScriptRoot
$PythonPath = Join-Path $BackendRoot ".venv\Scripts\python.exe"
$EnvironmentExamplePath = Join-Path $BackendRoot ".env.example"
$EnvironmentPath = Join-Path $BackendRoot ".env"

function Resolve-PostgresPsql {
    $Postgres18Psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
    if (Test-Path -LiteralPath $Postgres18Psql -PathType Leaf) {
        return $Postgres18Psql
    }

    $PathCommand = Get-Command "psql.exe" -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $PathCommand) {
        throw (
            "PostgreSQL 18 psql.exe was not found at '{0}' or on PATH. " +
            "Install PostgreSQL 18 and ensure its bin directory is available."
        ) -f $Postgres18Psql
    }

    return $PathCommand.Source
}

function Assert-Postgres18Client {
    param(
        [Parameter(Mandatory)]
        [string] $PsqlPath
    )

    $VersionOutput = & $PsqlPath --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to execute PostgreSQL psql at '$PsqlPath'."
    }

    $VersionText = ($VersionOutput | ForEach-Object { $_.ToString() }) -join " "
    if ($VersionText -notmatch "\(PostgreSQL\)\s+18(?:\.|\s|$)") {
        throw "PostgreSQL 18 is required, but '$PsqlPath --version' returned: $VersionText"
    }
}

function ConvertFrom-SecurePassword {
    param(
        [Parameter(Mandatory)]
        [System.Security.SecureString] $SecurePassword
    )

    $PasswordPointer = [System.IntPtr]::Zero
    try {
        $PasswordPointer = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR(
            $SecurePassword
        )
        return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($PasswordPointer)
    }
    finally {
        if ($PasswordPointer -ne [System.IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($PasswordPointer)
        }
    }
}

function Invoke-PostgresSql {
    param(
        [Parameter(Mandatory)]
        [string] $PsqlPath,

        [Parameter(Mandatory)]
        [string] $Database,

        [Parameter(Mandatory)]
        [string] $Sql
    )

    $PsqlArguments = @(
        "--no-psqlrc"
        "--host=$DatabaseHost"
        "--port=$DatabasePort"
        "--username=$PostgresAdminUser"
        "--dbname=$Database"
        "--set=ON_ERROR_STOP=1"
        "--no-align"
        "--tuples-only"
    )

    $Output = $Sql | & $PsqlPath @PsqlArguments 2>&1
    $ExitCode = $LASTEXITCODE
    $OutputLines = @($Output | ForEach-Object { $_.ToString() })

    if ($ExitCode -ne 0) {
        $FailureDetail = ($OutputLines | Where-Object { $_.Trim() }) -join [Environment]::NewLine
        if (-not $FailureDetail) {
            $FailureDetail = "psql exited with code $ExitCode."
        }

        $NewLine = [Environment]::NewLine
        throw "PostgreSQL command failed for database '$Database':${NewLine}$FailureDetail"
    }

    return $OutputLines
}

function Invoke-Alembic {
    param(
        [Parameter(Mandatory)]
        [string[]] $Arguments
    )

    & $PythonPath -m alembic @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Alembic command failed: alembic $($Arguments -join ' ')"
    }
}

try {
    $PsqlPath = Resolve-PostgresPsql
    Assert-Postgres18Client -PsqlPath $PsqlPath

    if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
        throw (
            "The backend virtual-environment Python was not found at '$PythonPath'. " +
            "Create backend/.venv and install the backend dependencies before running this script."
        )
    }

    if (-not (Test-Path -LiteralPath $EnvironmentExamplePath -PathType Leaf)) {
        throw "The environment template was not found at '$EnvironmentExamplePath'."
    }

    if ($null -eq $PostgresAdminPassword) {
        $PostgresAdminPassword = Read-Host (
            "Enter the password for PostgreSQL administrator '$PostgresAdminUser'"
        ) -AsSecureString
    }

    if ($PostgresAdminPassword.Length -eq 0) {
        throw "The PostgreSQL administrator password cannot be empty."
    }

    $HadPgPassword = Test-Path -LiteralPath "Env:PGPASSWORD"
    $PreviousPgPassword = if ($HadPgPassword) { $env:PGPASSWORD } else { $null }
    $PlainTextAdminPassword = $null

    try {
        $PlainTextAdminPassword = ConvertFrom-SecurePassword $PostgresAdminPassword
        $env:PGPASSWORD = $PlainTextAdminPassword

        Write-Host "Connecting to PostgreSQL 18 at ${DatabaseHost}:$DatabasePort..."
        $ServerVersionOutput = Invoke-PostgresSql -PsqlPath $PsqlPath `
            -Database "postgres" -Sql "SHOW server_version_num;"
        $ServerVersionNumber = (
            $ServerVersionOutput | Where-Object { $_.Trim() } | Select-Object -Last 1
        ).Trim()
        if ($ServerVersionNumber -notmatch "^18\d{4}$") {
            throw (
                "The server at ${DatabaseHost}:$DatabasePort is not PostgreSQL 18 " +
                "(server_version_num=$ServerVersionNumber)."
            )
        }

        if ($Reset) {
            Write-Host "Reset requested: recreating only the SkillProof local databases..."
            $ResetSql = @'
DROP DATABASE IF EXISTS skillproof WITH (FORCE);
DROP DATABASE IF EXISTS skillproof_test WITH (FORCE);
'@
            $null = Invoke-PostgresSql -PsqlPath $PsqlPath -Database "postgres" `
                -Sql $ResetSql
        }

        Write-Host "Creating or repairing the least-privilege local roles..."
        $RoleSql = @'
SET password_encryption TO 'scram-sha-256';

SELECT 'CREATE ROLE skillproof'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'skillproof')
\gexec
SELECT format('REVOKE %I FROM skillproof', granted_role.rolname)
FROM pg_auth_members AS membership
JOIN pg_roles AS granted_role ON granted_role.oid = membership.roleid
JOIN pg_roles AS member_role ON member_role.oid = membership.member
WHERE member_role.rolname = 'skillproof'
\gexec
ALTER ROLE skillproof WITH
    LOGIN
    PASSWORD 'skillproof'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT -1
    VALID UNTIL 'infinity';
ALTER ROLE skillproof SET search_path TO public;

SELECT 'CREATE ROLE skillproof_test'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'skillproof_test')
\gexec
SELECT format('REVOKE %I FROM skillproof_test', granted_role.rolname)
FROM pg_auth_members AS membership
JOIN pg_roles AS granted_role ON granted_role.oid = membership.roleid
JOIN pg_roles AS member_role ON member_role.oid = membership.member
WHERE member_role.rolname = 'skillproof_test'
\gexec
ALTER ROLE skillproof_test WITH
    LOGIN
    PASSWORD 'skillproof_test'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT -1
    VALID UNTIL 'infinity';
ALTER ROLE skillproof_test SET search_path TO public;
'@
        $null = Invoke-PostgresSql -PsqlPath $PsqlPath -Database "postgres" `
            -Sql $RoleSql

        Write-Host "Creating or repairing the SkillProof local databases..."
        $DatabaseSql = @'
SELECT 'CREATE DATABASE skillproof WITH OWNER skillproof ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'skillproof')
\gexec
ALTER DATABASE skillproof OWNER TO skillproof;
REVOKE ALL PRIVILEGES ON DATABASE skillproof FROM PUBLIC;
REVOKE ALL PRIVILEGES ON DATABASE skillproof FROM skillproof_test;
GRANT CONNECT, TEMPORARY ON DATABASE skillproof TO skillproof;

SELECT 'CREATE DATABASE skillproof_test WITH OWNER skillproof_test ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'skillproof_test')
\gexec
ALTER DATABASE skillproof_test OWNER TO skillproof_test;
REVOKE ALL PRIVILEGES ON DATABASE skillproof_test FROM PUBLIC;
REVOKE ALL PRIVILEGES ON DATABASE skillproof_test FROM skillproof;
GRANT CONNECT, TEMPORARY ON DATABASE skillproof_test TO skillproof_test;
'@
        $null = Invoke-PostgresSql -PsqlPath $PsqlPath -Database "postgres" `
            -Sql $DatabaseSql

        Write-Host "Securing the application database public schema..."
        $ApplicationSchemaSql = @'
SELECT 'CREATE SCHEMA public AUTHORIZATION skillproof'
WHERE NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'public')
\gexec
ALTER SCHEMA public OWNER TO skillproof;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO skillproof;
'@
        $null = Invoke-PostgresSql -PsqlPath $PsqlPath -Database $ApplicationDatabase `
            -Sql $ApplicationSchemaSql

        Write-Host "Securing the test database public schema..."
        $TestSchemaSql = @'
SELECT 'CREATE SCHEMA public AUTHORIZATION skillproof_test'
WHERE NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'public')
\gexec
ALTER SCHEMA public OWNER TO skillproof_test;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO skillproof_test;
'@
        $null = Invoke-PostgresSql -PsqlPath $PsqlPath -Database $TestDatabase `
            -Sql $TestSchemaSql
    }
    finally {
        if ($HadPgPassword) {
            $env:PGPASSWORD = $PreviousPgPassword
        }
        else {
            Remove-Item -LiteralPath "Env:PGPASSWORD" -ErrorAction SilentlyContinue
        }

        $PlainTextAdminPassword = $null
        $PreviousPgPassword = $null
        $PostgresAdminPassword = $null
    }

    if (-not (Test-Path -LiteralPath $EnvironmentPath -PathType Leaf)) {
        Copy-Item -LiteralPath $EnvironmentExamplePath -Destination $EnvironmentPath
        Write-Host "Created backend/.env from backend/.env.example."
    }
    else {
        Write-Host "Preserved the existing backend/.env."
    }

    $DatabaseUrl = (
        "postgresql+psycopg://${ApplicationRole}:${ApplicationPassword}" +
        "@${DatabaseHost}:$DatabasePort/$ApplicationDatabase"
    )
    $TestDatabaseUrl = (
        "postgresql+psycopg://${TestRole}:${TestPassword}" +
        "@${DatabaseHost}:$DatabasePort/$TestDatabase"
    )
    $env:DATABASE_URL = $DatabaseUrl
    $env:TEST_DATABASE_URL = $TestDatabaseUrl

    Write-Host "Applying and validating Alembic migrations with backend/.venv..."
    Push-Location $BackendRoot
    try {
        Invoke-Alembic -Arguments @("upgrade", "head")
        Invoke-Alembic -Arguments @("current")
        Invoke-Alembic -Arguments @("check")
    }
    finally {
        Pop-Location
    }

    Write-Host "SkillProof PostgreSQL setup completed successfully."
    Write-Host (
        "Application database: ${DatabaseHost}:$DatabasePort/" +
        "$ApplicationDatabase ($ApplicationRole)"
    )
    Write-Host "Test database:        ${DatabaseHost}:$DatabasePort/$TestDatabase ($TestRole)"
    Write-Host (
        "Credentials are low-value local-development credentials; " +
        "do not reuse them elsewhere."
    )
}
catch {
    Write-Error "SkillProof local PostgreSQL setup failed: $($_.Exception.Message)"
    exit 1
}
