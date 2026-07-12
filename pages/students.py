import os
import streamlit as st
import pandas as pd
from pathlib import Path
from utils.db import get_all_students, save_students, UPLOADS_DIR
from utils.logger import log_event
from components.forms import student_form
from config.constants import DEPARTMENTS, SEMESTERS, SECTIONS

def show_students_page():
    st.title("👥 Student Management")
    st.markdown("Register new students, update profiles, or search records here.")
    st.markdown("---")

    # Sync state from dashboard redirect
    sub_mode = st.session_state.get("student_sub_mode", "Directory")
    
    # We will use tabs for navigation inside Student Management
    tab_list = ["Directory", "Register Student", "Search & Manage"]
    default_idx = tab_list.index(sub_mode) if sub_mode in tab_list else 0
    
    # Reset redirect parameter
    if "student_sub_mode" in st.session_state:
        del st.session_state.student_sub_mode

    tab_dir, tab_add, tab_manage = st.tabs(tab_list)

    # Load active database
    students = get_all_students()
    actor = st.session_state.get("authenticated_user", {}).get("username", "admin")

    # ==========================================
    # TAB 1: DIRECTORY VIEW
    # ==========================================
    with tab_dir:
        st.subheader("📚 Active Student Directory")
        
        if not students:
            st.info("No students registered in the database yet. Go to 'Register Student' to add one.")
        else:
            # Filter bar
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                dept_filter = st.selectbox("Filter Department", ["All"] + DEPARTMENTS, key="dir_dept_filter")
            with col_f2:
                sem_filter = st.selectbox("Filter Semester", ["All"] + SEMESTERS, key="dir_sem_filter")
            with col_f3:
                sec_filter = st.selectbox("Filter Section", ["All"] + SECTIONS, key="dir_sec_filter")

            # Search bar
            search_query = st.text_input("🔍 Quick Search by Name or Roll Number", key="dir_search_input").strip().lower()

            # Process filters
            filtered_students = []
            for s_id, s_data in students.items():
                # Filter criteria
                if dept_filter != "All" and s_data.get("department") != dept_filter:
                    continue
                if sem_filter != "All" and s_data.get("semester") != sem_filter:
                    continue
                if sec_filter != "All" and s_data.get("section") != sec_filter:
                    continue
                
                # Search criteria
                name_match = search_query in s_data.get("name", "").lower()
                roll_match = search_query in s_data.get("roll_number", "").lower()
                id_match = search_query in s_id.lower()
                
                if search_query and not (name_match or roll_match or id_match):
                    continue
                    
                filtered_students.append(s_data)

            st.write(f"Showing {len(filtered_students)} of {len(students)} registered students.")

            # Render Table
            if filtered_students:
                df = pd.DataFrame(filtered_students)
                # Select display columns
                df_view = df[["id", "name", "roll_number", "department", "semester", "section", "email", "phone"]].copy()
                df_view.columns = ["ID", "Student Name", "Roll No", "Department", "Semester", "Section", "Email Address", "Phone"]
                
                st.dataframe(df_view, use_container_width=True, hide_index=True)
            else:
                st.warning("No records match the applied filters.")

    # ==========================================
    # TAB 2: REGISTER NEW STUDENT
    # ==========================================
    with tab_add:
        # Render the student creation form
        form_data, uploaded_file = student_form(is_edit=False)
        
        if form_data:
            # Add to DB
            students[form_data["id"]] = form_data
            if save_students(students):
                log_event("student_added", f"Registered new student '{form_data['name']}' ({form_data['id']})", actor)
                st.success(f"Student '{form_data['name']}' registered successfully!")
                # Refresh page state
                st.rerun()
            else:
                st.error("Failed to write to database. Check system logs.")

    # ==========================================
    # TAB 3: MANAGE PROFILE (EDIT / DELETE)
    # ==========================================
    with tab_manage:
        st.subheader("🛠️ Profile Manager")
        
        if not students:
            st.info("No students available to manage.")
        else:
            # Student lookup dropdown
            student_options = {f"{data['name']} ({data['roll_number']})": s_id for s_id, data in students.items()}
            selected_student_label = st.selectbox("Select Student to View/Modify", list(student_options.keys()))
            selected_id = student_options[selected_student_label]
            
            student_data = students[selected_id]
            
            # Divide UI into profile card and editing form
            col_card, col_edit = st.columns([1, 2])
            
            with col_card:
                st.markdown("### Profile Card")
                
                # Image check
                img_path = student_data.get("photo_path")
                if img_path and os.path.exists(img_path):
                    st.image(img_path, width=200, use_container_width=False)
                else:
                    st.image("https://api.dicebear.com/7.x/initials/svg?seed=" + student_data.get("name", "Student"), width=200)
                    
                st.markdown(f"""
                **Name**: {student_data.get('name')}<br>
                **Roll Number**: {student_data.get('roll_number')}<br>
                **ID**: `{student_data.get('id')}`<br>
                **Class**: {student_data.get('department')}<br>
                **Semester / Sec**: {student_data.get('semester')} - Sec {student_data.get('section')}<br>
                **Email**: {student_data.get('email')}<br>
                **Phone**: {student_data.get('phone')}<br>
                **Address**: {student_data.get('address')}
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Danger Zone: Deletion
                st.markdown("<span style='color:red;font-weight:bold;'>⚠️ Danger Zone</span>", unsafe_allow_html=True)
                confirm_delete = st.checkbox("Confirm database deletion", key=f"del_confirm_{selected_id}")
                if st.button("🗑️ Delete Student", key=f"del_btn_{selected_id}", type="primary", disabled=not confirm_delete):
                    # Delete photo file if it exists
                    if img_path and os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                        except Exception as e:
                            st.warning(f"Could not remove student photo file: {e}")
                            
                    del students[selected_id]
                    if save_students(students):
                        log_event("student_deleted", f"Deleted student '{student_data['name']}' ({selected_id})", actor)
                        st.success(f"Student '{student_data['name']}' deleted successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to update database.")
                        
            with col_edit:
                st.markdown("### Edit details")
                # Render editing form pre-populated
                edited_data, uploaded_edit_file = student_form(initial_data=student_data, is_edit=True)
                
                if edited_data:
                    # Save changes
                    students[selected_id] = edited_data
                    if save_students(students):
                        log_event("student_edited", f"Updated student profile details for '{edited_data['name']}' ({selected_id})", actor)
                        st.success("Student details updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to write updates to database.")
