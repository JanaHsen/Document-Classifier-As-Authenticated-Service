"""Simple Vault KV v2 reader used during app startup.

Reads secrets from Vault dev server (KV v2 mounted at `secret/`).
This module uses only the Python stdlib so it has no extra runtime deps.
"""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any


class VaultError(RuntimeError):
    pass


def _get(url: str, token: str, timeout: int = 5) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"X-Vault-Token": token})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        return json.loads(body.decode())


def read_kv_v2(path: str, vault_addr: str, token: str, retries: int = 5, delay: float = 1.0) -> Dict[str, Any]:
    """Read the KV v2 secret at `secret/data/{path}` and return the `data` mapping.

    Retries a few times to allow Vault to finish initializing.
    Raises VaultError on permanent failures.
    """
    url = f"{vault_addr.rstrip('/')}/v1/secret/data/{path}"
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            payload = _get(url, token)
            # KV v2 returns { "data": { "data": {...}, "metadata": {...} } }
            return payload["data"]["data"]
        except urllib.error.HTTPError as e:
            # 404 -> missing secret, treat as VaultError
            if e.code == 404:
                raise VaultError(f"secret not found at {path}") from e
            last_exc = e
        except Exception as e:
            last_exc = e
        time.sleep(delay)
    raise VaultError(f"failed to read secret {path} from Vault at {vault_addr}") from last_exc


def load_secrets_into_env(vault_addr: str, token: str) -> Dict[str, str]:
    """Fetch required secrets and return a mapping of env keys to values.

    This function does not modify os.environ directly to keep side-effects explicit in callers.
    Keys fetched: db (password), jwt (signing_key), minio (access_key, secret_key), redis (password)
    """
    secrets: Dict[str, str] = {}

    db = read_kv_v2("db", vault_addr, token)
    secrets["POSTGRES_PASSWORD"] = str(db.get("password", ""))

    jwt = read_kv_v2("jwt", vault_addr, token)
    secrets["JWT_SIGNING_KEY"] = str(jwt.get("signing_key", ""))

    minio = read_kv_v2("minio", vault_addr, token)
    secrets["MINIO_ROOT_USER"] = str(minio.get("access_key", ""))
    secrets["MINIO_ROOT_PASSWORD"] = str(minio.get("secret_key", ""))

    try:
        redis = read_kv_v2("redis", vault_addr, token)
        secrets["REDIS_PASSWORD"] = str(redis.get("password", ""))
    except VaultError:
        # Redis is optional; leave absent if not present
        pass

    # Basic validation
    missing = [k for k, v in secrets.items() if v == ""]
    if missing:
        raise VaultError(f"missing values for secrets: {missing}")

    return secrets
