import re
from typing import Tuple
from utils.db import get_all_students

def validate_email(email: str) -> bool:
    """Validate email format using standard regex."""
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(pattern.match(email.strip()))

def validate_phone(phone: str) -> bool:
    """Validate phone format. Must be between 7 to 15 digits, allowing optional leading '+'."""
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    pattern = re.compile(r'^\+?[1-9]\d{6,14}$')
    return bool(pattern.match(cleaned))

def validate_student_fields(
    student_id: str,
    name: str,
    roll_number: str,
    email: str,
    phone: str,
    address: str,
    is_edit: bool = False,
    original_id: str = ""
) -> Tuple[bool, str]:
    """
    Validates all field inputs for adding or editing a student.
    Returns (is_valid, error_message).
    """
    # 1. Validate required fields
    if not student_id.strip():
        return False, "Student ID is required."
    if not name.strip():
        return False, "Student Name is required."
    if not roll_number.strip():
        return False, "Roll Number is required."
    if not email.strip():
        return False, "Email address is required."
    if not phone.strip():
        return False, "Phone number is required."
    if not address.strip():
        return False, "Home address is required."

    # 2. Check formats
    if not validate_email(email):
        return False, f"Invalid email format: '{email}'"
    if not validate_phone(phone):
        return False, f"Invalid phone number format: '{phone}'. Use a valid international or local number (e.g. +1234567890 or 9876543210)."

    # 3. Check uniqueness
    students = get_all_students()
    
    # Clean inputs for uniqueness check
    student_id_clean = student_id.strip()
    roll_number_clean = roll_number.strip()

    if not is_edit:
        # For new student:
        if student_id_clean in students:
            return False, f"Student ID '{student_id_clean}' already exists in the database."
        
        for s_id, s_data in students.items():
            if s_data.get("roll_number", "").strip().lower() == roll_number_clean.lower():
                return False, f"Roll Number '{roll_number_clean}' is already assigned to student '{s_data.get('name')}'."
    else:
        # For editing:
        # ID cannot change if it's the database key, but if they try to edit the ID block:
        if student_id_clean != original_id:
            if student_id_clean in students:
                return False, f"New Student ID '{student_id_clean}' already exists in the database."

        for s_id, s_data in students.items():
            if s_id != original_id:
                if s_data.get("roll_number", "").strip().lower() == roll_number_clean.lower():
                    return False, f"Roll Number '{roll_number_clean}' is already assigned to student '{s_data.get('name')}'."

    return True, ""
