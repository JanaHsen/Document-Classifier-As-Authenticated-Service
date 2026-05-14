# Owner: HADI
import hvac


def load_secrets_into_env(vault_addr: str, vault_token: str) -> dict[str, str]:
    """Read secrets from Vault and return them as a dict of env-var-name -> value."""
    client = hvac.Client(url=vault_addr, token=vault_token)

    result: dict[str, str] = {}

    db = client.secrets.kv.v2.read_secret_version(path="db", mount_point="secret")
    result["POSTGRES_PASSWORD"] = db["data"]["data"]["password"]

    jwt = client.secrets.kv.v2.read_secret_version(path="jwt", mount_point="secret")
    result["JWT_SECRET"] = jwt["data"]["data"]["signing_key"]

    minio = client.secrets.kv.v2.read_secret_version(path="minio", mount_point="secret")
    result["MINIO_ROOT_USER"] = minio["data"]["data"]["access_key"]
    result["MINIO_ROOT_PASSWORD"] = minio["data"]["data"]["secret_key"]

    try:
        redis = client.secrets.kv.v2.read_secret_version(path="redis", mount_point="secret")
        if redis_pw := redis["data"]["data"].get("password"):
            result["REDIS_PASSWORD"] = redis_pw
    except Exception:
        pass

    return result
