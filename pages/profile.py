import streamlit as st
from utils.db import get_all_users, save_users
from utils.auth import change_user_password, check_password
from utils.logger import log_event
from utils.validation import validate_email

def show_profile_page():
    st.title("👤 My User Profile")
    st.markdown("Update your account credentials and personal contact profiles.")
    st.markdown("---")

    # Load session user
    session_user = st.session_state.get("authenticated_user")
    if not session_user:
        st.warning("No authenticated session found.")
        return

    username = session_user.get("username")
    users = get_all_users()
    user_db_data = users.get(username)

    if not user_db_data:
        st.error("Profile matching current session not found in the database.")
        return

    # Two column layout: Info updates & Password updates
    col_info, col_pwd = st.columns(2)

    with col_info:
        st.subheader("Edit Profile Information")
        
        name = st.text_input("Full Name", value=user_db_data.get("name", ""))
        email = st.text_input("Email Address", value=user_db_data.get("email", ""))
        
        st.markdown(f"""
        - **Username**: `{username}`
        - **Account Level**: `{user_db_data.get('role', 'Admin')}`
        """)
        
        if st.button("Update Profile", type="primary"):
            if not name.strip():
                st.error("Name field cannot be left blank.")
            elif not validate_email(email):
                st.error(f"Invalid email pattern: '{email}'")
            else:
                user_db_data["name"] = name.strip()
                user_db_data["email"] = email.strip()
                users[username] = user_db_data
                
                if save_users(users):
                    # Update session state cache
                    st.session_state.authenticated_user["name"] = name.strip()
                    st.session_state.authenticated_user["email"] = email.strip()
                    log_event("profile_updated", f"Updated contact info for user '{username}'.", username)
                    st.success("Profile information updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save changes to the database.")

    with col_pwd:
        st.subheader("Change System Password")
        
        current_pwd = st.text_input("Current Password", type="password", key="old_pwd_input")
        new_pwd = st.text_input("New Password", type="password", key="new_pwd_input")
        confirm_pwd = st.text_input("Confirm New Password", type="password", key="conf_pwd_input")
        
        if st.button("Update Password", type="primary"):
            # Validations
            stored_hash = user_db_data.get("password_hash")
            
            if not current_pwd:
                st.error("Please enter your current password.")
            elif not check_password(current_pwd, stored_hash):
                st.error("Current password incorrect.")
            elif len(new_pwd) < 6:
                st.error("New password must be at least 6 characters in length.")
            elif new_pwd != confirm_pwd:
                st.error("New passwords do not match.")
            else:
                # Update password
                if change_user_password(username, new_pwd, username):
                    st.success("Password changed successfully!")
                    st.balloons()
                else:
                    st.error("Failed to write password update to database.")
