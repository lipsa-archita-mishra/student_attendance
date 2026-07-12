import io
import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from utils.db import get_all_students, get_all_attendance, REPORTS_DIR
from utils.export import export_to_csv, export_to_excel, export_to_pdf
from utils.logger import log_event
from config.constants import DEPARTMENTS, SEMESTERS, SECTIONS

def show_reports_page():
    st.title("📊 Reports Generator")
    st.markdown("Preview and export student attendance logs across custom periods.")
    st.markdown("---")

    # Load data
    students = get_all_students()
    attendance = get_all_attendance()
    actor = st.session_state.get("authenticated_user", {}).get("username", "admin")

    if not students:
        st.info("No student records found. Add students before compiling reports.")
        return

    # Tabs for different report scopes
    tab_daily, tab_weekly, tab_monthly, tab_student = st.tabs([
        "Daily Report", 
        "Weekly Summary", 
        "Monthly Attendance Matrix", 
        "Student Report"
    ])

    # ==========================================
    # TAB 1: DAILY REPORT
    # ==========================================
    with tab_daily:
        st.subheader("📆 Daily Attendance Log")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            rep_date = st.date_input("Select Report Date", datetime.now().date(), key="rep_daily_date")
            date_str = rep_date.strftime("%Y-%m-%d")
        with col_d2:
            rep_dept = st.selectbox("Department (Optional)", ["All"] + DEPARTMENTS, key="rep_daily_dept")

        # Compile report data
        daily_records = attendance.get(date_str, {})
        
        report_rows = []
        for s_id, s_data in students.items():
            # Apply department filter
            if rep_dept != "All" and s_data.get("department") != rep_dept:
                continue
                
            status_entry = daily_records.get(s_id, {})
            status = status_entry.get("status", "Not Marked")
            notes = status_entry.get("notes", "")
            time_marked = status_entry.get("timestamp", "")
            if time_marked:
                try:
                    time_marked = datetime.fromisoformat(time_marked).strftime("%H:%M:%S")
                except:
                    pass
            
            report_rows.append({
                "Student ID": s_id,
                "Name": s_data.get("name"),
                "Roll Number": s_data.get("roll_number"),
                "Department": s_data.get("department"),
                "Semester": s_data.get("semester"),
                "Section": s_data.get("section"),
                "Status": status,
                "Time Marked": time_marked,
                "Remarks": notes
            })

        df_daily = pd.DataFrame(report_rows)
        
        if df_daily.empty:
            st.warning("No records match the applied criteria.")
        else:
            st.dataframe(df_daily, use_container_width=True, hide_index=True)
            
            # Downloads Section
            st.markdown("### Export options")
            c1, c2, c3 = st.columns(3)
            
            filename_base = f"daily_report_{date_str}_{rep_dept.replace(' ', '_')}"
            csv_path = REPORTS_DIR / f"{filename_base}.csv"
            xlsx_path = REPORTS_DIR / f"{filename_base}.xlsx"
            pdf_path = REPORTS_DIR / f"{filename_base}.pdf"

            with c1:
                if export_to_csv(report_rows, csv_path):
                    with open(csv_path, "rb") as f:
                        st.download_button(
                            "📥 Download CSV",
                            data=f.read(),
                            file_name=csv_path.name,
                            mime="text/csv",
                            use_container_width=True
                        )
            with c2:
                if export_to_excel(report_rows, xlsx_path):
                    with open(xlsx_path, "rb") as f:
                        st.download_button(
                            "📥 Download Excel",
                            data=f.read(),
                            file_name=xlsx_path.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
            with c3:
                pdf_headers = ["ID", "Name", "Roll No", "Dept", "Sem", "Sec", "Status", "Time", "Remarks"]
                pdf_data = [
                    [row["Student ID"], row["Name"], row["Roll Number"], row["Department"][:10], row["Semester"][:4], row["Section"], row["Status"], row["Time Marked"], row["Remarks"]]
                    for row in report_rows
                ]
                if export_to_pdf(f"Daily Attendance Report ({date_str})", pdf_headers, pdf_data, pdf_path, f"Department: {rep_dept}"):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "📥 Download PDF",
                            data=f.read(),
                            file_name=pdf_path.name,
                            mime="application/pdf",
                            use_container_width=True
                        )

    # ==========================================
    # TAB 2: WEEKLY SUMMARY
    # ==========================================
    with tab_weekly:
        st.subheader("📅 Weekly Attendance Summary")
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            start_date = st.date_input("Week Start Date (Monday)", datetime.now().date() - timedelta(days=datetime.now().date().weekday()), key="rep_weekly_start")
            end_date = start_date + timedelta(days=6)
            st.caption(f"Week Range: **{start_date}** to **{end_date}**")
        with col_w2:
            rep_w_dept = st.selectbox("Department", ["All"] + DEPARTMENTS, key="rep_weekly_dept")

        # Compile weekly range dates
        date_list = []
        curr = start_date
        while curr <= end_date:
            date_list.append(curr.strftime("%Y-%m-%d"))
            curr += timedelta(days=1)

        weekly_rows = []
        for s_id, s_data in students.items():
            if rep_w_dept != "All" and s_data.get("department") != rep_w_dept:
                continue
                
            total_days = 0
            present_days = 0
            absent_days = 0
            late_days = 0
            
            for d in date_list:
                day_records = attendance.get(d, {})
                if s_id in day_records:
                    total_days += 1
                    status = day_records[s_id].get("status")
                    if status == "Present":
                        present_days += 1
                    elif status == "Absent":
                        absent_days += 1
                    elif status == "Late":
                        late_days += 1

            att_rate = ((present_days + late_days) / total_days * 100) if total_days > 0 else 0.0
            
            weekly_rows.append({
                "Student ID": s_id,
                "Name": s_data.get("name"),
                "Roll Number": s_data.get("roll_number"),
                "Department": s_data.get("department"),
                "Total Marked": total_days,
                "Present": present_days,
                "Absent": absent_days,
                "Late": late_days,
                "Attendance Rate": f"{att_rate:.1f}%"
            })

        df_weekly = pd.DataFrame(weekly_rows)
        
        if df_weekly.empty:
            st.warning("No records match the applied criteria.")
        else:
            st.dataframe(df_weekly, use_container_width=True, hide_index=True)
            
            # Downloads Section
            st.markdown("### Export options")
            c1, c2, c3 = st.columns(3)
            
            filename_base = f"weekly_report_{start_date}_{end_date}"
            csv_path = REPORTS_DIR / f"{filename_base}.csv"
            xlsx_path = REPORTS_DIR / f"{filename_base}.xlsx"
            pdf_path = REPORTS_DIR / f"{filename_base}.pdf"

            with c1:
                if export_to_csv(weekly_rows, csv_path):
                    with open(csv_path, "rb") as f:
                        st.download_button("📥 Download CSV", csv_path.read_bytes(), file_name=csv_path.name, mime="text/csv", use_container_width=True, key="dl_csv_w")
            with c2:
                if export_to_excel(weekly_rows, xlsx_path):
                    with open(xlsx_path, "rb") as f:
                        st.download_button("📥 Download Excel", xlsx_path.read_bytes(), file_name=xlsx_path.name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="dl_xlsx_w")
            with c3:
                pdf_headers = ["ID", "Name", "Roll No", "Total", "Pres", "Abs", "Late", "Rate"]
                pdf_data = [
                    [row["Student ID"], row["Name"], row["Roll Number"], str(row["Total Marked"]), str(row["Present"]), str(row["Absent"]), str(row["Late"]), row["Attendance Rate"]]
                    for row in weekly_rows
                ]
                if export_to_pdf(f"Weekly Attendance Report", pdf_headers, pdf_data, pdf_path, f"Period: {start_date} to {end_date} | Department: {rep_w_dept}"):
                    with open(pdf_path, "rb") as f:
                        st.download_button("📥 Download PDF", f.read(), file_name=pdf_path.name, mime="application/pdf", use_container_width=True, key="dl_pdf_w")

    # ==========================================
    # TAB 3: MONTHLY ATTENDANCE MATRIX
    # ==========================================
    with tab_monthly:
        st.subheader("📅 Monthly Percentage Matrix")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            current_month_idx = datetime.now().month - 1
            selected_month_name = st.selectbox("Select Month", months_list, index=current_month_idx)
            selected_month_val = months_list.index(selected_month_name) + 1
        with col_m2:
            selected_year = st.selectbox("Select Year", [2026, 2027, 2028], index=0)
        with col_m3:
            rep_m_dept = st.selectbox("Department", ["All"] + DEPARTMENTS, key="rep_monthly_dept")

        # Compile monthly metrics
        monthly_rows = []
        for s_id, s_data in students.items():
            if rep_m_dept != "All" and s_data.get("department") != rep_m_dept:
                continue
                
            total_days = 0
            present_days = 0
            absent_days = 0
            late_days = 0
            
            for date_k, daily_recs in attendance.items():
                try:
                    dt = datetime.strptime(date_k, "%Y-%m-%d")
                    if dt.month == selected_month_val and dt.year == selected_year:
                        if s_id in daily_recs:
                            total_days += 1
                            status = daily_recs[s_id].get("status")
                            if status == "Present":
                                present_days += 1
                            elif status == "Absent":
                                absent_days += 1
                            elif status == "Late":
                                late_days += 1
                except ValueError:
                    pass

            att_rate = ((present_days + late_days) / total_days * 100) if total_days > 0 else 0.0
            
            monthly_rows.append({
                "Student ID": s_id,
                "Name": s_data.get("name"),
                "Roll Number": s_data.get("roll_number"),
                "Department": s_data.get("department"),
                "Total Marked": total_days,
                "Present": present_days,
                "Absent": absent_days,
                "Late": late_days,
                "Attendance Rate": f"{att_rate:.1f}%"
            })

        df_monthly = pd.DataFrame(monthly_rows)
        
        if df_monthly.empty:
            st.warning("No records match the applied criteria.")
        else:
            st.dataframe(df_monthly, use_container_width=True, hide_index=True)
            
            # Downloads Section
            st.markdown("### Export options")
            c1, c2, c3 = st.columns(3)
            
            filename_base = f"monthly_report_{selected_year}_{selected_month_val}"
            csv_path = REPORTS_DIR / f"{filename_base}.csv"
            xlsx_path = REPORTS_DIR / f"{filename_base}.xlsx"
            pdf_path = REPORTS_DIR / f"{filename_base}.pdf"

            with c1:
                if export_to_csv(monthly_rows, csv_path):
                    with open(csv_path, "rb") as f:
                        st.download_button("📥 Download CSV", csv_path.read_bytes(), file_name=csv_path.name, mime="text/csv", use_container_width=True, key="dl_csv_m")
            with c2:
                if export_to_excel(monthly_rows, xlsx_path):
                    with open(xlsx_path, "rb") as f:
                        st.download_button("📥 Download Excel", xlsx_path.read_bytes(), file_name=xlsx_path.name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="dl_xlsx_m")
            with c3:
                pdf_headers = ["ID", "Name", "Roll No", "Total", "Pres", "Abs", "Late", "Rate"]
                pdf_data = [
                    [row["Student ID"], row["Name"], row["Roll Number"], str(row["Total Marked"]), str(row["Present"]), str(row["Absent"]), str(row["Late"]), row["Attendance Rate"]]
                    for row in monthly_rows
                ]
                if export_to_pdf(f"Monthly Attendance Report", pdf_headers, pdf_data, pdf_path, f"Period: {selected_month_name} {selected_year} | Department: {rep_m_dept}"):
                    with open(pdf_path, "rb") as f:
                        st.download_button("📥 Download PDF", f.read(), file_name=pdf_path.name, mime="application/pdf", use_container_width=True, key="dl_pdf_m")

    # ==========================================
    # TAB 4: INDIVIDUAL STUDENT REPORT
    # ==========================================
    with tab_student:
        st.subheader("👤 Individual Student Summary")
        
        # Selection
        student_options = {f"{data['name']} ({data['roll_number']})": s_id for s_id, data in students.items()}
        selected_student_label = st.selectbox("Select Student for Detail Profile", list(student_options.keys()), key="rep_stud_sel")
        sel_s_id = student_options[selected_student_label]
        
        s_data = students[sel_s_id]

        # Extract history for student
        hist_rows = []
        total_days = 0
        present_days = 0
        absent_days = 0
        late_days = 0

        # Sort dates
        sorted_dates = sorted(attendance.keys())
        for d in sorted_dates:
            day_records = attendance[d]
            if sel_s_id in day_records:
                total_days += 1
                status = day_records[sel_s_id].get("status")
                notes = day_records[sel_s_id].get("notes", "")
                
                if status == "Present":
                    present_days += 1
                elif status == "Absent":
                    absent_days += 1
                elif status == "Late":
                    late_days += 1

                # Try to parse day of week
                try:
                    dt = datetime.strptime(d, "%Y-%m-%d")
                    day_name = dt.strftime("%A")
                except:
                    day_name = ""
                    
                hist_rows.append({
                    "Date": d,
                    "Day": day_name,
                    "Status": status,
                    "Remarks": notes
                })

        rate = (present_days + late_days) / total_days * 100 if total_days > 0 else 0.0

        # Render Student Stats
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Days Logged", total_days)
        col_m2.metric("Present Days", present_days)
        col_m3.metric("Absent / Late", f"{absent_days} / {late_days}")
        col_m4.metric("Attendance Rate", f"{rate:.1f}%")

        df_hist = pd.DataFrame(hist_rows)
        
        if df_hist.empty:
            st.warning("No attendance records found logged for this student.")
        else:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
            
            # Downloads Section
            st.markdown("### Export options")
            c1, c2, c3 = st.columns(3)
            
            filename_base = f"student_report_{s_data.get('roll_number')}"
            csv_path = REPORTS_DIR / f"{filename_base}.csv"
            xlsx_path = REPORTS_DIR / f"{filename_base}.xlsx"
            pdf_path = REPORTS_DIR / f"{filename_base}.pdf"

            with c1:
                if export_to_csv(hist_rows, csv_path):
                    with open(csv_path, "rb") as f:
                        st.download_button("📥 Download CSV", csv_path.read_bytes(), file_name=csv_path.name, mime="text/csv", use_container_width=True, key="dl_csv_s")
            with c2:
                if export_to_excel(hist_rows, xlsx_path):
                    with open(xlsx_path, "rb") as f:
                        st.download_button("📥 Download Excel", xlsx_path.read_bytes(), file_name=xlsx_path.name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="dl_xlsx_s")
            with c3:
                pdf_headers = ["Date", "Day of Week", "Status", "Remarks"]
                pdf_data = [
                    [row["Date"], row["Day"], row["Status"], row["Remarks"]]
                    for row in hist_rows
                ]
                if export_to_pdf(f"Student Attendance History", pdf_headers, pdf_data, pdf_path, f"Name: {s_data.get('name')} | Roll No: {s_data.get('roll_number')}"):
                    with open(pdf_path, "rb") as f:
                        st.download_button("📥 Download PDF", f.read(), file_name=pdf_path.name, mime="application/pdf", use_container_width=True, key="dl_pdf_s")
