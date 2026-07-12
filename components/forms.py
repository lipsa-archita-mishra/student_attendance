import os
import streamlit as st
from PIL import Image
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config.constants import DEPARTMENTS, SEMESTERS, SECTIONS
from utils.validation import validate_student_fields
from utils.db import UPLOADS_DIR

def handle_photo_upload(student_id: str, uploaded_file) -> Optional[str]:
    """
    Saves an uploaded photo using PIL as standard PNG and returns the file path.
    """
    if uploaded_file is None:
        return None
    try:
        image = Image.open(uploaded_file)
        # standard filename to avoid space or character issues
        # clean student_id
        safe_id = "".join([c for c in student_id if c.isalnum() or c in ("-", "_")])
        save_path = UPLOADS_DIR / f"{safe_id}.png"
        
        # Save image as PNG
        image.save(save_path, "PNG")
        return str(save_path)
    except Exception as e:
        st.error(f"Error saving profile picture: {e}")
        return None

def student_form(
    initial_data: Optional[Dict[str, Any]] = None,
    is_edit: bool = False,
    key_prefix: str = "form"
) -> Tuple[Optional[Dict[str, Any]], Optional[Any]]:
    """
    Renders a unified form for adding and editing a student.
    Returns (form_data, uploaded_photo_file) if submitted, (None, None) otherwise.
    """
    data = initial_data or {}
    
    # Mode header
    st.subheader("Student Details" if is_edit else "Register New Student")
    
    # We will use columns to organize fields nicely
    col1, col2 = st.columns(2)
    
    with col1:
        # ID is read-only during edits
        student_id = st.text_input(
            "Student ID *", 
            value=data.get("id", ""), 
            disabled=is_edit,
            help="E.g., STU-1001. Cannot be changed after creation.",
            key=f"{key_prefix}_id"
        )
        name = st.text_input("Full Name *", value=data.get("name", ""), key=f"{key_prefix}_name")
        roll_number = st.text_input("Roll Number / Registration No. *", value=data.get("roll_number", ""), key=f"{key_prefix}_roll")
        
        # Dropdowns
        dept_val = data.get("department", DEPARTMENTS[0])
        dept_idx = DEPARTMENTS.index(dept_val) if dept_val in DEPARTMENTS else 0
        department = st.selectbox("Department *", DEPARTMENTS, index=dept_idx, key=f"{key_prefix}_dept")
        
        sem_val = data.get("semester", SEMESTERS[0])
        sem_idx = SEMESTERS.index(sem_val) if sem_val in SEMESTERS else 0
        semester = st.selectbox("Semester *", SEMESTERS, index=sem_idx, key=f"{key_prefix}_sem")

    with col2:
        sec_val = data.get("section", SECTIONS[0])
        sec_idx = SECTIONS.index(sec_val) if sec_val in SECTIONS else 0
        section = st.selectbox("Section *", SECTIONS, index=sec_idx, key=f"{key_prefix}_sec")
        
        email = st.text_input("Email Address *", value=data.get("email", ""), key=f"{key_prefix}_email")
        phone = st.text_input("Phone Number *", value=data.get("phone", ""), key=f"{key_prefix}_phone")
        address = st.text_area("Home Address *", value=data.get("address", ""), height=100, key=f"{key_prefix}_address")

    # Photo uploading and preview
    st.markdown("### Profile Picture")
    col_pic1, col_pic2 = st.columns([1, 3])
    
    existing_photo_path = data.get("photo_path")
    photo_removed = False

    with col_pic1:
        if existing_photo_path and os.path.exists(existing_photo_path):
            st.image(existing_photo_path, caption="Current Picture", use_container_width=True)
            if st.button("Remove Photo", key=f"{key_prefix}_remove_photo_btn"):
                photo_removed = True
        else:
            st.info("No Photo Uploaded")
            
    with col_pic2:
        uploaded_file = st.file_uploader(
            "Upload Photo (PNG, JPG, JPEG)", 
            type=["png", "jpg", "jpeg"],
            help="Recommend square dimensions for profile display.",
            key=f"{key_prefix}_photo"
        )
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Preview", width=120)

    # Submission
    submit_label = "Update Student Record" if is_edit else "Add Student"
    submitted = st.button(submit_label, type="primary", key=f"{key_prefix}_submit")
    
    if submitted:
        # Assemble form data
        form_data = {
            "id": student_id.strip(),
            "name": name.strip(),
            "roll_number": roll_number.strip(),
            "department": department,
            "semester": semester,
            "section": section,
            "email": email.strip(),
            "phone": phone.strip(),
            "address": address.strip(),
            "photo_path": existing_photo_path if not photo_removed else None
        }
        
        # Validate
        is_valid, err_msg = validate_student_fields(
            student_id=form_data["id"],
            name=form_data["name"],
            roll_number=form_data["roll_number"],
            email=form_data["email"],
            phone=form_data["phone"],
            address=form_data["address"],
            is_edit=is_edit,
            original_id=data.get("id", "")
        )
        
        if not is_valid:
            st.error(err_msg)
            return None, None
            
        # Handle saving the file if valid
        if uploaded_file:
            pic_path = handle_photo_upload(form_data["id"], uploaded_file)
            if pic_path:
                form_data["photo_path"] = pic_path
                
        return form_data, uploaded_file
        
    return None, None
