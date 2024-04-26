from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from io import BytesIO
from db import db_handlers
from schemas.responses import MediaResponseModel
from .dependencies import get_db, api_key_dependency

router = APIRouter(prefix="/api")


@router.post(
    "/medias",
    response_model=MediaResponseModel,
    tags=["media"],
    summary="Загрузить медиафайл",
    description="Позволяет пользователю загрузить медиафайл, возвращая идентификатор медиа.",
)
async def upload_media(
    file: UploadFile = File(...),
    api_key: str = Depends(api_key_dependency),
    db: AsyncSession = Depends(get_db),
):
    user = await db_handlers.get_user_by_api(api_key, db)
    file_data = await file.read()
    media_id = await db_handlers.save_media(
        db, filename=file.filename, file_data=file_data
    )
    return {"result": True, "media_id": media_id}


@router.get(
    "/media/{media_id}",
    tags=["media"],
    summary="Получить медиафайл",
    description="Предоставляет медиафайл для скачивания по его идентификатору, если он существует.",
)
async def get_media(media_id: int, db: AsyncSession = Depends(get_db)):
    media = await db_handlers.get_media_handler(db, media_id)
    if media:
        return StreamingResponse(
            BytesIO(media.file_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={media.filename}"},
        )
    else:
        return {"error": "Media not found"}
