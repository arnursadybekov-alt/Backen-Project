import pytest


async def create_unit(client, admin_headers, title="Test Unit"):
    res = await client.post("/api/v1/units", json={
        "title": title, "description": "A test unit",
        "order_index": 1, "difficulty": "beginner", "is_published": True
    }, headers=admin_headers)
    return res.json()


async def create_lesson(client, admin_headers, unit_id, title="Test Lesson", published=True):
    res = await client.post("/api/v1/lessons", json={
        "unit_id": unit_id, "title": title,
        "order_index": 1, "difficulty": "beginner",
        "is_published": published, "xp_reward": 50,
    }, headers=admin_headers)
    return res.json()


async def create_exercise(client, admin_headers, lesson_id):
    res = await client.post(f"/api/v1/lessons/{lesson_id}/exercises", json={
        "exercise_type": "phonics",
        "question": "What sound does 'A' make?",
        "correct_answer": "ah",
        "options": ["ah", "eh", "oh", "uh"],
        "order_index": 1,
    }, headers=admin_headers)
    return res.json()


# ── Units ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_unit_as_admin(client, admin_headers):
    res = await client.post("/api/v1/units", json={
        "title": "Phonics Level 1", "order_index": 1, "difficulty": "beginner", "is_published": True
    }, headers=admin_headers)
    assert res.status_code == 201
    assert res.json()["title"] == "Phonics Level 1"


@pytest.mark.asyncio
async def test_create_unit_as_parent_forbidden(client, auth_headers):
    res = await client.post("/api/v1/units", json={
        "title": "Unauthorized", "order_index": 1, "difficulty": "beginner"
    }, headers=auth_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_list_units(client, auth_headers, admin_headers):
    await create_unit(client, admin_headers, "Unit A")
    res = await client.get("/api/v1/units", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1


@pytest.mark.asyncio
async def test_update_unit(client, admin_headers):
    unit = await create_unit(client, admin_headers)
    res = await client.put(f"/api/v1/units/{unit['id']}", json={"title": "Updated Unit"}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Unit"


@pytest.mark.asyncio
async def test_delete_unit(client, admin_headers):
    unit = await create_unit(client, admin_headers)
    res = await client.delete(f"/api/v1/units/{unit['id']}", headers=admin_headers)
    assert res.status_code == 204


# ── Lessons ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_lesson(client, admin_headers):
    unit = await create_unit(client, admin_headers)
    res = await client.post("/api/v1/lessons", json={
        "unit_id": unit["id"], "title": "Letter A", "order_index": 1,
        "difficulty": "beginner", "is_published": True, "xp_reward": 50,
    }, headers=admin_headers)
    assert res.status_code == 201
    assert res.json()["title"] == "Letter A"


@pytest.mark.asyncio
async def test_list_lessons_filtered(client, auth_headers, admin_headers):
    unit = await create_unit(client, admin_headers)
    await create_lesson(client, admin_headers, unit["id"], "Lesson 1")
    await create_lesson(client, admin_headers, unit["id"], "Lesson 2", published=False)
    res = await client.get(f"/api/v1/lessons?unit_id={unit['id']}&is_published=true", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1


# ── Exercises ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_exercise(client, admin_headers):
    unit = await create_unit(client, admin_headers)
    lesson = await create_lesson(client, admin_headers, unit["id"])
    ex = await create_exercise(client, admin_headers, lesson["id"])
    assert ex["exercise_type"] == "phonics"
    assert ex["correct_answer"] == "ah"


@pytest.mark.asyncio
async def test_get_lesson_exercises(client, auth_headers, admin_headers):
    unit = await create_unit(client, admin_headers)
    lesson = await create_lesson(client, admin_headers, unit["id"])
    await create_exercise(client, admin_headers, lesson["id"])
    res = await client.get(f"/api/v1/lessons/{lesson['id']}/exercises", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1


# ── Progress ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_exercise_correct(client, auth_headers, admin_headers):
    unit = await create_unit(client, admin_headers)
    lesson = await create_lesson(client, admin_headers, unit["id"])
    ex = await create_exercise(client, admin_headers, lesson["id"])

    child_res = await client.post("/api/v1/children", json={"name": "Kid", "display_name": "kid1", "age": 6}, headers=auth_headers)
    child_id = child_res.json()["id"]

    res = await client.post(f"/api/v1/exercises/{ex['id']}/submit", json={
        "child_id": child_id, "answer": "ah", "time_taken_seconds": 5
    }, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["is_correct"] is True


@pytest.mark.asyncio
async def test_submit_exercise_incorrect(client, auth_headers, admin_headers):
    unit = await create_unit(client, admin_headers)
    lesson = await create_lesson(client, admin_headers, unit["id"])
    ex = await create_exercise(client, admin_headers, lesson["id"])

    child_res = await client.post("/api/v1/children", json={"name": "Kid2", "display_name": "kid2", "age": 7}, headers=auth_headers)
    child_id = child_res.json()["id"]

    res = await client.post(f"/api/v1/exercises/{ex['id']}/submit", json={
        "child_id": child_id, "answer": "wrong_answer"
    }, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["is_correct"] is False


@pytest.mark.asyncio
async def test_complete_lesson(client, auth_headers, admin_headers):
    unit = await create_unit(client, admin_headers)
    lesson = await create_lesson(client, admin_headers, unit["id"])

    child_res = await client.post("/api/v1/children", json={"name": "Learner", "display_name": "learner1", "age": 8}, headers=auth_headers)
    child_id = child_res.json()["id"]

    res = await client.post(f"/api/v1/lessons/{lesson['id']}/complete", json={"child_id": child_id}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["xp_earned"] > 0
    assert "new_badges" in data
    assert "streak" in data


@pytest.mark.asyncio
async def test_complete_lesson_awards_first_lesson_badge(client, auth_headers, admin_headers):
    unit = await create_unit(client, admin_headers)
    lesson = await create_lesson(client, admin_headers, unit["id"])

    child_res = await client.post("/api/v1/children", json={"name": "Badge Kid", "display_name": "badgekid", "age": 6}, headers=auth_headers)
    child_id = child_res.json()["id"]

    complete_res = await client.post(f"/api/v1/lessons/{lesson['id']}/complete", json={"child_id": child_id}, headers=auth_headers)
    new_badges = complete_res.json()["new_badges"]
    assert "first_lesson" in new_badges

    badges_res = await client.get(f"/api/v1/children/{child_id}/badges", headers=auth_headers)
    assert any(b["badge_type"] == "first_lesson" for b in badges_res.json())


@pytest.mark.asyncio
async def test_complete_unpublished_lesson_forbidden(client, auth_headers, admin_headers):
    unit = await create_unit(client, admin_headers)
    lesson = await create_lesson(client, admin_headers, unit["id"], published=False)

    child_res = await client.post("/api/v1/children", json={"name": "Kid3", "display_name": "kid3", "age": 5}, headers=auth_headers)
    child_id = child_res.json()["id"]

    res = await client.post(f"/api/v1/lessons/{lesson['id']}/complete", json={"child_id": child_id}, headers=auth_headers)
    assert res.status_code == 403
