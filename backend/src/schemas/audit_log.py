from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int | None
    user_id: int | None
    action: str
    resource_type: str | None
    resource_id: int | None
    ip_address: str | None
    details: dict[str, Any] | None
    created_at: datetime
