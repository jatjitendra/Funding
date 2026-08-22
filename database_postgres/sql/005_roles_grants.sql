-- ApexFund — roles and grants
--
-- Three roles, so the API never connects as the schema owner:
--
--   apexfund_app       what the backend logs in as: read/write rows, no DDL.
--   apexfund_readonly  analytics and support: SELECT only.
--   apexfund_migrator  owns the schema; only used to apply DDL.
--
-- Roles are created WITHOUT a password on purpose, so no default credential is
-- ever committed to this repository. A password-less role cannot log in under
-- scram-sha-256 or md5 authentication, so you must set one before use:
--
--   ALTER ROLE apexfund_app PASSWORD 'a-strong-generated-secret';
--
-- Safe to re-run.

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'apexfund_app') THEN
        CREATE ROLE apexfund_app LOGIN;
        RAISE NOTICE 'Created role apexfund_app with no password — set one with ALTER ROLE before use.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'apexfund_readonly') THEN
        CREATE ROLE apexfund_readonly LOGIN;
        RAISE NOTICE 'Created role apexfund_readonly with no password — set one with ALTER ROLE before use.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'apexfund_migrator') THEN
        CREATE ROLE apexfund_migrator LOGIN;
        RAISE NOTICE 'Created role apexfund_migrator with no password — set one with ALTER ROLE before use.';
    END IF;
END
$$;

-- Resolved at run time so the script works whatever the database is called.
DO $$
BEGIN
    EXECUTE format(
        'GRANT CONNECT ON DATABASE %I TO apexfund_app, apexfund_readonly, apexfund_migrator',
        current_database()
    );
END
$$;

GRANT USAGE ON SCHEMA public TO apexfund_app, apexfund_readonly;
GRANT USAGE, CREATE ON SCHEMA public TO apexfund_migrator;

-- The application reads and writes rows but must not alter the schema.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO apexfund_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO apexfund_app;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO apexfund_readonly;

-- Plans are configuration, not application data: the API only ever reads them,
-- and the upsert in app/seed.py runs on startup. Revoke the write grants below
-- if you prefer plan changes to go exclusively through migrations, and set
-- AUTO_CREATE_TABLES=false plus skip seeding in that case.
-- REVOKE INSERT, UPDATE, DELETE ON plans FROM apexfund_app;

-- Tables added by future migrations should inherit the same grants, otherwise
-- the app role silently loses access to them.
--
-- Default privileges are recorded per creating role, so they are set both for
-- whoever runs this script and for apexfund_migrator, which is what applies
-- DDL in a deployed setup.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO apexfund_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO apexfund_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO apexfund_readonly;

ALTER DEFAULT PRIVILEGES FOR ROLE apexfund_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO apexfund_app;
ALTER DEFAULT PRIVILEGES FOR ROLE apexfund_migrator IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO apexfund_app;
ALTER DEFAULT PRIVILEGES FOR ROLE apexfund_migrator IN SCHEMA public
    GRANT SELECT ON TABLES TO apexfund_readonly;

COMMIT;
