from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, Time
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    image = Column(String(500), nullable=True)
    address = Column(String(300), nullable=False)
    phone = Column(String(20), nullable=False)
    opening_time = Column(Time, nullable=False)
    closing_time = Column(Time, nullable=False)
    rating = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    foods = relationship("Food", back_populates="restaurant", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")
