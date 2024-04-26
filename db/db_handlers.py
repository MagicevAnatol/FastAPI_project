from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import LargeBinary
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine, EncryptedType

from .database import settings
from .models import Media, Tweet, User, likes_table, followers


async def get_user_by_api(api_key: str, db: AsyncSession) -> User:
    """
    Получает пользователя по API ключу.

    Args:
        api_key (str): API ключ пользователя для поиска.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        User: Объект пользователя, если найден.

    Raises:
        HTTPException: Если пользователь не найден.
    """
    encrypted_api_key = EncryptedType(
        LargeBinary, settings.SECRET_KEY, AesEngine, "pkcs5"
    ).process_bind_param(api_key, None)
    try:
        result = await db.execute(
            select(User).filter(User.api_key == encrypted_api_key)
        )
        user = result.scalar_one()
        return user
    except NoResultFound:
        raise HTTPException(status_code=401, detail="Invalid API key")


async def save_media(db: AsyncSession, filename: str, file_data: bytes) -> int:
    """
    Сохраняет медиафайл в базу данных.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        filename (str): Имя файла.
        file_data (bytes): Данные файла.

    Returns:
        int: Идентификатор сохраненного медиафайла.
    """
    media = Media(filename=filename, file_data=file_data)
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media.id


async def create_tweet(
    db: AsyncSession,
    user_id: int,
    tweet_data: str,
    tweet_media_ids: Optional[List[int]] = None,
) -> int:
    """
    Создает новый твит.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        user_id (int): Идентификатор пользователя.
        tweet_data (str): Текст твита.
        tweet_media_ids (Optional[List[int]]): Список идентификаторов медиафайлов.

    Returns:
        int: Идентификатор созданного твита.
    """
    tweet_media_ids = tweet_media_ids or []
    tweet = Tweet(
        user_id=user_id, tweet_data=tweet_data, tweet_media_ids=tweet_media_ids
    )
    db.add(tweet)
    await db.commit()
    await db.refresh(tweet)
    return tweet.id


async def delete_tweet(db: AsyncSession, tweet_id: int, user_id: int) -> None:
    """
    Удаляет твит.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        tweet_id (int): Идентификатор твита.
        user_id (int): Идентификатор пользователя.

    Raises:
        HTTPException: Если пользователь не имеет права удалять твит.
    """
    result = await db.execute(select(Tweet).filter(Tweet.id == tweet_id))
    tweet = result.scalar_one_or_none()

    if not tweet or tweet.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to delete this tweet"
        )

    await db.delete(tweet)
    await db.commit()


async def like_tweet(db: AsyncSession, tweet_id: int, user_id: int) -> None:
    """
    Добавляет лайк твиту.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        tweet_id (int): Идентификатор твита.
        user_id (int): Идентификатор пользователя.
    """
    await db.execute(likes_table.insert().values(tweet_id=tweet_id, user_id=user_id))
    await db.commit()


async def unlike_tweet(db: AsyncSession, tweet_id: int, user_id: int) -> None:
    """
    Удаляет лайк с твита.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        tweet_id (int): Идентификатор твита.
        user_id (int): Идентификатор пользователя.
    """
    await db.execute(
        likes_table.delete().where(
            (likes_table.c.tweet_id == tweet_id) & (likes_table.c.user_id == user_id)
        )
    )
    await db.commit()


async def is_tweet_owner(db: AsyncSession, tweet_id: int, user_id: int) -> bool:
    """
    Проверяет, является ли пользователь владельцем твита.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        tweet_id (int): Идентификатор твита.
        user_id (int): Идентификатор пользователя.

    Returns:
        bool: Возвращает True, если пользователь является владельцем твита, иначе False.
    """
    result = await db.execute(
        select(Tweet).filter(Tweet.id == tweet_id, Tweet.user_id == user_id)
    )
    tweet = result.first()
    return tweet is not None


