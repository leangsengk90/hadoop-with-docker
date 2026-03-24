#!/bin/sh
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE hue_metadata;
    GRANT ALL PRIVILEGES ON DATABASE hue_metadata TO $POSTGRES_USER;
EOSQL
