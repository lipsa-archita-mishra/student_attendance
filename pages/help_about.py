import streamlit as st

def show_help_page():
    st.title("ℹ️ Help & About Portal")
    st.markdown("User guides, technical specs, licensing details, and version histories.")
    st.markdown("---")

    # Grid columns
    col_guide, col_tech = st.columns(2)

    with col_guide:
        st.markdown("""
        ### 📖 User Guide
        
        #### 1. Managing Students
        Navigate to the **Students** tab:
        - **Directory**: Displays list of students. Use filter headers or search bars to isolate cards.
        - **Register Student**: Input details, assign unique ID & roll codes, upload profile photos, and submit.
        - **Manage Student Profile**: Look up a profile, perform details edits, or delete records.
        
        #### 2. Recording Attendance
        Navigate to the **Attendance** tab:
        - Select target date, department, semester, and section.
        - Grid auto-populates. Update **Status** cells (Present, Absent, Late) or add notes.
        - Click **Save Attendance Registry** to submit updates.
        
        #### 3. Compiling Reports
        Navigate to the **Reports** tab:
        - Generate Daily, Weekly, Monthly, or Individual student history logs.
        - Click download buttons to export templates as **CSV**, **Excel**, or **PDF**.
        """)

    with col_tech:
        st.markdown("""
        ### 🛠️ Technical Specifications
        
        - **Software Core**: Streamlit Framework (Python)
        - **Data Model Engine**: Pydantic v2
        - **Database**: Atomic Flat File JSON Storage
        - **Plot Rendering Engine**: Plotly Express Charts
        - **PDF Engine**: ReportLab Flowable Canvas
        - **Excel Engine**: OpenPyXL
        - **Logger Framework**: Loguru (Console + Local Files)
        - **Password Security**: Bcrypt (fallback to PBKDF2)
        - **System Version**: `v1.0.0-release`
        
        ### 👨‍💻 System Architecture
        All files are loaded and written atomically via Python's filesystem wrapper routines. File locks are resolved sequentially to prevent race condition write crashes.
        
        ### 📜 License
        Open-sourced under the **MIT License**. Free to adapt for academic coursework and professional portfolios.
        """)
