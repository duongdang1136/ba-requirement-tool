from pydantic import BaseModel
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


class ClientConfigOut(BaseModel):
    max_upload_size_mb: int
    allowed_extensions: list[str]


@router.get("/client", response_model=ClientConfigOut)
def get_client_config():
    return ClientConfigOut(
        max_upload_size_mb=settings.max_upload_size_mb,
        allowed_extensions=settings.allowed_extensions,
    )
