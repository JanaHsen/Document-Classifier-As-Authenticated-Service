from pydantic import BaseModel, ConfigDict

from app.api.schemas.user import Role


class RoleToggleRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    role: Role
