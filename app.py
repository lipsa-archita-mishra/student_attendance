import streamlit as st
from pathlib import Path
from streamlit_option_menu import option_menu

# Set page config FIRST before imports or actions
st.set_page_config(
    page_title="Attendance Management System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Core imports
from utils.db import init_db, get_settings
from utils.auth import authenticate_user
from utils.logger import log_event

# Page view imports
from pages.dashboard import show_dashboard
from pages.students import show_students_page
from pages.attendance import show_attendance_page
from pages.reports import show_reports_page
from pages.analytics import show_analytics_page
from pages.settings import show_settings_page
from pages.profile import show_profile_page
from pages.help_about import show_help_page

# Inject Global Modern CSS
def inject_custom_css():
    """
    Injects custom styles for glassmorphism, shadows, custom metric fonts,
    and responsive button structures to elevate visual appeal.
    """
    settings = st.session_state.get("settings", {})
    theme = settings.get("theme", "Dark")
    
    # Custom colors depending on settings theme
    if theme == "Dark":
        bg_card = "rgba(255, 255, 255, 0.05)"
        border_card = "rgba(255, 255, 255, 0.1)"
        font_color = "#F3F4F6"
    else:
        bg_card = "rgba(0, 0, 0, 0.02)"
        border_card = "rgba(0, 0, 0, 0.08)"
        font_color = "#1F2937"

    custom_css = f"""
    <style>
        /* CSS variables and global overrides */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Outfit', sans-serif;
        }}
        
        /* Glassmorphism styling wrapper classes */
        .glass-card {{
            background: {bg_card};
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 16px;
            border: 1px solid {border_card};
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            color: {font_color};
        }}
        
        /* Make standard Streamlit card borders clean */
        div[data-testid="stMetricValue"] {{
            font-weight: 700 !important;
            font-size: 2.2rem !important;
        }}
        
        /* Round buttons style */
        .stButton>button {{
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease-in-out !important;
        }}
        .stButton>button:hover {{
            transform: scale(1.02);
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def render_login_view():
    """
    Renders a centered login layout for unauthenticated sessions.
    """
    # Centering columns
    _, col_center, _ = st.columns([1, 1.5, 1])
    
    with col_center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0;">🏫 Student Portal</h1>
            <p style="color: #6B7280; font-size: 1.1rem; margin-top: 5px;">Attendance Management System</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Wrapping in a styled frame
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Login Credentials")
            
            username = st.text_input("Username").strip()
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Keep me logged in")
            
            st.write("")
            if st.button("Access Dashboard", type="primary", use_container_width=True):
                if not username or not password:
                    st.error("Please fill in all credential fields.")
                else:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.is_authenticated = True
                        st.session_state.authenticated_user = user
                        st.success("Access Granted! Loading system parameters...")
                        st.rerun()
                    else:
                        st.error("Incorrect username or password. Check credentials.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Default guide info
            st.info("🔑 **Default Account**: Username: `admin` | Password: `admin123`")

def main():
    # 1. Initialize databases and structure if missing
    init_db()
    
    # 2. Setup Session states
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "authenticated_user" not in st.session_state:
        st.session_state.authenticated_user = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"
        
    # Sync settings into session state
    if "settings" not in st.session_state:
        st.session_state.settings = get_settings()

    # Apply style themes
    inject_custom_css()

    # 3. Route Views based on authentication
    if not st.session_state.is_authenticated:
        render_login_view()
    else:
        # Load sidebar navigation
        user = st.session_state.authenticated_user
        
        # User details card in sidebar
        with st.sidebar:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 25px;
                color: white;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            ">
                <div style="font-size: 1.2rem; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    👤 {user.get('name')}
                </div>
                <div style="font-size: 0.8rem; font-weight: 500; opacity: 0.8; margin-top: 4px;">
                    🔓 {user.get('role')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Option Menu layout
            menu_selection = option_menu(
                menu_title="Main Navigation",
                options=[
                    "Dashboard", "Students", "Attendance", "Reports", 
                    "Analytics", "Settings", "My Profile", "Help & About", "Sign Out"
                ],
                icons=[
                    "house", "people", "check-square", "file-earmark-bar-graph", 
                    "graph-up", "gear", "person-circle", "info-circle", "box-arrow-right"
                ],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "transparent"},
                    "icon": {"color": "#8B5CF6", "font-size": "1rem"},
                    "nav-link": {"font-size": "0.95rem", "text-align": "left", "margin": "0px", "--hover-color": "rgba(255,255,255,0.08)"},
                    "nav-link-selected": {"background-color": "#4F46E5"},
                }
            )

        # Route main views
        if menu_selection == "Sign Out":
            log_event("logout", f"User '{user.get('username')}' logged out.", user.get("username"))
            # Reset authentication session state keys
            st.session_state.is_authenticated = False
            st.session_state.authenticated_user = None
            st.session_state.current_page = "Dashboard"
            st.rerun()
            
        # Dynamically set page if selection is clicked
        if menu_selection != "Sign Out":
            st.session_state.current_page = menu_selection

        # Render chosen page
        current_page = st.session_state.current_page
        
        if current_page == "Dashboard":
            show_dashboard()
        elif current_page == "Students":
            show_students_page()
        elif current_page == "Attendance":
            show_attendance_page()
        elif current_page == "Reports":
            show_reports_page()
        elif current_page == "Analytics":
            show_analytics_page()
        elif current_page == "Settings":
            show_settings_page()
        elif current_page == "My Profile":
            show_profile_page()
        elif current_page == "Help & About":
            show_help_page()

if __name__ == "__main__":
    main()
