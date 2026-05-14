#!/bin/sh
set -e

python /app/docker/vault/bootstrap.py

set -a
. /tmp/vault_secrets.env
set +a

exec "$@"
