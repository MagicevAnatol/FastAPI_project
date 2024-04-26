from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import db_handlers
from schemas.responses import TweetsResponseModel, TweetResponseModel
from schemas.schemas import TweetCreateRequest
from .dependencies import api_key_dependency, get_db

router = APIRouter(prefix="/api/tweets")


@router.get(
    "/",
    dependencies=[Depends(api_key_dependency)],
    response_model=TweetsResponseModel,
    tags=["tweets"],
    summary="Получить список твитов",
    description="Получает список всех твитов в ленте.",
)
async def get_tweets(db: AsyncSession = Depends(get_db)):
    tweets = await db_handlers.get_tweet_feed(db)
    return {"result": True, "tweets": tweets}


@router.post(
    "/",
    response_model=TweetResponseModel,
    tags=["tweets"],
    summary="Создать новый твит",
    description="Создает новый твит с данными, предоставленными пользователем.",
)
async def create_tweet(
    tweet_request: TweetCreateRequest,
    api_key: str = Depends(api_key_dependency),
    db: AsyncSession = Depends(get_db),
):
    user = await db_handlers.get_user_by_api(api_key, db)
    tweet_id = await db_handlers.create_tweet(
        db, user.id, tweet_request.tweet_data, tweet_request.tweet_media_ids
    )
    return {"result": True, "tweet_id": tweet_id}


@router.delete(
    "/{tweet_id}",
    tags=["tweets"],
    summary="Удалить твит",
    description="Удаляет твит по его идентификатору, если пользователь является владельцем.",
)
async def delete_tweet_route(
    tweet_id: int,
    api_key: str = Depends(api_key_dependency),
    db: AsyncSession = Depends(get_db),
):
    user = await db_handlers.get_user_by_api(api_key, db)
    await db_handlers.delete_tweet(db, tweet_id, user.id)
    return {"result": True}


@router.post(
    "/{tweet_id}/likes",
    tags=["tweets"],
    summary="Поставить лайк твиту",
    description="Добавляет лайк к указанному твиту от имени пользователя.",
)
async def like_tweet(
    tweet_id: int,
    api_key: str = Depends(api_key_dependency),
    db: AsyncSession = Depends(get_db),
):
    user = await db_handlers.get_user_by_api(api_key, db)
    await db_handlers.like_tweet(db, tweet_id, user.id)
    return {"result": True}


@router.delete(
    "/{tweet_id}/likes",
    tags=["tweets"],
    summary="Убрать лайк с твита",
    description="Удаляет лайк у указанного твита от имени пользователя.",
)
async def unlike_tweet(
    tweet_id: int,
    api_key: str = Depends(api_key_dependency),
    db: AsyncSession = Depends(get_db),
):
    user = await db_handlers.get_user_by_api(api_key, db)
    await db_handlers.unlike_tweet(db, tweet_id, user.id)
    return {"result": True}
