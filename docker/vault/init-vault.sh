#!/bin/sh
set -eu

VAULT_ADDR=${VAULT_ADDR:-http://vault:8200}
TOKEN=${VAULT_TOKEN:-root}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-password}
MINIO_ROOT_USER=${MINIO_ROOT_USER:-minio}
MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD:-minio123}
REDIS_PASSWORD=${REDIS_PASSWORD:-}
JWT_SIGNING_KEY=${JWT_SIGNING_KEY:-dev-jwt-signing-key}

echo "Vault init: waiting for Vault to be healthy at $VAULT_ADDR"
until curl -sSf "$VAULT_ADDR/v1/sys/health" >/dev/null 2>&1; do
  sleep 1
done
echo "Vault is healthy. Using token=${TOKEN}"

curl_opts="-s -H X-Vault-Token: $TOKEN -H Content-Type: application/json"

kv_exists() {
  path="$1"
  status=$(curl -o /dev/null -w "%{http_code}" -s -H "X-Vault-Token: $TOKEN" "$VAULT_ADDR/v1/secret/data/$path" || true)
  [ "$status" = "200" ]
}

kv_write() {
  path="$1"
  payload="$2"
  echo "Writing secret to secret/data/$path"
  curl -X POST $curl_opts -d "$payload" "$VAULT_ADDR/v1/secret/data/$path" >/dev/null
}

if kv_exists db; then
  echo "DB secret already present, skipping"
else
  payload=$(printf '{"data":{"password":"%s"}}' "$POSTGRES_PASSWORD")
  kv_write db "$payload"
fi

if kv_exists jwt; then
  echo "JWT secret already present, skipping"
else
  payload=$(printf '{"data":{"signing_key":"%s"}}' "$JWT_SIGNING_KEY")
  kv_write jwt "$payload"
fi

if kv_exists minio; then
  echo "MinIO secret already present, skipping"
else
  payload=$(printf '{"data":{"access_key":"%s","secret_key":"%s"}}' "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD")
  kv_write minio "$payload"
fi

if [ -n "$REDIS_PASSWORD" ]; then
  if kv_exists redis; then
    echo "Redis secret already present, skipping"
  else
    payload=$(printf '{"data":{"password":"%s"}}' "$REDIS_PASSWORD")
    kv_write redis "$payload"
  fi
else
  echo "No REDIS_PASSWORD provided; skipping Redis secret"
fi

echo "Vault init completed"

exit 0
