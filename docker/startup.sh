#!/bin/sh
set -eu

# Bootstrap Vault secrets into /tmp/vault_secrets.env using the project python
echo "Running Vault bootstrap..."
PYTHONPATH=/app:$PYTHONPATH python /app/docker/vault/bootstrap.py
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "Vault bootstrap failed with code $rc" >&2
  exit $rc
fi

if [ -f /tmp/vault_secrets.env ]; then
  echo "Sourcing Vault secrets into environment"
  set -o allexport
  . /tmp/vault_secrets.env
  set +o allexport
fi

echo "Starting: $@"
exec "$@"
