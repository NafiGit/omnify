from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional, List
import re


class FitnessClass(BaseModel):
    """Model for fitness class data"""
    id: int
    name: str
    date_time: datetime
    instructor: str
    available_slots: int
    total_slots: int

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookingRequest(BaseModel):
    """Model for booking request validation"""
    class_id: int
    client_name: str
    client_email: str

    @validator('client_name')
    def validate_client_name(cls, v):
        if not v.strip():
            raise ValueError('Client name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Client name must be at least 2 characters long')
        return v.strip()

    @validator('client_email')
    def validate_client_email(cls, v):
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('class_id')
    def validate_class_id(cls, v):
        if v <= 0:
            raise ValueError('Class ID must be a positive integer')
        return v


class BookingResponse(BaseModel):
    """Model for booking response"""
    booking_id: int
    class_name: str
    client_name: str
    client_email: str
    booking_date: datetime
    message: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookingHistory(BaseModel):
    """Model for booking history"""
    id: int
    class_name: str
    client_name: str
    client_email: str
    booking_date: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str
    detail: Optional[str] = None 