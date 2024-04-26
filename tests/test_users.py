import pytest


@pytest.mark.asyncio
async def test_get_current_user(async_client):
    response = await async_client.get("/api/users/me", headers={"api-key": "test"})
    assert response.status_code == 200
    assert response.json()["result"] is True
    assert "user" in response.json()


@pytest.mark.asyncio
async def test_get_user_profile(async_client):
    response = await async_client.get("/api/users/1")
    assert response.status_code == 200
    assert response.json()["result"] is True
    assert "user" in response.json()


@pytest.mark.asyncio
async def test_get_user_profile_not_found(async_client):
    response = await async_client.get("/api/users/999")
    assert response.status_code == 200
    assert response.json()["result"] is False


@pytest.mark.asyncio
async def test_unfollow_user(async_client):
    response = await async_client.delete(
        "/api/users/2/follow", headers={"api-key": "test"}
    )
    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_follow_user(async_client):
    response = await async_client.post(
        "/api/users/2/follow", headers={"api-key": "test"}
    )
    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_unfollow_already_unfollowed_user(async_client):
    response = await async_client.delete(
        "/api/users/3/follow", headers={"api-key": "test"}
    )
    assert response.status_code == 200
    assert response.json()["result"] is False
