from datetime import datetime, time
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.commerce import OrderStatus, DeliveryStatus

class ORM(BaseModel): model_config = ConfigDict(from_attributes=True)
class CategoryIn(BaseModel): name: str = Field(min_length=2, max_length=100)
class CategoryOut(CategoryIn, ORM): id: int
class RestaurantIn(BaseModel):
    name: str = Field(min_length=2, max_length=150); description: str = Field(min_length=2); image: Optional[str] = None
    address: str = Field(min_length=5, max_length=300); phone: str = Field(min_length=10, max_length=20)
    opening_time: time; closing_time: time; rating: float = Field(default=0, ge=0, le=5); is_active: bool = True
class RestaurantOut(RestaurantIn, ORM): id: int; created_at: datetime
class FoodIn(BaseModel):
    restaurant_id: int; category_id: int; name: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=2); price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    image: Optional[str] = None; is_available: bool = True
class FoodInRestaurant(BaseModel):
    category_id: int; name: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=2); price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    image: Optional[str] = None; is_available: bool = True
class FoodOut(FoodIn, ORM): id: int
class CartAdd(BaseModel): food_id: int; quantity: int = Field(default=1, ge=1, le=20); clear_existing: bool = False
class CartUpdate(BaseModel): quantity: int = Field(ge=1, le=20)
class CartItemOut(ORM): id: int; food_id: int; quantity: int; food: FoodOut
class CartOut(ORM): id: int; restaurant_id: Optional[int]; items: list[CartItemOut]; total_price: Decimal
class OrderCreate(BaseModel): delivery_address: str = Field(min_length=10, max_length=500)
class OrderStatusUpdate(BaseModel): status: OrderStatus
class OrderItemOut(ORM): id: int; food_id: Optional[int]; name: str; price: Decimal; quantity: int
class OrderOut(ORM): 
    id: int; restaurant_id: int; status: OrderStatus; delivery_status: Optional[DeliveryStatus] = None
    total_price: Decimal; delivery_address: str; created_at: datetime; assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None; delivered_at: Optional[datetime] = None
    items: list[OrderItemOut]
    delivery_person_id: Optional[int] = None
class ReviewIn(BaseModel):
    restaurant_id: Optional[int] = None; food_id: Optional[int] = None; rating: int = Field(ge=1, le=5); comment: Optional[str] = Field(default=None, max_length=1000)
    @model_validator(mode="after")
    def target(self):
        if (self.restaurant_id is None) == (self.food_id is None): raise ValueError("Provide exactly one of restaurant_id or food_id")
        return self
class ReviewOut(ReviewIn, ORM): id: int; user_id: int; created_at: datetime; updated_at: datetime


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    role: Optional[str] = None
    is_active: Optional[bool] = None
