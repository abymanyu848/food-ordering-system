from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Cart, CartItem, Category, Food, Order, OrderItem, Restaurant, Review
from app.models.commerce import OrderStatus
from app.models.user import User, UserRole
from app.schemas.commerce import *
from app.schemas.user import UserResponse
from app.security import get_current_active_admin, get_current_active_user

router = APIRouter()
def one(db, model, value):
    result = db.get(model, value)
    if not result: raise HTTPException(404, f"{model.__name__} not found")
    return result
def commit(db, obj): db.add(obj); db.commit(); db.refresh(obj); return obj
def admin(_: User = Depends(get_current_active_admin)): return _
def refresh_restaurant_rating(db, restaurant_id: int | None):
    if restaurant_id:
        restaurant = db.get(Restaurant, restaurant_id)
        restaurant.rating = float(db.query(func.avg(Review.rating)).filter(Review.restaurant_id == restaurant_id).scalar() or 0)
        db.commit()

@router.get("/restaurants", response_model=list[RestaurantOut])
def restaurants(db: Session = Depends(get_db)): return db.query(Restaurant).filter(Restaurant.is_active.is_(True)).all()
@router.get("/restaurants/{restaurant_id}", response_model=RestaurantOut)
def restaurant(restaurant_id: int, db: Session = Depends(get_db)): return one(db, Restaurant, restaurant_id)
@router.post("/restaurants", response_model=RestaurantOut, status_code=201, dependencies=[Depends(admin)])
def create_restaurant(body: RestaurantIn, db: Session = Depends(get_db)): return commit(db, Restaurant(**body.model_dump()))
@router.put("/restaurants/{restaurant_id}", response_model=RestaurantOut, dependencies=[Depends(admin)])
def update_restaurant(restaurant_id: int, body: RestaurantIn, db: Session = Depends(get_db)):
    obj = one(db, Restaurant, restaurant_id)
    for key, value in body.model_dump().items(): setattr(obj, key, value)
    return commit(db, obj)
@router.delete("/restaurants/{restaurant_id}", status_code=204, dependencies=[Depends(admin)])
def delete_restaurant(restaurant_id: int, db: Session = Depends(get_db)): db.delete(one(db, Restaurant, restaurant_id)); db.commit()
@router.get("/admin/restaurants", response_model=list[RestaurantOut], dependencies=[Depends(admin)])
def admin_restaurants(db: Session = Depends(get_db)): return db.query(Restaurant).order_by(Restaurant.name).all()

@router.get("/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)): return db.query(Category).order_by(Category.name).all()
@router.post("/categories", response_model=CategoryOut, status_code=201, dependencies=[Depends(admin)])
def create_category(body: CategoryIn, db: Session = Depends(get_db)):
    if db.query(Category).filter(func.lower(Category.name) == body.name.lower()).first(): raise HTTPException(409, "Category already exists")
    return commit(db, Category(**body.model_dump()))
@router.put("/categories/{category_id}", response_model=CategoryOut, dependencies=[Depends(admin)])
def update_category(category_id: int, body: CategoryIn, db: Session = Depends(get_db)):
    obj = one(db, Category, category_id); obj.name = body.name; return commit(db, obj)
@router.delete("/categories/{category_id}", status_code=204, dependencies=[Depends(admin)])
def delete_category(category_id: int, db: Session = Depends(get_db)): db.delete(one(db, Category, category_id)); db.commit()

@router.get("/foods", response_model=list[FoodOut])
def foods(search: str | None = None, restaurant_id: int | None = None, category_id: int | None = None, min_price: Decimal | None = Query(None, ge=0), max_price: Decimal | None = Query(None, ge=0), available: bool | None = None, sort: str = "name", db: Session = Depends(get_db)):
    q = db.query(Food)
    if search: q = q.filter(Food.name.ilike(f"%{search.strip()}%"))
    if restaurant_id: q = q.filter(Food.restaurant_id == restaurant_id)
    if category_id: q = q.filter(Food.category_id == category_id)
    if min_price is not None: q = q.filter(Food.price >= min_price)
    if max_price is not None: q = q.filter(Food.price <= max_price)
    if available is not None: q = q.filter(Food.is_available == available)
    sorts = {"price_asc": asc(Food.price), "price_desc": desc(Food.price), "name": asc(Food.name)}
    return q.order_by(sorts.get(sort, asc(Food.name))).all()
@router.get("/foods/{food_id}", response_model=FoodOut)
def food(food_id: int, db: Session = Depends(get_db)): return one(db, Food, food_id)
@router.post("/foods", response_model=FoodOut, status_code=201, dependencies=[Depends(admin)])
def create_food(body: FoodIn, db: Session = Depends(get_db)):
    one(db, Restaurant, body.restaurant_id); one(db, Category, body.category_id); return commit(db, Food(**body.model_dump()))
@router.put("/foods/{food_id}", response_model=FoodOut, dependencies=[Depends(admin)])
def update_food(food_id: int, body: FoodIn, db: Session = Depends(get_db)):
    obj = one(db, Food, food_id); one(db, Restaurant, body.restaurant_id); one(db, Category, body.category_id)
    for key, value in body.model_dump().items(): setattr(obj, key, value)
    return commit(db, obj)
@router.delete("/foods/{food_id}", status_code=204, dependencies=[Depends(admin)])
def delete_food(food_id: int, db: Session = Depends(get_db)): db.delete(one(db, Food, food_id)); db.commit()

@router.post("/uploads/{kind}", dependencies=[Depends(admin)])
def upload(kind: str, image: UploadFile = File(...)):
    if kind not in {"restaurants", "foods"}: raise HTTPException(404, "Upload type not found")
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}: raise HTTPException(415, "Use JPG, PNG, or WEBP images")
    target = Path(__file__).resolve().parents[4] / "uploads" / kind; target.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{Path(image.filename or '').suffix.lower()}"; destination = target / filename
    with destination.open("wb") as output: output.write(image.file.read())
    return {"url": f"/uploads/{kind}/{filename}"}

