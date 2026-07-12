import streamlit as st
import pandas as pd
from datetime import datetime
from utils.db import get_all_students, get_all_attendance, save_attendance
from utils.logger import log_event
from config.constants import DEPARTMENTS, SEMESTERS, SECTIONS

def show_attendance_page():
    st.title("📝 Attendance Registry")
    st.markdown("Select a date and class grouping to mark or edit student attendance.")
    st.markdown("---")

    # Load DB records
    students = get_all_students()
    attendance = get_all_attendance()
    actor = st.session_state.get("authenticated_user", {}).get("username", "admin")

    if not students:
        st.info("No students registered in the database. Please add students first.")
        return

    # Date and Class Selection Widgets
    col_date, col_dept, col_sem, col_sec = st.columns([1, 1.2, 1, 0.8])
    
    with col_date:
        selected_date = st.date_input("Select Date", datetime.now().date())
        date_str = selected_date.strftime("%Y-%m-%d")
        
    with col_dept:
        selected_dept = st.selectbox("Department", DEPARTMENTS)
        
    with col_sem:
        selected_sem = st.selectbox("Semester", SEMESTERS)
        
    with col_sec:
        selected_sec = st.selectbox("Section", SECTIONS)

    # Filter students by selection
    class_students = []
    for s_id, s_data in students.items():
        if (s_data.get("department") == selected_dept and 
            s_data.get("semester") == selected_sem and 
            s_data.get("section") == selected_sec):
            class_students.append(s_data)

    st.markdown("---")

    if not class_students:
        st.warning(f"No students found registered in: **{selected_dept}**, **{selected_sem}**, Section **{selected_sec}**.")
        return

    st.write(f"Class Strength: **{len(class_students)} students** found.")

    # Prepare DataFrame for data_editor
    # Fetch existing attendance records for the selected date if they exist
    date_records = attendance.get(date_str, {})
    
    records_list = []
    for student in class_students:
        s_id = student["id"]
        # Default values if no attendance is logged for today
        status = "Present"
        notes = ""
        
        if s_id in date_records:
            status = date_records[s_id].get("status", "Present")
            notes = date_records[s_id].get("notes", "")
            
        records_list.append({
            "Student ID": s_id,
            "Roll Number": student.get("roll_number"),
            "Student Name": student.get("name"),
            "Status": status,
            "Notes / Remarks": notes
        })

    df_records = pd.DataFrame(records_list)

    # UI details and interactive data editor
    st.info("💡 Edit the **Status** or **Notes** column directly in the grid below, then click **Save Attendance Registry** to submit.")
    
    edited_df = st.data_editor(
        df_records,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Student ID": st.column_config.TextColumn("ID", disabled=True),
            "Roll Number": st.column_config.TextColumn("Roll No", disabled=True),
            "Student Name": st.column_config.TextColumn("Name", disabled=True),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Present", "Absent", "Late"],
                required=True,
                width="medium"
            ),
            "Notes / Remarks": st.column_config.TextColumn("Notes / Remarks", width="large")
        }
    )

    # Save button
    if st.button("💾 Save Attendance Registry", type="primary", use_container_width=True):
        # Format registry updates
        if date_str not in attendance:
            attendance[date_str] = {}
            
        timestamp_now = datetime.now().isoformat()
        
        # Keep track of counts for logs
        p_count, a_count, l_count = 0, 0, 0
        
        for index, row in edited_df.iterrows():
            s_id = row["Student ID"]
            status = row["Status"]
            notes = str(row["Notes / Remarks"]).strip()
            
            attendance[date_str][s_id] = {
                "status": status,
                "timestamp": timestamp_now,
                "marked_by": actor,
                "notes": notes
            }
            
            if status == "Present":
                p_count += 1
            elif status == "Absent":
                a_count += 1
            elif status == "Late":
                l_count += 1

        if save_attendance(attendance):
            # Log action
            log_event(
                "attendance_marked", 
                f"Marked attendance on {date_str} for {selected_dept} {selected_sem} Sec {selected_sec}. "
                f"Stats: Present={p_count}, Absent={a_count}, Late={l_count}", 
                actor
            )
            st.success(f"Attendance for {date_str} saved successfully! Stats: {p_count} Present, {a_count} Absent, {l_count} Late.")
            st.balloons()
        else:
            st.error("Failed to save records to the JSON database.")
            
    # Add Section: Quick Attendance Summary for selected day
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📊 View Today's Stats Details"):
        total = len(df_records)
        present = len(df_records[df_records["Status"] == "Present"])
        absent = len(df_records[df_records["Status"] == "Absent"])
        late = len(df_records[df_records["Status"] == "Late"])
        rate = (present + late) / total * 100 if total > 0 else 0
        
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        col_c1.metric("Class Strength", total)
        col_c2.metric("Present Today", present)
        col_c3.metric("Absent Today", absent)
        col_c4.metric("Attendance Percentage", f"{rate:.1f}%")
