import streamlit as st
from typing import Any

def render_metric_card(
    label: str,
    value: Any,
    icon: str = "📊",
    color_gradient: str = "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
    text_color: str = "#FFFFFF"
):
    """
    Renders a premium visual card for statistics.
    """
    card_html = f"""
    <div style="
        background: {color_gradient};
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        color: {text_color};
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        transition: transform 0.2s ease-in-out;
    " onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size: 3rem; margin-right: 20px; line-height: 1;">
            {icon}
        </div>
        <div>
            <div style="font-size: 0.9rem; font-weight: 500; opacity: 0.85; text-transform: uppercase; letter-spacing: 0.5px;">
                {label}
            </div>
            <div style="font-size: 2rem; font-weight: 700; margin-top: 4px; line-height: 1;">
                {value}
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_kpi_dashboard(
    total_students: int,
    present_today: int,
    absent_today: int,
    late_today: int,
    attendance_rate: float
):
    """
    Renders a standard 4-column metrics dashboard.
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_metric_card(
            label="Total Students",
            value=total_students,
            icon="👥",
            color_gradient="linear-gradient(135deg, #4F46E5 0%, #3730A3 100%)" # Indigo
        )
    with col2:
        render_metric_card(
            label="Present Today",
            value=present_today,
            icon="✅",
            color_gradient="linear-gradient(135deg, #10B981 0%, #065F46 100%)" # Emerald
        )
    with col3:
        render_metric_card(
            label="Absent / Late Today",
            value=f"{absent_today} / {late_today}",
            icon="⚠️",
            color_gradient="linear-gradient(135deg, #F59E0B 0%, #92400E 100%)" # Amber
        )
    with col4:
        render_metric_card(
            label="Attendance Rate",
            value=f"{attendance_rate:.1f}%",
            icon="📈",
            color_gradient="linear-gradient(135deg, #EC4899 0%, #9D174D 100%)" # Pink
        )
