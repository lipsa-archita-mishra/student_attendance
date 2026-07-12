import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.db import get_all_students, get_all_attendance, read_json
from components.cards import render_kpi_dashboard
from utils.logger import log_event, AUDIT_LOG_FILE

def show_dashboard():
    st.title("🏫 Dashboard")
    st.markdown("Welcome to the **Attendance Management System** portal. Here is a quick snapshot of today's academic state.")
    st.markdown("---")

    # Load data
    students = get_all_students()
    attendance = get_all_attendance()
    
    total_students = len(students)
    
    # Calculate today's metrics
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_attendance = attendance.get(today_str, {})
    
    present_today = 0
    absent_today = 0
    late_today = 0
    
    for s_id, record in today_attendance.items():
        # verify student still exists in active records
        if s_id in students:
            status = record.get("status")
            if status == "Present":
                present_today += 1
            elif status == "Absent":
                absent_today += 1
            elif status == "Late":
                late_today += 1
                
    # If today's attendance has not been marked at all, default to showing the total number as unrecorded.
    # But if it has been marked, calculate rate
    recorded_count = len(today_attendance)
    if recorded_count > 0:
        marked_present_late = present_today + late_today
        # Rate relative to students who actually have marked records
        attendance_rate = (marked_present_late / recorded_count) * 100 if recorded_count > 0 else 0.0
    else:
        attendance_rate = 0.0
        # If no attendance marked today, they are effectively unregistered for today
        # We'll display present/absent/late as 0 until marked
        
    # Render modern glassmorphism metric cards
    render_kpi_dashboard(
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        late_today=late_today,
        attendance_rate=attendance_rate
    )
    
    st.markdown("---")
    
    # Dashboard Grid Layout: Quick Actions & Recent Activity
    col_actions, col_logs = st.columns([1, 1])
    
    with col_actions:
        st.markdown("### ⚡ Quick Actions")
        
        # We can simulate navigation by modifying session state page
        if st.button("📝 Mark Today's Attendance", use_container_width=True, type="primary"):
            st.session_state.current_page = "Attendance"
            st.rerun()
            
        if st.button("➕ Register New Student", use_container_width=True):
            st.session_state.current_page = "Students"
            # We can set sub_mode inside students page to trigger new entry form directly
            st.session_state.student_sub_mode = "Add New"
            st.rerun()
            
        if st.button("📊 Export Performance Reports", use_container_width=True):
            st.session_state.current_page = "Reports"
            st.rerun()
            
        # Add visual system info card
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(
            f"**System Information**\n\n"
            f"- **Date**: {datetime.now().strftime('%A, %B %d, %Y')}\n"
            f"- **Active Term**: {st.session_state.get('settings', {}).get('academic_year', '2026-2027')}\n"
            f"- **Database Format**: JSON Flat files"
        )
        
    with col_logs:
        st.markdown("### 📋 System Activity Log")
        
        # Load activity log from json
        logs = read_json(AUDIT_LOG_FILE, [])
        if not logs:
            st.info("No system activity recorded yet.")
        else:
            # Display logs in a scrollable styled container
            log_items_html = ""
            # Display latest 8 logs
            for log in logs[:8]:
                timestamp = log.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%b %d %H:%M")
                except:
                    time_str = timestamp[:16]
                    
                event_type = log.get("event_type", "EVENT").upper()
                desc = log.get("description", "")
                user = log.get("username", "system")
                
                # Determine pill color
                pill_color = "#3B82F6" # Blue
                if "fail" in event_type.lower() or "delete" in event_type.lower() or "error" in event_type.lower():
                    pill_color = "#EF4444" # Red
                elif "success" in event_type.lower() or "add" in event_type.lower() or "mark" in event_type.lower():
                    pill_color = "#10B981" # Green
                elif "backup" in event_type.lower():
                    pill_color = "#8B5CF6" # Purple
                    
                log_items_html += f"""
                <div style="
                    border-left: 4px solid {pill_color};
                    background: rgba(255, 255, 255, 0.05);
                    padding: 10px 14px;
                    border-radius: 4px;
                    margin-bottom: 8px;
                    font-size: 0.85rem;
                ">
                    <div style="display: flex; justify-content: space-between; font-weight: 600; margin-bottom: 4px;">
                        <span><span style="color: {pill_color}; font-size: 0.75rem; padding: 2px 6px; border: 1px solid {pill_color}; border-radius: 12px; margin-right: 6px;">{event_type}</span> @{user}</span>
                        <span style="color: #888; font-size: 0.75rem;">{time_str}</span>
                    </div>
                    <div style="color: #ccc;">{desc}</div>
                </div>
                """
                
            scroll_container_html = f"""
            <div style="max-height: 320px; overflow-y: auto; padding-right: 6px;">
                {log_items_html}
            </div>
            """
            st.markdown(scroll_container_html, unsafe_allow_html=True)
