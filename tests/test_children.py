import pytest


@pytest.mark.asyncio
async def test_create_child(client, auth_headers):
    res = await client.post("/api/v1/children", json={
        "name": "Alice", "display_name": "alice99", "age": 7
    }, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Alice"
    assert data["xp"] == 0
    assert data["level"] == 1


@pytest.mark.asyncio
async def test_list_children(client, auth_headers):
    await client.post("/api/v1/children", json={"name": "Bob", "display_name": "bob1", "age": 5}, headers=auth_headers)
    res = await client.get("/api/v1/children", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert "items" in data


@pytest.mark.asyncio
async def test_get_child(client, auth_headers):
    create = await client.post("/api/v1/children", json={"name": "Carol", "display_name": "carol1", "age": 8}, headers=auth_headers)
    child_id = create.json()["id"]
    res = await client.get(f"/api/v1/children/{child_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Carol"


@pytest.mark.asyncio
async def test_update_child(client, auth_headers):
    create = await client.post("/api/v1/children", json={"name": "Dave", "display_name": "dave1", "age": 6}, headers=auth_headers)
    child_id = create.json()["id"]
    res = await client.put(f"/api/v1/children/{child_id}", json={"name": "David", "age": 7}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "David"
    assert res.json()["age"] == 7


@pytest.mark.asyncio
async def test_delete_child(client, auth_headers):
    create = await client.post("/api/v1/children", json={"name": "Eve", "display_name": "eve1", "age": 4}, headers=auth_headers)
    child_id = create.json()["id"]
    res = await client.delete(f"/api/v1/children/{child_id}", headers=auth_headers)
    assert res.status_code == 204
    get_res = await client.get(f"/api/v1/children/{child_id}", headers=auth_headers)
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_child_not_accessible_by_other_parent(client):
    # Register two parents
    res1 = await client.post("/api/v1/auth/register", json={"email": "p1@x.com", "password": "pass1234!", "full_name": "P1"})
    res2 = await client.post("/api/v1/auth/register", json={"email": "p2@x.com", "password": "pass1234!", "full_name": "P2"})
    h1 = {"Authorization": f"Bearer {res1.json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {res2.json()['access_token']}"}

    child_res = await client.post("/api/v1/children", json={"name": "Kid", "display_name": "kid1", "age": 5}, headers=h1)
    child_id = child_res.json()["id"]

    res = await client.get(f"/api/v1/children/{child_id}", headers=h2)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_child_badges(client, auth_headers):
    create = await client.post("/api/v1/children", json={"name": "Frank", "display_name": "frank1", "age": 9}, headers=auth_headers)
    child_id = create.json()["id"]
    res = await client.get(f"/api/v1/children/{child_id}/badges", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_get_child_progress(client, auth_headers):
    create = await client.post("/api/v1/children", json={"name": "Grace", "display_name": "grace1", "age": 10}, headers=auth_headers)
    child_id = create.json()["id"]
    res = await client.get(f"/api/v1/children/{child_id}/progress", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] == 0
