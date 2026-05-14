#!/bin/sh
set -e

export VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
export VAULT_TOKEN="${VAULT_TOKEN:-root}"

until vault status > /dev/null 2>&1; do
    echo "Waiting for Vault..."
    sleep 2
done

vault_write_if_missing() {
    path="$1"
    shift
    if ! vault kv get "$path" > /dev/null 2>&1; then
        vault kv put "$path" "$@"
        echo "Seeded $path"
    else
        echo "Skipped $path (already exists)"
    fi
}

vault_write_if_missing secret/db \
    password="${POSTGRES_PASSWORD:-postgres}"

vault_write_if_missing secret/jwt \
    signing_key="${JWT_SECRET:-changeme-dev-secret}"

vault_write_if_missing secret/minio \
    access_key="${MINIO_ROOT_USER:-minioadmin}" \
    secret_key="${MINIO_ROOT_PASSWORD:-minioadmin}"

if [ -n "${REDIS_PASSWORD}" ]; then
    vault_write_if_missing secret/redis password="${REDIS_PASSWORD}"
fi

echo "Vault seeding complete"
