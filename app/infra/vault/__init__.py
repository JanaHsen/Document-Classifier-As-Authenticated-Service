# Owner: HADI
import hvac


def load_secrets_into_env(vault_addr: str, vault_token: str) -> dict[str, str]:
    """Read secrets from Vault and return them as a dict of env-var-name -> value."""
    # Open a connection to Vault using the given address and master token.
    client = hvac.Client(url=vault_addr, token=vault_token)

    # Empty dictionary to collect the secrets we read.
    result: dict[str, str] = {}

    # Read the secret stored at secret/db (holds the Postgres password).
    db = client.secrets.kv.v2.read_secret_version(path="db", mount_point="secret")
    # Pull the password value out of Vault's nested response and save it.
    result["POSTGRES_PASSWORD"] = db["data"]["data"]["password"]

    # Read the secret stored at secret/jwt (holds the JWT signing key).
    jwt = client.secrets.kv.v2.read_secret_version(path="jwt", mount_point="secret")
    # Pull the signing_key value out and save it under JWT_SECRET.
    result["JWT_SECRET"] = jwt["data"]["data"]["signing_key"]

    # Read the secret stored at secret/minio (holds MinIO root credentials).
    minio = client.secrets.kv.v2.read_secret_version(path="minio", mount_point="secret")
    # Save the MinIO access key as MINIO_ROOT_USER.
    result["MINIO_ROOT_USER"] = minio["data"]["data"]["access_key"]
    # Save the MinIO secret key as MINIO_ROOT_PASSWORD.
    result["MINIO_ROOT_PASSWORD"] = minio["data"]["data"]["secret_key"]

    # Optional: try to grab a Redis password too. Skip silently if missing.
    try:
        # Read the secret stored at secret/redis (may or may not exist).
        redis = client.secrets.kv.v2.read_secret_version(path="redis", mount_point="secret")
        # If a password field is present and non-empty, save it.
        if redis_pw := redis["data"]["data"].get("password"):
            result["REDIS_PASSWORD"] = redis_pw
    except Exception:
        # Vault has no Redis secret (or it failed to read) — that's fine.
        pass

    # Hand the collected secrets back to the caller.
    return result
