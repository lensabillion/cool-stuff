from pydantic import BaseModel


class ToggleResponse(BaseModel):
    ok: bool