def cart_for(db, user): return db.query(Cart).options(joinedload(Cart.items).joinedload(CartItem.food)).filter(Cart.user_id == user.id).first()
def cart_out(cart):
    return {"id": cart.id, "restaurant_id": cart.restaurant_id, "items": cart.items, "total_price": sum((i.food.price * i.quantity for i in cart.items), Decimal("0"))}
@router.get("/cart", response_model=CartOut)
def get_cart(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cart = cart_for(db, user)
    if not cart: cart = commit(db, Cart(user_id=user.id))
    return cart_out(cart)
@router.post("/cart/items", response_model=CartOut)
def add_cart(body: CartAdd, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    food_obj = one(db, Food, body.food_id)
    if not food_obj.is_available: raise HTTPException(400, "Food is unavailable")
    cart = cart_for(db, user) or Cart(user_id=user.id)
    if cart.restaurant_id and cart.restaurant_id != food_obj.restaurant_id:
        if not body.clear_existing: raise HTTPException(409, "Cart contains another restaurant. Confirm clear_existing to continue.")
        cart.items.clear()
    cart.restaurant_id = food_obj.restaurant_id
    item = next((x for x in cart.items if x.food_id == food_obj.id), None)
    if item: item.quantity += body.quantity
    else: cart.items.append(CartItem(food=food_obj, quantity=body.quantity))
    commit(db, cart); return cart_out(cart_for(db, user))
@router.put("/cart/items/{item_id}", response_model=CartOut)
def update_cart(item_id: int, body: CartUpdate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cart = cart_for(db, user); item = next((x for x in (cart.items if cart else []) if x.id == item_id), None)
    if not item: raise HTTPException(404, "Cart item not found")
    item.quantity = body.quantity; commit(db, cart); return cart_out(cart_for(db, user))
@router.delete("/cart/items/{item_id}", response_model=CartOut)
def remove_cart(item_id: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cart = cart_for(db, user); item = next((x for x in (cart.items if cart else []) if x.id == item_id), None)
    if not item: raise HTTPException(404, "Cart item not found")
    db.delete(item); db.commit(); cart = cart_for(db, user); 
    if not cart.items: cart.restaurant_id = None; commit(db, cart)
    return cart_out(cart_for(db, user))
@router.delete("/cart", status_code=204)
def clear_cart(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cart = cart_for(db, user)
    if cart: cart.items.clear(); cart.restaurant_id = None; db.commit()

@router.post("/orders", response_model=OrderOut, status_code=201)
def place_order(body: OrderCreate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cart = cart_for(db, user)
    if not cart or not cart.items: raise HTTPException(400, "Cart is empty")
    total = sum((i.food.price * i.quantity for i in cart.items), Decimal("0"))
    order = Order(user_id=user.id, restaurant_id=cart.restaurant_id, total_price=total, delivery_address=body.delivery_address)
    for item in cart.items: order.items.append(OrderItem(food_id=item.food_id, name=item.food.name, price=item.food.price, quantity=item.quantity))
    cart.items.clear(); cart.restaurant_id = None; return commit(db, order)
@router.get("/orders", response_model=list[OrderOut])
def orders(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)): return db.query(Order).filter(Order.user_id == user.id).order_by(desc(Order.created_at)).all()
@router.get("/orders/{order_id}", response_model=OrderOut)
def order(order_id: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    obj = one(db, Order, order_id)
    if obj.user_id != user.id and user.role.value != "admin": raise HTTPException(403, "Not allowed")
    return obj
@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    obj = one(db, Order, order_id)
    if obj.user_id != user.id: raise HTTPException(403, "Not allowed")
    # Allow cancellation for PENDING, ACCEPTED, PREPARING
    if obj.status not in [OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PREPARING]:
        raise HTTPException(400, "Only pending, accepted, or preparing orders can be cancelled")
    obj.status = OrderStatus.CANCELLED
    return commit(db, obj)
@router.patch("/orders/{order_id}/status", response_model=OrderOut, dependencies=[Depends(admin)])
def order_status(order_id: int, body: OrderStatusUpdate, db: Session = Depends(get_db)):
    obj = one(db, Order, order_id)
    obj.status = body.status
    return commit(db, obj)
@router.get("/admin/orders", response_model=list[OrderOut], dependencies=[Depends(admin)])
def admin_orders(db: Session = Depends(get_db)): return db.query(Order).order_by(desc(Order.created_at)).all()
@router.get("/admin/reports", dependencies=[Depends(admin)])
def reports(db: Session = Depends(get_db)):
    return {"total_users": db.query(func.count(User.id)).scalar(), "total_restaurants": db.query(func.count(Restaurant.id)).scalar(), "total_foods": db.query(func.count(Food.id)).scalar(), "total_orders": db.query(func.count(Order.id)).scalar(), "total_revenue": db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(Order.status != OrderStatus.CANCELLED).scalar()}

@router.get("/admin/users", response_model=list[UserResponse], dependencies=[Depends(admin)])
def admin_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()

@router.patch("/admin/users/{user_id}", response_model=UserResponse, dependencies=[Depends(admin)])
def admin_update_user(user_id: int, body: AdminUserUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    obj = one(db, User, user_id)
    if body.role is not None:
        try:
            obj.role = UserRole(body.role)
        except ValueError:
            raise HTTPException(422, "Unknown role")
    if body.is_active is not None:
        if obj.id == current_admin.id and not body.is_active:
            raise HTTPException(400, "You cannot deactivate your own account")
        obj.is_active = body.is_active
    if body.full_name is not None:
        obj.full_name = body.full_name
    return commit(db, obj)

@router.get("/admin/foods", response_model=list[FoodOut], dependencies=[Depends(admin)])
def admin_foods(db: Session = Depends(get_db)):
    return db.query(Food).order_by(Food.name).all()

@router.get("/reviews", response_model=list[ReviewOut])
def reviews(restaurant_id: int | None = None, food_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Review)
    if restaurant_id: q = q.filter(Review.restaurant_id == restaurant_id)
    if food_id: q = q.filter(Review.food_id == food_id)
    return q.order_by(desc(Review.created_at)).all()
@router.post("/reviews", response_model=ReviewOut, status_code=201)
def create_review(body: ReviewIn, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if body.restaurant_id: one(db, Restaurant, body.restaurant_id)
    if body.food_id: one(db, Food, body.food_id)
    field, value = (Review.restaurant_id, body.restaurant_id) if body.restaurant_id else (Review.food_id, body.food_id)
    if db.query(Review).filter(Review.user_id == user.id, field == value).first(): raise HTTPException(409, "You already reviewed this item")
    review = commit(db, Review(user_id=user.id, **body.model_dump()))
    refresh_restaurant_rating(db, review.restaurant_id)
    return review
@router.put("/reviews/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, body: ReviewIn, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    obj = one(db, Review, review_id)
    if obj.user_id != user.id: raise HTTPException(403, "Not allowed")
    old_restaurant_id = obj.restaurant_id
    for key, value in body.model_dump().items(): setattr(obj, key, value)
    review = commit(db, obj); refresh_restaurant_rating(db, old_restaurant_id); refresh_restaurant_rating(db, review.restaurant_id)
    return review
@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(review_id: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    obj = one(db, Review, review_id)
    if obj.user_id != user.id: raise HTTPException(403, "Not allowed")
    restaurant_id = obj.restaurant_id; db.delete(obj); db.commit(); refresh_restaurant_rating(db, restaurant_id)
