import os
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


engine = create_engine("sqlite:///./test_auth.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # Reset dependency override for this test module
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_register_login_and_profile(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Test Student", "email": "student@example.com", "phone": "9876543210", "password": "password123"},
    )
    assert registration.status_code == 201
    assert registration.json()["role"] == "customer"
    assert "password_hash" not in registration.json()

    duplicate = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Test Student", "email": "student@example.com", "phone": "9876543210", "password": "password123"},
    )
    assert duplicate.status_code == 409

    incorrect = client.post("/api/v1/auth/login", json={"email": "student@example.com", "password": "wrongpass"})
    assert incorrect.status_code == 401

    login = client.post("/api/v1/auth/login", json={"email": "student@example.com", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert login.json()["token_type"] == "bearer"

    protected = client.get("/api/v1/users/me")
    assert protected.status_code == 401
    profile = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == "student@example.com"

    from app.models.user import User
    from app.security import verify_password
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter_by(email="student@example.com").one()
        # Passwords must be bcrypt hashes, never stored as plain text.
        assert user.password_hash != "password123"
        assert user.password_hash.startswith(("$2a$", "$2b$", "$2y$"))
        assert verify_password("password123", user.password_hash)
    finally:
        db.close()