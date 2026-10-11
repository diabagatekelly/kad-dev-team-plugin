#!/usr/bin/env bash
# Applies every ops/migrations/*.sql not yet recorded in schema_migrations,
# in file-name order, each in its own transaction. Connection settings come
# from the standard PG* environment variables.
set -euo pipefail
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/migrations"
psql -v ON_ERROR_STOP=1 -qc "create table if not exists schema_migrations (name text primary key, applied_at timestamptz not null default now())"
for file in "$dir"/*.sql; do
  name="$(basename "$file")"
  if [ -z "$(psql -tAc "select 1 from schema_migrations where name = '$name'")" ]; then
    psql -v ON_ERROR_STOP=1 --single-transaction -f "$file"
    psql -qc "insert into schema_migrations (name) values ('$name')"
    echo "applied $name"
  fi
done
