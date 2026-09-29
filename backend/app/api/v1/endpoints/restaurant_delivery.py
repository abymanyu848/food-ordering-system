from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Category, DeliveryPerson, Food, Order, Restaurant, Review
from app.models.commerce import OrderStatus, DeliveryStatus
from app.models.user import User, UserRole
from app.schemas.commerce import (RestaurantOut, FoodOut, OrderOut, RestaurantIn, OrderStatusUpdate, FoodInRestaurant)
from app.schemas.user import *
from app.security import (
    get_current_active_admin, get_current_active_restaurant,
    get_current_active_delivery_person, get_current_restaurant_or_admin
)

router = APIRouter()

def one(db, model, value):
    result = db.get(model, value)
    if not result: raise HTTPException(404, f"{model.__name__} not found")
    return result

def commit(db, obj): db.add(obj); db.commit(); db.refresh(obj); return obj

def admin(_: User = Depends(get_current_active_admin)): return _
def restaurant_user(_: User = Depends(get_current_active_restaurant)): return _
def delivery_person_user(_: User = Depends(get_current_active_delivery_person)): return _
def restaurant_or_admin(_: User = Depends(get_current_restaurant_or_admin)): return _

def refresh_restaurant_rating(db, restaurant_id: int | None):
    if restaurant_id:
        restaurant = db.get(Restaurant, restaurant_id)
        restaurant.rating = float(db.query(func.avg(Review.rating)).filter(Review.restaurant_id == restaurant_id).scalar() or 0)
        db.commit()

# ============ Restaurant Dashboard Endpoints ============

@router.get("/restaurant/me", response_model=RestaurantOut)
def get_my_restaurant(current_user: User = Depends(get_current_active_restaurant), db: Session = Depends(get_db)):
    """Get the restaurant associated with the current restaurant user"""
    if not current_user.restaurant_id:
        raise HTTPException(404, "No restaurant linked to this account")
    return one(db, Restaurant, current_user.restaurant_id)

@router.put("/restaurant/me", response_model=RestaurantOut)
def update_my_restaurant(
    body: RestaurantIn,
    current_user: User = Depends(get_current_active_restaurant),
    db: Session = Depends(get_db)
):
    """Update basic restaurant information (restaurant owner only)"""
    if not current_user.restaurant_id:
        raise HTTPException(404, "No restaurant linked to this account")
    obj = one(db, Restaurant, current_user.restaurant_id)
    for key, value in body.model_dump().items():
        setattr(obj, key, value)
    return commit(db, obj)

@router.get("/restaurant/foods", response_model=list[FoodOut])
def get_my_foods(current_user: User = Depends(get_current_active_restaurant), db: Session = Depends(get_db)):
    """Get all foods for the current restaurant"""
    if not current_user.restaurant_id:
        raise HTTPException(404, "No restaurant linked to this account")
    return db.query(Food).filter(Food.restaurant_id == current_user.restaurant_id).all()

@router.post("/restaurant/foods", response_model=FoodOut, status_code=201)
def create_my_food(
    body: FoodInRestaurant,
    current_user: User = Depends(get_current_active_restaurant),
    db: Session = Depends(get_db)
):
    """Add a new food item to the restaurant's menu"""
    if not current_user.restaurant_id:
        raise HTTPException(404, "No restaurant linked to this account")
    # Override restaurant_id to ensure it belongs to this restaurant
    food_data = body.model_dump(); food_data["restaurant_id"] = current_user.restaurant_id
    one(db, Restaurant, current_user.restaurant_id)
    one(db, Category, food_data["category_id"])
    return commit(db, Food(**food_data))

@router.put("/restaurant/foods/{food_id}", response_model=FoodOut)
def update_my_food(
    food_id: int,
    body: FoodInRestaurant,
    current_user: User = Depends(get_current_active_restaurant),
    db: Session = Depends(get_db)
):
    """Update a food item in the restaurant's menu"""
    if not current_user.restaurant_id:
        raise HTTPException(404, "No restaurant linked to this account")
    obj = one(db, Food, food_id)
    if obj.restaurant_id != current_user.restaurant_id:
        raise HTTPException(403, "Not allowed to modify this food item")
    food_data = body.model_dump(); food_data["restaurant_id"] = current_user.restaurant_id
    one(db, Category, body.category_id)
    for key, value in body.model_dump().items():
        setattr(obj, key, value)
    return commit(db, obj)

