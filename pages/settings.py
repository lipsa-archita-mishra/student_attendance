import os
import io
import shutil
import pandas as pd
import streamlit as st
from datetime import datetime
from pathlib import Path
from utils.db import (
    get_settings, save_settings, create_backup, 
    list_backups, restore_backup, get_all_students, save_students
)
from utils.logger import log_event
from utils.validation import validate_email, validate_phone

def show_settings_page():
    st.title("⚙️ System Settings & Data Operations")
    st.markdown("Configure institution settings, manage backups, and perform bulk import/export operations.")
    st.markdown("---")

    actor = st.session_state.get("authenticated_user", {}).get("username", "admin")

    # Tabs for Settings, Backups, and Importer
    tab_config, tab_backup, tab_import = st.tabs([
        "Institution Configuration", 
        "Database Backup & Restore", 
        "Bulk Student Importer"
    ])

    # ==========================================
    # TAB 1: INSTITUTION CONFIG
    # ==========================================
    with tab_config:
        st.subheader("🏫 Institution Parameters")
        
        current_settings = get_settings()
        
        inst_name = st.text_input("Institution Name", value=current_settings.get("institution_name", "Antigravity Institute of Technology"))
        academic_year = st.text_input("Active Academic Year", value=current_settings.get("academic_year", "2026-2027"))
        theme_val = st.selectbox("Interface Theme Override", ["Dark", "Light"], index=0 if current_settings.get("theme") == "Dark" else 1)
        
        if st.button("💾 Save Settings", type="primary"):
            current_settings["institution_name"] = inst_name.strip()
            current_settings["academic_year"] = academic_year.strip()
            current_settings["theme"] = theme_val
            
            if save_settings(current_settings):
                # Update session state settings
                st.session_state.settings = current_settings
                log_event("settings_updated", "System settings updated.", actor)
                st.success("System configurations updated successfully!")
                st.rerun()
            else:
                st.error("Failed to write configurations to database.")

    # ==========================================
    # TAB 2: BACKUPS
    # ==========================================
    with tab_backup:
        st.subheader("📦 Database Backup Control Center")
        st.info("System backups compress students, attendance, users, and settings databases into localized snapshots.")
        
        col_btn, _ = st.columns([1, 2])
        with col_btn:
            if st.button("⚡ Create Manual Backup", type="primary", use_container_width=True):
                backup_name = create_backup(actor)
                if backup_name:
                    st.success(f"System snapshot saved: **{backup_name}**")
                    st.rerun()
                else:
                    st.error("Failed to create system backup.")
                    
        st.markdown("### 📜 Available Recovery Snapshots")
        backups = list_backups()
        
        if not backups:
            st.info("No backup snapshots found in the directory.")
        else:
            for b in backups:
                # Calculate size
                b_path = Path("data/backups") / b
                size_kb = b_path.stat().st_size / 1024 if b_path.exists() else 0.0
                
                # Make display row
                col_name, col_size, col_actions = st.columns([3, 1, 2])
                with col_name:
                    st.markdown(f"📄 **{b}**")
                with col_size:
                    st.markdown(f"`{size_kb:.1f} KB`")
                with col_actions:
                    col_r, col_d = st.columns(2)
                    with col_r:
                        if st.button("Restore", key=f"restore_btn_{b}", type="secondary", use_container_width=True):
                            if restore_backup(b, actor):
                                st.success("Database restored successfully!")
                                st.rerun()
                            else:
                                st.error("Database restore failed.")
                    with col_d:
                        if st.button("Delete", key=f"del_backup_btn_{b}", type="secondary", use_container_width=True):
                            try:
                                b_path.unlink()
                                st.success(f"Deleted backup: {b}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete backup: {e}")

    # ==========================================
    # TAB 3: BULK IMPORTER
    # ==========================================
    with tab_import:
        st.subheader("📥 Bulk Student Registry Importer")
        st.markdown("""
        Import student files in **CSV** or **Excel** formats. 
        Your uploaded spreadsheet file **must contain the exact column headers** listed below:
        
        `Student ID`, `Name`, `Roll Number`, `Department`, `Semester`, `Section`, `Email`, `Phone`, `Address`
        """)
        
        # Download template buttons
        template_data = [{
            "Student ID": "STU-1001",
            "Name": "John Doe",
            "Roll Number": "CS2026-001",
            "Department": "Computer Science & Engineering",
            "Semester": "6th Semester",
            "Section": "A",
            "Email": "john.doe@school.com",
            "Phone": "+1234567890",
            "Address": "123 Main Street"
        }]
        df_temp = pd.DataFrame(template_data)
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.download_button(
                "⬇️ Download CSV Template",
                data=df_temp.to_csv(index=False).encode('utf-8'),
                file_name="student_import_template.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_t2:
            # write template to bytes for excel download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_temp.to_excel(writer, index=False)
            st.download_button(
                "⬇️ Download Excel Template",
                data=buffer.getvalue(),
                file_name="student_import_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        st.markdown("---")
        
        uploaded_file = st.file_uploader("Upload Student Sheet", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                # Read file depending on extension
                if uploaded_file.name.endswith(".csv"):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file, engine="openpyxl")
                    
                # Clean header names
                df_upload.columns = [str(c).strip() for c in df_upload.columns]
                
                # Check for required headers
                required_headers = [
                    "Student ID", "Name", "Roll Number", "Department", 
                    "Semester", "Section", "Email", "Phone", "Address"
                ]
                
                missing_headers = [rh for rh in required_headers if rh not in df_upload.columns]
                
                if missing_headers:
                    st.error(f"Upload aborted. Missing column headers: {missing_headers}")
                else:
                    st.write(f"Parsed **{len(df_upload)} records** from file. Beginning database validations...")
                    
                    active_students = get_all_students()
                    
                    success_count = 0
                    rejected_records = []
                    
                    # Track temporary roll numbers and IDs from the file to check for internal duplicates
                    file_ids = set()
                    file_rolls = set()
                    
                    for idx, row in df_upload.iterrows():
                        row_num = idx + 2 # 1-indexed plus header line
                        
                        s_id = str(row["Student ID"]).strip()
                        name = str(row["Name"]).strip()
                        roll_number = str(row["Roll Number"]).strip()
                        department = str(row["Department"]).strip()
                        semester = str(row["Semester"]).strip()
                        section = str(row["Section"]).strip()
                        email = str(row["Email"]).strip()
                        phone = str(row["Phone"]).strip()
                        address = str(row["Address"]).strip()
                        
                        # Check empty fields
                        if not all([s_id, name, roll_number, department, semester, section, email, phone, address]):
                            rejected_records.append({"Row": row_num, "ID": s_id, "Name": name, "Reason": "Empty fields found."})
                            continue
                            
                        # Format validations
                        if not validate_email(email):
                            rejected_records.append({"Row": row_num, "ID": s_id, "Name": name, "Reason": f"Invalid email format: '{email}'."})
                            continue
                        if not validate_phone(phone):
                            rejected_records.append({"Row": row_num, "ID": s_id, "Name": name, "Reason": f"Invalid phone format: '{phone}'."})
                            continue
                            
                        # Duplicate IDs check (in DB or file)
                        if s_id in active_students or s_id in file_ids:
                            rejected_records.append({"Row": row_num, "ID": s_id, "Name": name, "Reason": f"Student ID '{s_id}' already exists."})
                            continue
                            
                        # Duplicate Roll number check (in DB or file)
                        db_roll_exists = any(s.get("roll_number", "").lower() == roll_number.lower() for s in active_students.values())
                        if db_roll_exists or roll_number.lower() in file_rolls:
                            rejected_records.append({"Row": row_num, "ID": s_id, "Name": name, "Reason": f"Roll number '{roll_number}' is already assigned."})
                            continue
                            
                        # Register valid student
                        new_student = {
                            "id": s_id,
                            "name": name,
                            "roll_number": roll_number,
                            "department": department,
                            "semester": semester,
                            "section": section,
                            "email": email,
                            "phone": phone,
                            "address": address,
                            "photo_path": None
                        }
                        
                        # Add to temporary registers
                        active_students[s_id] = new_student
                        file_ids.add(s_id)
                        file_rolls.add(roll_number.lower())
                        success_count += 1
                        
                    # Save updates
                    if success_count > 0:
                        if save_students(active_students):
                            log_event("students_imported", f"Imported {success_count} students from spreadsheet.", actor)
                            st.success(f"Successfully imported **{success_count}** student records into the database.")
                        else:
                            st.error("Failed to commit imported records to the JSON file.")
                            
                    # Display rejections if any
                    if rejected_records:
                        st.warning(f"Rejected **{len(rejected_records)}** invalid records. See details below:")
                        st.dataframe(pd.DataFrame(rejected_records), use_container_width=True, hide_index=True)
                        
            except Exception as e:
                st.error(f"Error parsing file: {e}")
