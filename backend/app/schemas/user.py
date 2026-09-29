from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
from app.models.commerce import DeliveryStatus


class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=100, examples=["John Doe"])
    email: EmailStr = Field(examples=["john.doe@example.com"])
    phone: Optional[str] = Field(default=None, examples=["9876543210"])

    @field_validator("phone")
    @classmethod
    def validate_indian_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        digits = value.replace(" ", "").replace("-", "")
        if digits.startswith("+91"):
            digits = digits[3:]
        elif digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        if len(digits) != 10 or not digits.isdigit() or digits[0] not in "6789":
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return digits


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72, examples=["securepassword123"])


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = Field(default=None, examples=["9876543210"])
    password: Optional[str] = Field(default=None, min_length=8, max_length=72)

    @field_validator("phone")
    @classmethod
    def validate_indian_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        digits = value.replace(" ", "").replace("-", "")
        if digits.startswith("+91"):
            digits = digits[3:]
        elif digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        if len(digits) != 10 or not digits.isdigit() or digits[0] not in "6789":
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return digits


class UserLogin(BaseModel):
    email: EmailStr = Field(examples=["john.doe@example.com"])
    password: str = Field(min_length=8, max_length=72, examples=["password123"])


class UserInDBBase(UserBase):
    id: int
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserInDBBase):
    password_hash: str


class UserResponse(UserInDBBase):
    restaurant_id: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class AddressBase(BaseModel):
    address_line: str = Field(min_length=5, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    pincode: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    address_line: Optional[str] = Field(default=None, min_length=5, max_length=200)
    city: Optional[str] = Field(default=None, min_length=2, max_length=100)
    state: Optional[str] = Field(default=None, min_length=2, max_length=100)
    pincode: Optional[str] = Field(default=None, min_length=6, max_length=6, pattern=r"^\d{6}$")


class AddressOut(AddressBase, BaseModel):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class DeliveryPersonBase(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    vehicle_type: str = Field(min_length=2, max_length=50)
    vehicle_number: str = Field(min_length=2, max_length=50)


class DeliveryPersonCreate(DeliveryPersonBase):
    user_id: int


class DeliveryPersonUpdate(BaseModel):
    phone: Optional[str] = Field(default=None, min_length=10, max_length=20)
    vehicle_type: Optional[str] = Field(default=None, min_length=2, max_length=50)
    vehicle_number: Optional[str] = Field(default=None, min_length=2, max_length=50)
    is_available: Optional[bool] = None


class DeliveryPersonOut(DeliveryPersonBase, BaseModel):
    id: int
    user_id: int
    is_available: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignDeliveryPerson(BaseModel):
    delivery_person_id: int


class DeliveryOrderUpdate(BaseModel):
    delivery_status: DeliveryStatus
