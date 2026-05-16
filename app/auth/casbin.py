import os
import tempfile
from functools import lru_cache
from pathlib import Path

import casbin
from casbin_sqlalchemy_adapter import Adapter


CASBIN_MODEL_CONF = """\
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
"""


def _get_model_path() -> str:
    
    model_path = Path(tempfile.gettempdir()) / "doc_classifier_rbac_model.conf"
    if not model_path.exists() or model_path.read_text() != CASBIN_MODEL_CONF:
        model_path.write_text(CASBIN_MODEL_CONF)
    return str(model_path)


def _sync_database_url() -> str:
    
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/docclassifier",
    )
    return url.replace("+asyncpg", "").replace("+aiosqlite", "")


@lru_cache(maxsize=1)
def get_enforcer() -> casbin.Enforcer:

    return casbin.Enforcer(_get_model_path(), Adapter(_sync_database_url()))


def assert_policies_seeded() -> None:
   
    enforcer = get_enforcer()
    if not enforcer.get_policy():
        raise RuntimeError(
            "Casbin policy table is empty. Run "
            "`python scripts/seed_policies.py` before starting the api. "
            "An api with no RBAC policies cannot enforce permissions "
            "safely and refuses to boot."
        )
