import pytest


@pytest.mark.asyncio
async def test_get_tweets(async_client):
    response = await async_client.get("/api/tweets/", headers={"api-key": "test"})
    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_invalid_api_key(async_client):
    response = await async_client.get("/api/tweets/", headers={"api-key": "invalid"})
    assert response.status_code == 200
    assert response.json()["result"] == "false"
    assert response.json()["error_type"] == "HTTPException"
    assert response.json()["error_message"] == "Invalid API key"


@pytest.mark.asyncio
async def test_create_tweet(created_tweet_id):
    assert created_tweet_id is not None


@pytest.mark.asyncio
async def test_create_tweet_with_media_ids(async_client):
    tweet_request = {"tweet_data": "Test tweet with media", "tweet_media_ids": [1, 2]}
    response = await async_client.post(
        "/api/tweets/", headers={"api-key": "test"}, json=tweet_request
    )
    assert response.status_code == 200
    assert response.json()["result"] is True
    assert "tweet_id" in response.json()


@pytest.mark.asyncio
async def test_delete_tweet(created_tweet_id, async_client):
    tweet_id = await created_tweet_id
    response = await async_client.delete(
        f"/api/tweets/{tweet_id}", headers={"api-key": "test"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_not_owned_tweet(async_client):
    response = await async_client.delete("/api/tweets/2", headers={"api-key": "test"})
    assert response.status_code == 200
    assert response.json()["result"] == "false"
    assert response.json()["error_type"] == "HTTPException"
    assert (
        response.json()["error_message"] == "You are not allowed to delete this tweet"
    )


@pytest.mark.asyncio
async def test_unlike_tweet(async_client):
    response = await async_client.delete(
        "/api/tweets/2/likes", headers={"api-key": "test"}
    )
    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_like_tweet(async_client):
    response = await async_client.post(
        "/api/tweets/2/likes", headers={"api-key": "test"}
    )
    assert response.status_code == 200
    assert response.json()["result"] is True
