#!/usr/bin/env bash
#
# Apply the ApexFund schema to a PostgreSQL database.
#
#   ./scripts/apply.sh                  # apply schema + seed, then verify
#   ./scripts/apply.sh --create-db      # create the database first if missing
#   ./scripts/apply.sh --with-demo      # also load sql/optional_demo_data.sql
#   ./scripts/apply.sh --no-verify      # skip the verification pass
#
# Connection details come from DATABASE_URL, or from the standard PG* variables
# (PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE) if it is unset. A .env file
# next to this folder is sourced when present.
#
# Every statement is idempotent, so re-running is safe and is the intended way
# to pick up changes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SQL_DIR="${ROOT_DIR}/sql"

CREATE_DB=false
WITH_DEMO=false
RUN_VERIFY=true

for arg in "$@"; do
    case "$arg" in
        --create-db) CREATE_DB=true ;;
        --with-demo) WITH_DEMO=true ;;
        --no-verify) RUN_VERIFY=false ;;
        -h|--help)
            sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $arg" >&2
            exit 2
            ;;
    esac
done

if [[ -f "${ROOT_DIR}/.env" ]]; then
    # shellcheck disable=SC1091
    set -a && source "${ROOT_DIR}/.env" && set +a
fi

# SQLAlchemy uses postgresql+psycopg:// to pick a driver; psql only understands
# postgresql://, so strip the driver suffix if it is there.
PSQL_TARGET="${DATABASE_URL:-}"
PSQL_TARGET="${PSQL_TARGET/postgresql+psycopg:/postgresql:}"
PSQL_TARGET="${PSQL_TARGET/postgres+psycopg:/postgresql:}"

if [[ -n "$PSQL_TARGET" ]]; then
    CONN=("$PSQL_TARGET")
    DB_NAME="$(basename "${PSQL_TARGET%%\?*}")"
    ADMIN_TARGET="${PSQL_TARGET%/*}/postgres"
    ADMIN_CONN=("$ADMIN_TARGET")
else
    DB_NAME="${PGDATABASE:-apexfund}"
    CONN=("--dbname=${DB_NAME}")
    ADMIN_CONN=("--dbname=postgres")
fi

psql_run() {
    psql "${CONN[@]}" --quiet --no-psqlrc -v ON_ERROR_STOP=1 "$@"
}

echo "Target database: ${DB_NAME}"

if [[ "$CREATE_DB" == true ]]; then
    echo "-- ensuring database ${DB_NAME} exists"

    if psql "${ADMIN_CONN[@]}" --no-psqlrc -tAc \
        "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1; then
        echo "   already exists"
    else
        psql "${ADMIN_CONN[@]}" --no-psqlrc -v ON_ERROR_STOP=1 \
            -c "CREATE DATABASE \"${DB_NAME}\" ENCODING 'UTF8'"
        echo "   created"
    fi
fi

for file in 001_tables.sql 002_indexes.sql 003_views.sql 004_seed_plans.sql 005_roles_grants.sql; do
    echo "-- applying ${file}"
    psql_run -f "${SQL_DIR}/${file}"
done

if [[ "$WITH_DEMO" == true ]]; then
    echo "-- applying optional_demo_data.sql"
    psql_run -f "${SQL_DIR}/optional_demo_data.sql"
fi

if [[ "$RUN_VERIFY" == true ]]; then
    echo "-- verifying"
    psql_run -f "${SQL_DIR}/verify.sql"
fi

echo
echo "Done. Point the backend at this database with:"
echo "  export DATABASE_URL=\"postgresql+psycopg://<user>:<password>@<host>:5432/${DB_NAME}\""
