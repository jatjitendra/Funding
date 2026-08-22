# Convenience wrapper around the scripts in this folder.
#
#   make up          start local Postgres in Docker
#   make apply       apply schema + seed, then verify
#   make demo        apply and load demo data
#   make verify      check the schema without changing it
#   make psql        open a shell against the database
#   make reset       DESTRUCTIVE: drop everything and rebuild
#   make down        stop Postgres, keeping the volume
#   make clean       stop Postgres and delete the volume

.PHONY: up down clean apply demo verify psql reset dump

# Pick up DATABASE_URL and the POSTGRES_* variables from .env when present, the
# same way the shell scripts do.
ifneq (,$(wildcard .env))
include .env
export
endif

# psql does not understand SQLAlchemy's +psycopg driver suffix.
PSQL_URL := $(subst postgresql+psycopg:,postgresql:,$(DATABASE_URL))

up:
	docker compose up -d
	@echo "waiting for postgres to be healthy..."
	@until [ "$$(docker inspect -f '{{.State.Health.Status}}' apexfund-postgres 2>/dev/null)" = "healthy" ]; do sleep 1; done
	@echo "ready on 127.0.0.1:$${POSTGRES_PORT:-5432}"

down:
	docker compose down

clean:
	docker compose down -v

apply:
	./scripts/apply.sh --create-db

demo:
	./scripts/apply.sh --create-db --with-demo

verify:
	psql "$(PSQL_URL)" --no-psqlrc -v ON_ERROR_STOP=1 -f sql/verify.sql

psql:
	psql "$(PSQL_URL)"

reset:
	./scripts/reset.sh --yes

# Schema-only dump, handy for reviewing what is actually deployed.
dump:
	pg_dump --schema-only --no-owner --no-privileges "$(PSQL_URL)"
