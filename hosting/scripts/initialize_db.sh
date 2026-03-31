#!/bin/bash
set -e

DB_USER="${POSTGRES_USER:-abc}"
DB_PASSWORD="${POSTGRES_PASSWORD:-qwerty}"
DB_NAME="${POSTGRES_DB:-sentinel_db}"

echo "Checking if database '${DB_NAME}' exists..."

DB_EXISTS=$(psql -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'")

if [ "$DB_EXISTS" != "1" ]; then
    echo "Database '${DB_NAME}' does not exist. Creating..."
    psql -U "$DB_USER" -d postgres -c "CREATE DATABASE \"${DB_NAME}\" OWNER \"${DB_USER}\";"
    echo "Database '${DB_NAME}' created successfully."
else
    echo "Database '${DB_NAME}' already exists. Skipping creation."
fi
