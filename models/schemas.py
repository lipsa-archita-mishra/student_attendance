from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict
import re

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password_hash: str
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: str = Field(default="Admin")

class Student(BaseModel):
    id: str = Field(..., description="Unique Student ID (e.g. STU-UUID)")
    name: str = Field(..., min_length=2, max_length=100)
    roll_number: str = Field(..., min_length=2, max_length=50)
    department: str
    semester: str
    section: str
    email: EmailStr
    phone: str
    address: str = Field(..., min_length=5, max_length=250)
    photo_path: Optional[str] = None

    @field_validator('phone')
    def validate_phone(cls, v):
        # Validate simple phone format e.g. +1234567890 or 1234567890
        pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
        # Remove spaces, dashes, parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not pattern.match(cleaned):
            raise ValueError("Invalid phone number format. Must be a valid E.164 phone number.")
        return cleaned

class AttendanceEntry(BaseModel):
    status: str = Field(..., description="Present, Absent, or Late")
    timestamp: str = Field(..., description="ISO 8601 Timestamp of marking")
    marked_by: str = Field(..., description="Username of the user who marked this")
    notes: Optional[str] = ""

    @field_validator('status')
    def validate_status(cls, v):
        allowed = ["Present", "Absent", "Late"]
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v

class SystemSettings(BaseModel):
    institution_name: str = Field(default="Antigravity Institute of Technology")
    academic_year: str = Field(default="2026-2027")
    theme: str = Field(default="Dark")
    backup_frequency: str = Field(default="Manual")
