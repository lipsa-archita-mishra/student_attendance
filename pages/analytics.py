import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.db import get_all_students, get_all_attendance
from config.constants import DEPARTMENTS

def show_analytics_page():
    st.title("📈 Attendance Analytics")
    st.markdown("Interactive visualizations showing enrollment figures, daily turnouts, and performance trends.")
    st.markdown("---")

    # Load data
    students = get_all_students()
    attendance = get_all_attendance()

    if not students:
        st.info("No student data available to calculate statistics.")
        return

    if not attendance:
        st.warning("No attendance records found. Please mark attendance to enable charts.")
        return

    # Aggregate Data
    total_students = len(students)

    # 1. PIE CHART: Today's Status Distribution
    st.subheader("📊 Today's Attendance Distribution")
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_records = attendance.get(today_str, {})
    
    if not today_records:
        st.info("Today's attendance has not been registered yet. Showing distribution from the last recorded day instead.")
        # Find the latest date with records
        sorted_dates = sorted(attendance.keys(), reverse=True)
        if sorted_dates:
            target_date = sorted_dates[0]
            today_records = attendance[target_date]
            st.caption(f"Displaying data for latest recorded date: **{target_date}**")
        else:
            target_date = None
    else:
        target_date = today_str

    if today_records:
        stats = {"Present": 0, "Absent": 0, "Late": 0}
        for s_id, rec in today_records.items():
            if s_id in students: # verify student exists
                status = rec.get("status")
                if status in stats:
                    stats[status] += 1
                    
        df_pie = pd.DataFrame(list(stats.items()), columns=["Status", "Count"])
        
        # Color coding
        color_map = {
            "Present": "#10B981", # Emerald Green
            "Absent": "#EF4444",  # Red
            "Late": "#F59E0B"    # Amber
        }
        
        col_pie, col_stats = st.columns([2, 1])
        with col_pie:
            fig_pie = px.pie(
                df_pie, 
                values="Count", 
                names="Status", 
                color="Status",
                color_discrete_map=color_map,
                hole=0.4,
                title=f"Attendance Distribution on {target_date}"
            )
            # Make chart transparent background to fit theme
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_stats:
            st.markdown("#### Registry Count Details")
            p_val = stats["Present"]
            a_val = stats["Absent"]
            l_val = stats["Late"]
            total_val = p_val + a_val + l_val
            rate = (p_val + l_val) / total_val * 100 if total_val > 0 else 0
            
            st.markdown(f"""
            - **Present Students**: {p_val}
            - **Absent Students**: {a_val}
            - **Late Arrivals**: {l_val}
            - **Total Records Logged**: {total_val}
            
            **Registry Rate**: {rate:.1f}%
            """)
            st.progress(rate / 100)

    st.markdown("---")

    # 2. LINE CHART: 30-Day Attendance Rate Trend
    st.subheader("📈 30-Day Turnout Rate Trend")
    
    # Compile stats for past 30 days
    trend_data = []
    # Get last 30 dates (sorted)
    today = datetime.now().date()
    dates_30 = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
    dates_30.reverse() # past to present
    
    for d_str in dates_30:
        day_recs = attendance.get(d_str, {})
        if day_recs:
            total_rec = 0
            present_rec = 0
            late_rec = 0
            for s_id, rec in day_recs.items():
                if s_id in students:
                    total_rec += 1
                    status = rec.get("status")
                    if status == "Present":
                        present_rec += 1
                    elif status == "Late":
                        late_rec += 1
            if total_rec > 0:
                day_rate = (present_rec + late_rec) / total_rec * 100
                trend_data.append({
                    "Date": d_str,
                    "Attendance Rate (%)": round(day_rate, 1),
                    "Records Logged": total_rec
                })

    if not trend_data:
        st.info("Insufficient timeline records to generate 30-day trends.")
    else:
        df_trend = pd.DataFrame(trend_data)
        fig_trend = px.line(
            df_trend,
            x="Date",
            y="Attendance Rate (%)",
            markers=True,
            title="Daily Attendance Trend (Last 30 Days)",
            hover_data=["Records Logged"]
        )
        fig_trend.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_range=[0, 105]
        )
        fig_trend.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
        fig_trend.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
        st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # 3. BAR CHART: Department Turnout Ratios
    st.subheader("🏢 Department Comparison")
    
    # Calculate average attendance for each department over all logs
    dept_stats = {dept: {"present_late": 0, "total": 0} for dept in DEPARTMENTS}
    
    for d_str, day_recs in attendance.items():
        for s_id, rec in day_recs.items():
            if s_id in students:
                s_dept = students[s_id].get("department")
                if s_dept in dept_stats:
                    status = rec.get("status")
                    dept_stats[s_dept]["total"] += 1
                    if status in ("Present", "Late"):
                        dept_stats[s_dept]["present_late"] += 1

    dept_chart_data = []
    for dept, data in dept_stats.items():
        if data["total"] > 0:
            avg_rate = data["present_late"] / data["total"] * 100
            dept_chart_data.append({
                "Department": dept,
                "Average Turnout (%)": round(avg_rate, 1),
                "Total Logs": data["total"]
            })
            
    if not dept_chart_data:
        st.info("No logs matched any departments.")
    else:
        df_dept = pd.DataFrame(dept_chart_data)
        fig_dept = px.bar(
            df_dept,
            x="Department",
            y="Average Turnout (%)",
            color="Average Turnout (%)",
            color_continuous_scale="Viridis",
            title="Average Attendance Turnout by Department",
            hover_data=["Total Logs"]
        )
        fig_dept.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_range=[0, 105]
        )
        fig_dept.update_xaxes(tickangle=30)
        st.plotly_chart(fig_dept, use_container_width=True)
