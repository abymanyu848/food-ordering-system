import os
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole

engine = create_engine("sqlite:///./test_commerce.db", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

def override():
    db = Session()
    try: yield db
    finally: db.close()

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def token(client, email, role="customer"):
    client.post("/api/v1/auth/register", json={"full_name": email.split("@")[0], "email": email, "phone": "9876543210", "password": "password123"})
    db=Session(); user=db.query(User).filter_by(email=email).one(); user.role=UserRole.ADMIN if role == "admin" else UserRole.CUSTOMER; db.commit(); db.close()
    return client.post("/api/v1/auth/login", json={"email":email,"password":"password123"}).json()["access_token"]

def test_phase_3_to_7_flow(client):
    admin_token = token(client, 'admin@example.com','admin')
    user_token = token(client, 'user@example.com')
    admin={"Authorization":f"Bearer {admin_token}"}; user={"Authorization":f"Bearer {user_token}"}
    restaurant=client.post("/api/v1/restaurants",headers=admin,json={"name":"Kitchen","description":"Good food","address":"12 Main Street","phone":"9876543210","opening_time":"09:00:00","closing_time":"22:00:00"}).json(); assert restaurant["id"]
    category=client.post("/api/v1/categories",headers=admin,json={"name":"Indian"}).json()
    food=client.post("/api/v1/foods",headers=admin,json={"restaurant_id":restaurant["id"],"category_id":category["id"],"name":"Paneer Curry","description":"Creamy","price":"199.00"}).json()
    assert client.get("/api/v1/foods?search=Paneer&price_asc").status_code == 200
    assert len(client.get("/api/v1/foods",params={"restaurant_id":restaurant["id"],"category_id":category["id"],"available":True}).json()) == 1
    cart=client.post("/api/v1/cart/items",headers=user,json={"food_id":food["id"],"quantity":2}).json(); assert cart["total_price"] == "398.00"
    item=cart["items"][0]; assert client.put(f"/api/v1/cart/items/{item['id']}",headers=user,json={"quantity":3}).status_code == 200
    order=client.post("/api/v1/orders",headers=user,json={"delivery_address":"12 Main Street, City"}).json(); assert order["status"] == "pending"
    assert client.post(f"/api/v1/orders/{order['id']}/cancel",headers=user).json()["status"] == "cancelled"
    review=client.post("/api/v1/reviews",headers=user,json={"restaurant_id":restaurant["id"],"rating":5,"comment":"Great"}).json(); assert review["rating"] == 5
    assert client.put(f"/api/v1/reviews/{review['id']}",headers=user,json={"restaurant_id":restaurant["id"],"rating":4,"comment":"Good"}).json()["rating"] == 4
    assert client.delete(f"/api/v1/reviews/{review['id']}",headers=user).status_code == 204