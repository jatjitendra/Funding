#!/usr/bin/env bash
#
# Drop every ApexFund table and rebuild the schema from scratch.
#
#   ./scripts/reset.sh --yes                # rebuild empty
#   ./scripts/reset.sh --yes --with-demo    # rebuild and load demo data
#
# DESTRUCTIVE: every user, account, order, payout and contact message is
# deleted. --yes is required; there is no interactive prompt so this cannot be
# triggered by accident in a pipeline.
#
# Refuses to run when the target looks like production. Set
# ALLOW_PRODUCTION_RESET=1 to override, and think twice before you do.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

CONFIRMED=false
PASSTHROUGH=()

for arg in "$@"; do
    case "$arg" in
        --yes) CONFIRMED=true ;;
        --with-demo) PASSTHROUGH+=("$arg") ;;
        -h|--help)
            sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $arg" >&2
            exit 2
            ;;
    esac
done

if [[ "$CONFIRMED" != true ]]; then
    echo "Refusing to drop anything without --yes." >&2
    echo "This deletes all ApexFund data in the target database." >&2
    exit 1
fi

if [[ -f "${ROOT_DIR}/.env" ]]; then
    # shellcheck disable=SC1091
    set -a && source "${ROOT_DIR}/.env" && set +a
fi

PSQL_TARGET="${DATABASE_URL:-}"
PSQL_TARGET="${PSQL_TARGET/postgresql+psycopg:/postgresql:}"
PSQL_TARGET="${PSQL_TARGET/postgres+psycopg:/postgresql:}"

if [[ -n "$PSQL_TARGET" ]]; then
    CONN=("$PSQL_TARGET")
    DB_NAME="$(basename "${PSQL_TARGET%%\?*}")"
else
    DB_NAME="${PGDATABASE:-apexfund}"
    CONN=("--dbname=${DB_NAME}")
fi

if [[ "${ALLOW_PRODUCTION_RESET:-0}" != "1" ]]; then
    case "${PSQL_TARGET}${DB_NAME}" in
        *prod*|*production*|*live*)
            echo "Target '${DB_NAME}' looks like production. Refusing." >&2
            echo "Set ALLOW_PRODUCTION_RESET=1 if you are certain." >&2
            exit 1
            ;;
    esac
fi

echo "Dropping ApexFund objects in ${DB_NAME}"
psql "${CONN[@]}" --quiet --no-psqlrc -v ON_ERROR_STOP=1 -f "${ROOT_DIR}/sql/drop_all.sql"

echo "Rebuilding"
"${SCRIPT_DIR}/apply.sh" "${PASSTHROUGH[@]+"${PASSTHROUGH[@]}"}"
