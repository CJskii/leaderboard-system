import pytest
import warnings
from fastapi.testclient import TestClient
from ..main import app
from ..app.database import SessionLocal, engine
from ..app import models

client = TestClient(app)


# Create a test database
@pytest.fixture(scope="module")
def setup_database():
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


# Test user registration
def test_user_registration(setup_database):
    response = client.post(
        "/users/",
        json={"username": "testuser", "password": "testpassword", "email": "testemail"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


# Test user login and token generation
def test_user_login(setup_database):
    # Create the user
    client.post("/users/", json={"username": "testuser", "password": "testpassword"})

    # Log in the user
    response = client.post(
        "/token", data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


# Test accessing a protected route
def test_access_protected_route(setup_database):
    # Create and log in the user
    client.post("/users/", json={"username": "testuser", "password": "testpassword"})
    login_response = client.post(
        "/token", data={"username": "testuser", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]

    # Use the token to access a protected route
    response = client.get("/users/me/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
