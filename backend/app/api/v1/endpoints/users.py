from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate, AddressCreate, AddressUpdate, AddressOut
from app.security import get_current_active_user, hash_password
from app.models.user import User
from app.models.address import Address

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.password is not None:
        current_user.password_hash = hash_password(user_update.password)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/addresses", response_model=list[AddressOut])
def get_addresses(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return db.query(Address).filter(Address.user_id == current_user.id).all()


@router.post("/me/addresses", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create_address(
    address: AddressCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    db_address = Address(user_id=current_user.id, **address.model_dump())
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address


@router.put("/me/addresses/{address_id}", response_model=AddressOut)
def update_address(
    address_id: int,
    address_update: AddressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    db_address = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    for key, value in address_update.model_dump(exclude_unset=True).items():
        setattr(db_address, key, value)
    db.commit()
    db.refresh(db_address)
    return db_address


@router.delete("/me/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    db_address = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(db_address)
    db.commit()