async def get_likes_for_tweet(db: AsyncSession, tweet_id: int) -> List[dict]:
    """
    Получает список пользователей, которые поставили лайк твиту.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        tweet_id (int): Идентификатор твита.

    Returns:
        List[dict]: Список словарей, содержащих информацию о пользователях.
    """
    result = await db.execute(
        select(User.id, User.name)
        .select_from(likes_table)
        .join(User, User.id == likes_table.c.user_id)
        .where(likes_table.c.tweet_id == tweet_id)
    )
    likes = [{"user_id": user_id, "name": name} for (user_id, name) in result]
    return likes


async def get_tweet_feed(db: AsyncSession) -> List[dict]:
    """
    Получает ленту твитов с информацией о лайках и вложениях.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        List[dict]: Список словарей, содержащих информацию о твитах.
    """
    result = await db.execute(
        select(Tweet)
        .options(selectinload(Tweet.user))
        .order_by(Tweet.id.desc())
        .limit(50)
    )
    tweets = result.scalars().all()
    tweet_list = []
    for tweet in tweets:
        likes = await get_likes_for_tweet(db, tweet.id)

        attachments = []
        if tweet.tweet_media_ids:
            for media_id in tweet.tweet_media_ids:
                attachment_link = f"/api/media/{media_id}"
                attachments.append(attachment_link)

        tweet_dict = {
            "id": tweet.id,
            "content": tweet.tweet_data,
            "attachments": attachments,
            "author": {"id": tweet.user.id, "name": tweet.user.name},
            "likes": [
                {"user_id": like["user_id"], "name": like["name"]} for like in likes
            ],
        }
        tweet_list.append(tweet_dict)

    return tweet_list


async def get_media_handler(db: AsyncSession, media_id: int) -> Media:
    """
    Получает медиафайл по идентификатору.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        media_id (int): Идентификатор медиафайла.

    Returns:
        Media: Объект медиафайла, если он найден, иначе None.
    """
    result = await db.execute(select(Media).filter(Media.id == media_id))
    media = result.scalar_one_or_none()
    return media


async def get_followers(user_id: int, db: AsyncSession) -> List[dict]:
    """
    Получает список подписчиков пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        List[dict]: Список словарей, содержащих идентификаторы и имена подписчиков.
    """
    result = await db.execute(
        select(User)
        .join(followers, User.id == followers.c.follower_id)
        .where(followers.c.followed_id == user_id)
    )
    followers_list = [
        {"id": follower.id, "name": follower.name}
        for follower in result.scalars().all()
    ]
    return followers_list


async def get_following(user_id: int, db: AsyncSession) -> List[dict]:
    """
    Получает список пользователей, на которых подписан пользователь.

    Args:
        user_id (int): Идентификатор пользователя.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        List[dict]: Список словарей, содержащих идентификаторы и имена подписок.
    """
    result = await db.execute(
        select(User)
        .join(followers, User.id == followers.c.followed_id)
        .where(followers.c.follower_id == user_id)
    )
    following_list = [
        {"id": following.id, "name": following.name}
        for following in result.scalars().all()
    ]
    return following_list


