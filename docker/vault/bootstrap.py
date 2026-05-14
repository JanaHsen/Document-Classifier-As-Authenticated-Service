#!/usr/bin/env python3
"""Read secrets from Vault and write them to /tmp/vault_secrets.env."""
import os
import sys

sys.path.insert(0, "/app")

from app.infra import vault  # noqa: E402

vault_addr = os.environ["VAULT_ADDR"]
vault_token = os.environ["VAULT_TOKEN"]

secrets = vault.load_secrets_into_env(vault_addr, vault_token)

with open("/tmp/vault_secrets.env", "w") as f:
    for key, value in secrets.items():
        f.write(f"{key}={value}\n")

print(f"Wrote {len(secrets)} secrets to /tmp/vault_secrets.env")
