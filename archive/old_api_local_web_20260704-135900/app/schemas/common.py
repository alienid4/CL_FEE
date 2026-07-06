from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    ok: bool
    data: Any = None


class ApiError(BaseModel):
    ok: bool = False
    error: dict[str, str]
