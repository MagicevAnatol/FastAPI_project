from typing import AsyncGenerator
from fastapi import Header, HTTPException, Depends

from sqlalchemy.ext.asyncio import AsyncSession


from db.database import async_session
from db.db_handlers import get_user_by_api


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def api_key_dependency(
    api_key: str = Header(...), db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_api(api_key, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