@router.delete("/restaurant/foods/{food_id}", status_code=204)
def delete_my_food(
    food_id: int,
    current_user: User = Depends(get_current_active_restaurant),
    db: Session = Depends(get_db)
):
    """Delete a food item from the restaurant's menu"""
    if not current_user.restaurant_id:
        raise HTTPException(404, "No restaurant linked to this account")
    obj = one(db, Food, food_id)
    if obj.restaurant_id != current_user.restaurant_id:
        raise HTTPException(403, "Not allowed to delete this food item")
    db.delete(obj)
    db.commit()

@router.get("/restaurant/orders", response_model=list[OrderOut])
def get_my_restaurant_orders(
    status_filter: OrderStatus | None = Query(None),
    current_user: User = Depends(get_current_active_restaurant),
    db: Session = Depends(get_db)
):
    """Get all orders for the current restaurant"""
    if not current_user.restaurant_id:
        raise HTTPException(404, "No restaurant linked to this account")
    q = db.query(Order).filter(Order.restaurant_id == current_user.restaurant_id)
    if status_filter:
        q = q.filter(Order.status == status_filter)
    return q.order_by(desc(Order.created_at)).all()

@router.get("/restaurant/orders/{order_id}", response_model=OrderOut)
def get_my_restaurant_order(
    order_id: int,
    current_user: User = Depends(get_current_active_restaurant),
    db: Session = Depends(get_db)
):
    """Get a specific order for the current restaurant"""
    if not current_user.restaurant_id:
        raise HTTPException(404, "No restaurant linked to this account")
    obj = one(db, Order, order_id)
    if obj.restaurant_id != current_user.restaurant_id:
        raise HTTPException(403, "Not allowed to view this order")
    return obj

@router.patch("/restaurant/orders/{order_id}/status", response_model=OrderOut)
def update_my_restaurant_order_status(
    order_id: int,
    body: OrderStatusUpdate,
    current_user: User = Depends(get_current_active_restaurant),
    db: Session = Depends(get_db)
):
    """Update order status (PENDING -> ACCEPTED -> PREPARING -> READY)"""
    if not current_user.restaurant_id:
        raise HTTPException(404, "No restaurant linked to this account")
    obj = one(db, Order, order_id)
    if obj.restaurant_id != current_user.restaurant_id:
        raise HTTPException(403, "Not allowed to modify this order")
    
    # Validate status transition
    valid_transitions = {
        OrderStatus.PENDING: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
        OrderStatus.ACCEPTED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
        OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
        OrderStatus.READY: [OrderStatus.ASSIGNED, OrderStatus.CANCELLED],
    }
    if obj.status not in valid_transitions or body.status not in valid_transitions[obj.status]:
        raise HTTPException(400, f"Invalid status transition from {obj.status} to {body.status}")
    
    obj.status = body.status
    if body.status == OrderStatus.ACCEPTED:
        obj.assigned_at = func.now()
    elif body.status == OrderStatus.DELIVERED:
        obj.delivered_at = func.now()
    elif body.status == OrderStatus.CANCELLED:
        obj.delivered_at = func.now()
    return commit(db, obj)

@router.post("/restaurant/uploads/foods", dependencies=[Depends(get_current_active_restaurant)])
def upload_food_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_active_restaurant)
):
    """Upload food image for restaurant's menu"""
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Use JPG, PNG, or WEBP images")
    target = Path(__file__).resolve().parents[4] / "uploads" / "foods"
    target.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{Path(image.filename or '').suffix.lower()}"
    destination = target / filename
    with destination.open("wb") as output:
        output.write(image.file.read())
    return {"url": f"/uploads/foods/{filename}"}

# ============ Delivery Person Dashboard Endpoints ============

@router.get("/delivery/me", response_model=DeliveryPersonOut)
def get_my_delivery_profile(
    current_user: User = Depends(get_current_active_delivery_person),
    db: Session = Depends(get_db)
):
    """Get the delivery person profile"""
    dp = db.query(DeliveryPerson).filter(DeliveryPerson.user_id == current_user.id).first()
    if not dp:
        raise HTTPException(404, "Delivery person profile not found")
    return dp