async def get_user_by_id(user_id: int, db: AsyncSession) -> User:
    """
    Получает пользователя по идентификатору.

    Args:
        user_id (int): Идентификатор пользователя.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        User: Объект пользователя, если он найден, иначе None.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# Функция для добавления подписки на пользователя
async def follow_user(follower_id: int, followed_id: int, db: AsyncSession) -> bool:
    """
    Добавляет подписку пользователя на другого пользователя.

    Args:
        follower_id (int): Идентификатор пользователя, который подписывается.
        followed_id (int): Идентификатор пользователя, на которого подписываются.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        bool: Возвращает True, если подписка успешно добавлена, иначе False.
    """
    new_follow = followers.insert().values(
        follower_id=follower_id, followed_id=followed_id
    )
    try:
        await db.execute(new_follow)
        await db.commit()
        return True
    except Exception as e:
        # Обработка возможных исключений, например, если подписка уже существует
        await db.rollback()
        return False


# Функция для удаления подписки на пользователя
async def unfollow_user(follower_id: int, followed_id: int, db: AsyncSession) -> bool:
    """
    Удаляет подписку пользователя на другого пользователя.

    Args:
        follower_id (int): Идентификатор пользователя, который отписывается.
        followed_id (int): Идентификатор пользователя, от которого отписываются.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        bool: Возвращает True, если подписка успешно удалена, иначе False.
    """
    unfollow = followers.delete().where(
        (followers.c.follower_id == follower_id)
        & (followers.c.followed_id == followed_id)
    )
    result = await db.execute(unfollow)
    if result.rowcount > 0:
        await db.commit()
        return True
    else:
        # Если подписка не найдена
        await db.rollback()
        return False


async def create_initial_data(session: AsyncSession) -> None:
    """
     Создает начальные данные в базе данных, включая пользователей, твиты, медиафайлы,
     подписчиков и лайки для тестирования.

    Эта функция создает начальный набор пользователей, твитов и медиафайлов,
    если в базе данных еще нет данных. Если данные уже существуют, функция
    прерывает свою работу.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных для выполнения операций.

    """
    # Проверка на наличие данных
    existing_user = await session.execute(select(User))
    if existing_user.scalars().first():
        print("База данных уже содержит данные. Процесс инициализации прерван.")
        return

        # Создаем пользователей
    encrypted_api_key1 = EncryptedType(
        LargeBinary, settings.SECRET_KEY, AesEngine, "pkcs5"
    ).process_bind_param("test", None)
    encrypted_api_key2 = EncryptedType(
        LargeBinary, settings.SECRET_KEY, AesEngine, "pkcs5"
    ).process_bind_param("test_2", None)
    user1 = User(name="test", api_key=encrypted_api_key1)
    user2 = User(name="User2", api_key=encrypted_api_key2)
    session.add(user1)
    session.add(user2)
    await session.commit()

    # Создаем твиты
    tweet1 = Tweet(tweet_data="Hello, World! This is tweet 1", user_id=user1.id)
    tweet2 = Tweet(tweet_data="This is tweet 2", user_id=user2.id)
    tweet3 = Tweet(tweet_data="Another day, another tweet!", user_id=user1.id)
    session.add(tweet1)
    session.add(tweet2)
    session.add(tweet3)
    await session.commit()

    # Читаем и добавляем изображения
    with open("images/image_1.jpg", "rb") as file:
        binary_data_1 = file.read()
        media1 = Media(filename="image1.jpg", file_data=binary_data_1)
        session.add(media1)

    with open("images/image_2.jpg", "rb") as file:
        binary_data_2 = file.read()
        media2 = Media(filename="image2.jpg", file_data=binary_data_2)
        session.add(media2)

    with open("images/image_3.jpg", "rb") as file:
        binary_data_3 = file.read()
        media3 = Media(filename="image3.jpg", file_data=binary_data_3)
        session.add(media3)

    await session.commit()

    # Обновляем твиты с ID медиа
    tweet1.tweet_media_ids = [media1.id]
    tweet2.tweet_media_ids = [media2.id]
    tweet3.tweet_media_ids = [media3.id]
    await session.commit()

    # Добавляем подписчиков
    user1_follow_user2 = followers.insert().values(
        follower_id=user1.id, followed_id=user2.id
    )
    user2_follow_user1 = followers.insert().values(
        follower_id=user2.id, followed_id=user1.id
    )
    # Выполняем запросы на добавление подписчиков
    await session.execute(user1_follow_user2)
    await session.execute(user2_follow_user1)
    await session.commit()

    # Добавляем лайки на твитах
    like1 = likes_table.insert().values(tweet_id=tweet1.id, user_id=user2.id)
    like2 = likes_table.insert().values(tweet_id=tweet2.id, user_id=user1.id)
    like3 = likes_table.insert().values(tweet_id=tweet3.id, user_id=user2.id)
    # Выполняем запросы на добавление лайков
    await session.execute(like1)
    await session.execute(like2)
    await session.execute(like3)
    await session.commit()
    print("Начальные данные успешно созданы.")
