import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from main import app, get_db
import respx
from app.models import user as user_model
from urllib.parse import urlparse, parse_qs
from tests.conftest import TestingSessionLocal


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app, follow_redirects=False)


@respx.mock
@pytest.mark.anyio
async def test_github_callback_creates_user(setup_database):
    # Mock the GitHub API calls
    respx.post("https://github.com/login/oauth/access_token").respond(
        200, json={"access_token": "test_token"}
    )
    respx.get("https://api.github.com/user").respond(
        200,
        json={
            "id": 12345,
            "login": "testuser",
            "email": "testuser@example.com",
            "avatar_url": "https://example.com/avatar.jpg",
        },
    )
    respx.get("https://api.github.com/user/emails").respond(
        200, json=[{"email": "testuser@example.com", "primary": True}]
    )

    # 1. Get the state from the initial redirect
    response = client.get("/auth/github")
    assert response.status_code == 302
    redirect_url = response.headers["location"]
    parsed_url = urlparse(redirect_url)
    query_params = parse_qs(parsed_url.query)
    state = query_params["state"][0]

    # 2. Call the callback with the state
    response = client.get(f"/auth/callback?code=test_code&state={state}")
    assert response.status_code == 307  # Redirect status code

    async with TestingSessionLocal() as session:
        result = await session.execute(
            select(user_model.User).filter(user_model.User.github_id == "12345")
        )
        user = result.scalars().first()
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "testuser@example.com"