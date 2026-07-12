import streamlit as st
import pandas as pd
from typing import List, Dict, Any

def render_students_table(students_list: List[Dict[str, Any]]):
    """
    Renders an interactive, searchable and beautiful table of students.
    """
    if not students_list:
        st.info("No students found.")
        return
        
    df = pd.DataFrame(students_list)
    
    # Select and reorder columns for display
    display_cols = [
        "id", "name", "roll_number", "department", 
        "semester", "section", "email", "phone", "address"
    ]
    df_display = df[display_cols].copy()
    
    # Rename columns for presentation
    df_display.columns = [
        "Student ID", "Name", "Roll Number", "Department", 
        "Semester", "Section", "Email Address", "Phone Number", "Home Address"
    ]
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Student ID": st.column_config.TextColumn("ID", help="Unique system identifier", width="medium"),
            "Name": st.column_config.TextColumn("Student Name", help="Full legal name", width="medium"),
            "Roll Number": st.column_config.TextColumn("Roll No.", width="small"),
            "Email Address": st.column_config.LinkColumn("Email", width="medium"),
            "Phone Number": st.column_config.TextColumn("Phone", width="small"),
        }
    )

def render_attendance_log_table(logs: List[Dict[str, Any]]):
    """
    Renders a formatted table containing logs of attendance.
    """
    if not logs:
        st.info("No attendance records found.")
        return
        
    df = pd.DataFrame(logs)
    
    # Make columns look pretty
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "roll_number": st.column_config.TextColumn("Roll No."),
            "student_name": st.column_config.TextColumn("Name"),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["Present", "Absent", "Late"],
                width="small"
            ),
            "timestamp": st.column_config.TextColumn("Marked Time"),
            "marked_by": st.column_config.TextColumn("Recorded By"),
            "notes": st.column_config.TextColumn("Comments", width="medium")
        }
    )
