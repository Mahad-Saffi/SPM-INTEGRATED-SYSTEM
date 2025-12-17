import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import jwt
from datetime import datetime, timedelta
from sqlalchemy import select

from main import app, get_db, config
from tests.conftest import TestingSessionLocal
from app.models.project import Project
from app.models.task import Task


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def authenticated_user_token():
    jwt_payload = {
        "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "username": "testuser",
        "email": "test@test.com",
        "role": "developer",
        "avatar_url": "",
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    secret_key = config('JWT_SECRET_KEY')
    token = jwt.encode(jwt_payload, secret_key, algorithm="HS256")
    return token

@patch("app.services.ai_service.ai_service._get_formatted_users", new_callable=AsyncMock)
@pytest.mark.anyio
async def test_discover_endpoint_team_suggestion(mock_get_formatted_users, authenticated_user_token, setup_database):
    from app.services.ai_service import ai_service
    ai_service.conversation_state = "TEAM_SUGGESTION"
    ai_service.conversation = AsyncMock()
    ai_service.conversation.predict.return_value = "This is a mock AI response."
    mock_get_formatted_users.return_value = "- testuser1 (Role: developer)\n- testuser2 (Role: designer)"

    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    payload = {"message": "Hello AI"}

    response = client.post("/api/v1/ai/discover", headers=headers, json=payload)

    assert response.status_code == 200
    assert response.json() == {"sender": "ai", "text": "This is a mock AI response."}
    mock_get_formatted_users.assert_called_once()
    ai_service.conversation.predict.assert_called_once_with(input="Hello AI", formatted_users="- testuser1 (Role: developer)\n- testuser2 (Role: designer)")

@patch("app.services.project_service.project_service.create_project_from_plan", new_callable=AsyncMock)
@pytest.mark.anyio
async def test_discover_endpoint_plan_generation(mock_create_project, authenticated_user_token, setup_database):
    from app.services.ai_service import ai_service
    ai_service.conversation_state = "PLAN_GENERATION"
    # Create a fresh AsyncMock conversation with a predictable `predict` coroutine
    ai_service.conversation = AsyncMock()
    
    mock_plan = {
        "project_name": "Test Project",
        "epics": [{
            "name": "Test Epic",
            "stories": [{
                "name": "Test Story",
                "tasks": ["Test Task"]
            }]
        }]
    }
    # The patched conversation.predict will return a properly formatted JSON string.
    ai_service.conversation.predict.return_value = json.dumps(mock_plan)
    
    # Save a reference to the mock conversation before it's reset
    mock_conversation = ai_service.conversation

    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    payload = {"message": "Here are the details..."}

    response = client.post("/api/v1/ai/discover", headers=headers, json=payload)

    assert response.status_code == 200
    assert response.json() == {"sender": "ai", "text": "Project created successfully!"}
    mock_conversation.predict.assert_called_once_with(input="Here are the details...")
    mock_create_project.assert_called_once_with(mock_plan, "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")

@pytest.mark.anyio
async def test_discover_endpoint_plan_generation_and_save_to_db(authenticated_user_token, setup_database):
    from app.services.ai_service import ai_service
    ai_service.conversation_state = "PLAN_GENERATION"
    ai_service.conversation = AsyncMock()
    mock_plan = {
        "project_name": "Test Project",
        "epics": [{
            "name": "Test Epic",
            "stories": [{
                "name": "Test Story",
                "tasks": ["Test Task"]
            }]
        }]
    }
    ai_service.conversation.predict.return_value = json.dumps(mock_plan)

    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    payload = {"message": "Here are the details..."}

    response = client.post("/api/v1/ai/discover", headers=headers, json=payload)

    assert response.status_code == 200
    assert response.json() == {"sender": "ai", "text": "Project created successfully!"}

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Project).where(Project.name == "Test Project"))
        project = result.scalars().first()
        assert project is not None

        result = await session.execute(select(Task).where(Task.project_id == project.id))
        tasks = result.scalars().all()
        assert len(tasks) == 1
        assert tasks[0].title == "Test Task"
