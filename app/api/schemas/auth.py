from pydantic import BaseModel, ConfigDict

from app.core.constants import Role


class RoleToggleRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    role: Role
