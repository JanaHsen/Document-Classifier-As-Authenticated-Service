import os
import sys

from app.infra import vault


def main() -> int:
    vault_addr = os.environ.get("VAULT_ADDR", "http://vault:8200")
    token = os.environ.get("VAULT_TOKEN")
    if not token:
        print("ERROR: VAULT_TOKEN not set", file=sys.stderr)
        return 2
    try:
        secrets = vault.load_secrets_into_env(vault_addr, token)
    except Exception as e:
        print(f"ERROR: failed to load secrets from Vault: {e}", file=sys.stderr)
        return 3

    # write secrets to a temporary envfile for sourcing
    path = "/tmp/vault_secrets.env"
    with open(path, "w") as f:
        for k, v in secrets.items():
            # simple safe write; values shouldn't contain newlines for our secrets
            f.write(f"{k}={v}\n")
    print("Vault bootstrap: wrote secrets to", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
