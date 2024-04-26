from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import db_handlers
from db.db_handlers import get_user_by_api
from schemas.responses import UserResponseModel
from .dependencies import get_db, api_key_dependency

router = APIRouter(prefix="/api/users")


@router.get(
    "/me",
    response_model=UserResponseModel,
    tags=["users"],
    summary="Получить текущего пользователя",
    description="Получает профиль текущего пользователя, используя предоставленный API ключ.",
)
async def get_current_user(
    api_key: str = Depends(api_key_dependency), db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_api(api_key, db)
    followers = await db_handlers.get_followers(user.id, db)
    following = await db_handlers.get_following(user.id, db)
    return {
        "result": "true",
        "user": {
            "id": user.id,
            "name": user.name,
            "followers": followers,
            "following": following,
        },
    }


@router.get(
    "/{user_id}",
    response_model=UserResponseModel,
    tags=["users"],
    summary="Получить профиль пользователя",
    description="Отображает профиль пользователя по его уникальному идентификатору.",
)
async def get_user_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db_handlers.get_user_by_id(user_id, db)
    if not user:
        return {"result": False, "message": "User not found"}
    followers = await db_handlers.get_followers(user_id, db)
    following = await db_handlers.get_following(user_id, db)
    return {
        "result": "true",
        "user": {
            "id": user.id,
            "name": user.name,
            "followers": followers,
            "following": following,
        },
    }


@router.post(
    "/{followed_id}/follow",
    tags=["users"],
    summary="Подписаться на пользователя",
    description="Позволяет текущему пользователю подписаться на другого пользователя по идентификатору.",
)
async def follow_user(
    followed_id: int,
    api_key: str = Depends(api_key_dependency),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_api(api_key, db)
    success = await db_handlers.follow_user(user.id, followed_id, db)
    return {"result": success}


@router.delete(
    "/{followed_id}/follow",
    tags=["users"],
    summary="Отписаться от пользователя",
    description="Позволяет текущему пользователю отписаться от другого пользователя по идентификатору.",
)
async def unfollow_user(
    followed_id: int,
    api_key: str = Depends(api_key_dependency),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_api(api_key, db)
    success = await db_handlers.unfollow_user(user.id, followed_id, db)
    return {"result": success}
