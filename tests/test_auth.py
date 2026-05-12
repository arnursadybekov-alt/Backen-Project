import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    res = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "strongpass123",
        "full_name": "New User",
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "pass1234", "full_name": "User"}
    await client.post("/api/v1/auth/register", json=payload)
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code in (409, 500)


@pytest.mark.asyncio
async def test_register_short_password(client):
    res = await client.post("/api/v1/auth/register", json={
        "email": "x@x.com", "password": "short", "full_name": "X"
    })
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com", "password": "loginpass1", "full_name": "Login User"
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com", "password": "loginpass1"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "wp@example.com", "password": "correctpass", "full_name": "WP"
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": "wp@example.com", "password": "wrongpass1"
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent(client):
    res = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com", "password": "nopass1234"
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com", "password": "refreshpass", "full_name": "Refresh"
    })
    refresh_token = reg.json()["refresh_token"]
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_logout(client, auth_headers):
    res = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_protected_route_no_token(client):
    res = await client.get("/api/v1/children")
    assert res.status_code == 403
