#!/bin/bash
# Cria o banco "evolution" (usado pela Evolution API) além do banco principal "sgv".
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE evolution;
EOSQL
