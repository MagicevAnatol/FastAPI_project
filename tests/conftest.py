import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app
from schemas.schemas import TweetCreateRequest


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def created_tweet_id():
    tweet_request = TweetCreateRequest(tweet_data="Test tweet", tweet_media_ids=[])
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/tweets/", headers={"api-key": "test"}, json=tweet_request.dict()
        )
    return response.json()["tweet_id"]


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