@router.put("/delivery/me", response_model=DeliveryPersonOut)
def update_my_delivery_profile(
    body: DeliveryPersonUpdate,
    current_user: User = Depends(get_current_active_delivery_person),
    db: Session = Depends(get_db)
):
    """Update delivery person profile"""
    dp = db.query(DeliveryPerson).filter(DeliveryPerson.user_id == current_user.id).first()
    if not dp:
        raise HTTPException(404, "Delivery person profile not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(dp, key, value)
    return commit(db, dp)

@router.get("/delivery/orders", response_model=list[OrderOut])
def get_my_delivery_orders(
    status_filter: DeliveryStatus | None = Query(None),
    current_user: User = Depends(get_current_active_delivery_person),
    db: Session = Depends(get_db)
):
    """Get orders assigned to the delivery person"""
    dp = db.query(DeliveryPerson).filter(DeliveryPerson.user_id == current_user.id).first()
    if not dp:
        raise HTTPException(404, "Delivery person profile not found")
    q = db.query(Order).filter(Order.delivery_person_id == dp.id)
    if status_filter:
        q = q.filter(Order.delivery_status == status_filter)
    return q.order_by(desc(Order.created_at)).all()

@router.get("/delivery/orders/available", response_model=list[OrderOut])
def get_available_delivery_orders(
    current_user: User = Depends(get_current_active_delivery_person),
    db: Session = Depends(get_db)
):
    """Get orders ready for delivery assignment (for available delivery persons)"""
    dp = db.query(DeliveryPerson).filter(DeliveryPerson.user_id == current_user.id).first()
    if not dp:
        raise HTTPException(404, "Delivery person profile not found")
    if not dp.is_available:
        raise HTTPException(400, "You are not currently available for deliveries")
    # Orders that are READY and not yet assigned
    return db.query(Order).filter(
        Order.status == OrderStatus.READY,
        Order.delivery_person_id == None
    ).order_by(Order.created_at).all()

@router.get("/delivery/orders/{order_id}", response_model=OrderOut)
def get_my_delivery_order(
    order_id: int,
    current_user: User = Depends(get_current_active_delivery_person),
    db: Session = Depends(get_db)
):
    """Get a specific order assigned to the delivery person"""
    dp = db.query(DeliveryPerson).filter(DeliveryPerson.user_id == current_user.id).first()
    if not dp:
        raise HTTPException(404, "Delivery person profile not found")
    obj = one(db, Order, order_id)
    if obj.delivery_person_id != dp.id:
        raise HTTPException(403, "Not allowed to view this order")
    return obj

@router.post("/delivery/orders/{order_id}/accept", response_model=OrderOut)
def accept_delivery_order(
    order_id: int,
    current_user: User = Depends(get_current_active_delivery_person),
    db: Session = Depends(get_db)
):
    """Accept a delivery assignment (ASSIGNED -> ACCEPTED)"""
    dp = db.query(DeliveryPerson).filter(DeliveryPerson.user_id == current_user.id).first()
    if not dp:
        raise HTTPException(404, "Delivery person profile not found")
    obj = one(db, Order, order_id)
    if obj.delivery_person_id != dp.id:
        raise HTTPException(403, "Not allowed to accept this order")
    if obj.delivery_status != DeliveryStatus.ASSIGNED:
        raise HTTPException(400, "Order is not in ASSIGNED status")
    obj.delivery_status = DeliveryStatus.ACCEPTED
    return commit(db, obj)

@router.post("/delivery/orders/{order_id}/pickup", response_model=OrderOut)
def pickup_delivery_order(
    order_id: int,
    current_user: User = Depends(get_current_active_delivery_person),
    db: Session = Depends(get_db)
):
    """Mark order as picked up from restaurant (ACCEPTED -> PICKED_UP)"""
    dp = db.query(DeliveryPerson).filter(DeliveryPerson.user_id == current_user.id).first()
    if not dp:
        raise HTTPException(404, "Delivery person profile not found")
    obj = one(db, Order, order_id)
    if obj.delivery_person_id != dp.id:
        raise HTTPException(403, "Not allowed to pickup this order")
    if obj.delivery_status != DeliveryStatus.ACCEPTED:
        raise HTTPException(400, "Order must be ACCEPTED before pickup")
    obj.delivery_status = DeliveryStatus.PICKED_UP
    obj.picked_up_at = func.now()
    obj.status = OrderStatus.OUT_FOR_DELIVERY
    return commit(db, obj)

@router.post("/delivery/orders/{order_id}/out-for-delivery", response_model=OrderOut)
def out_for_delivery(
    order_id: int,
    current_user: User = Depends(get_current_active_delivery_person),
    db: Session = Depends(get_db)
):
    """Mark order as out for delivery (PICKED_UP -> OUT_FOR_DELIVERY)"""
    dp = db.query(DeliveryPerson).filter(DeliveryPerson.user_id == current_user.id).first()
    if not dp:
        raise HTTPException(404, "Delivery person profile not found")
    obj = one(db, Order, order_id)
    if obj.delivery_person_id != dp.id:
        raise HTTPException(403, "Not allowed")
    if obj.delivery_status != DeliveryStatus.PICKED_UP:
        raise HTTPException(400, "Order must be PICKED_UP before out for delivery")
    obj.delivery_status = DeliveryStatus.OUT_FOR_DELIVERY
    return commit(db, obj)

@router.post("/delivery/orders/{order_id}/delivered", response_model=OrderOut)
def mark_delivered(
    order_id: int,
    current_user: User = Depends(get_current_active_delivery_person),
    db: Session = Depends(get_db)
):
    """Mark order as delivered (OUT_FOR_DELIVERY -> DELIVERED)"""
    dp = db.query(DeliveryPerson).filter(DeliveryPerson.user_id == current_user.id).first()
    if not dp:
        raise HTTPException(404, "Delivery person profile not found")
    obj = one(db, Order, order_id)
    if obj.delivery_person_id != dp.id:
        raise HTTPException(403, "Not allowed")
    if obj.delivery_status != DeliveryStatus.OUT_FOR_DELIVERY:
        raise HTTPException(400, "Order must be OUT_FOR_DELIVERY before marking delivered")
    obj.delivery_status = DeliveryStatus.DELIVERED
    obj.status = OrderStatus.DELIVERED
    obj.delivered_at = func.now()
    return commit(db, obj)

# ============ Admin Delivery Management Endpoints ============

@router.get("/admin/delivery-persons", response_model=list[DeliveryPersonOut], dependencies=[Depends(admin)])
def admin_get_delivery_persons(db: Session = Depends(get_db)):
    """Get all delivery persons"""
    return db.query(DeliveryPerson).order_by(DeliveryPerson.id).all()

@router.post("/admin/delivery-persons", response_model=DeliveryPersonOut, status_code=201, dependencies=[Depends(admin)])
def admin_create_delivery_person(
    body: DeliveryPersonCreate,
    db: Session = Depends(get_db)
):
    """Create a new delivery person account"""
    # Check if user exists and is a delivery person
    user = db.query(User).filter(User.id == body.user_id, User.role == UserRole.DELIVERY_PERSON).first()
    if not user:
        raise HTTPException(404, "User not found or not a delivery person")
    # Check if delivery person profile already exists
    existing = db.query(DeliveryPerson).filter(DeliveryPerson.user_id == body.user_id).first()
    if existing:
        raise HTTPException(409, "Delivery person profile already exists")
    dp = DeliveryPerson(**body.model_dump())
    return commit(db, dp)

@router.put("/admin/delivery-persons/{dp_id}", response_model=DeliveryPersonOut, dependencies=[Depends(admin)])
def admin_update_delivery_person(
    dp_id: int,
    body: DeliveryPersonUpdate,
    db: Session = Depends(get_db)
):
    """Update delivery person"""
    dp = one(db, DeliveryPerson, dp_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(dp, key, value)
    return commit(db, dp)

@router.delete("/admin/delivery-persons/{dp_id}", status_code=204, dependencies=[Depends(admin)])
def admin_delete_delivery_person(dp_id: int, db: Session = Depends(get_db)):
    """Delete delivery person"""
    db.delete(one(db, DeliveryPerson, dp_id))
    db.commit()

@router.patch("/admin/orders/{order_id}/assign-delivery", response_model=OrderOut, dependencies=[Depends(admin)])
def admin_assign_delivery_person(
    order_id: int,
    body: AssignDeliveryPerson,
    db: Session = Depends(get_db)
):
    """Assign a delivery person to an order"""
    obj = one(db, Order, order_id)
    if obj.status != OrderStatus.READY:
        raise HTTPException(400, "Order must be READY to assign delivery person")
    if obj.delivery_person_id:
        raise HTTPException(400, "Order already has a delivery person assigned")
    dp = one(db, DeliveryPerson, body.delivery_person_id)
    if not dp.is_available:
        raise HTTPException(400, "Delivery person is not available")
    obj.delivery_person_id = dp.id
    obj.delivery_status = DeliveryStatus.ASSIGNED
    obj.assigned_at = func.now()
    obj.status = OrderStatus.ASSIGNED
    return commit(db, obj)

@router.patch("/admin/orders/{order_id}/reassign-delivery", response_model=OrderOut, dependencies=[Depends(admin)])
def admin_reassign_delivery_person(
    order_id: int,
    body: AssignDeliveryPerson,
    db: Session = Depends(get_db)
):
    """Reassign a delivery person to an order"""
    obj = one(db, Order, order_id)
    if obj.status not in [OrderStatus.ASSIGNED, OrderStatus.ACCEPTED]:
        raise HTTPException(400, "Can only reassign orders in ASSIGNED or ACCEPTED status")
    dp = one(db, DeliveryPerson, body.delivery_person_id)
    if not dp.is_available:
        raise HTTPException(400, "Delivery person is not available")
    obj.delivery_person_id = dp.id
    obj.delivery_status = DeliveryStatus.ASSIGNED
    obj.assigned_at = func.now()
    obj.status = OrderStatus.ASSIGNED
    return commit(db, obj)
