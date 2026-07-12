# Global constants for the Attendance Management System

DEPARTMENTS = [
    "Computer Science & Engineering",
    "Information Technology",
    "Electronics & Communication Engineering",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Business Administration",
    "Basic Sciences"
]

SEMESTERS = [
    "1st Semester",
    "2nd Semester",
    "3rd Semester",
    "4th Semester",
    "5th Semester",
    "6th Semester",
    "7th Semester",
    "8th Semester"
]

SECTIONS = ["A", "B", "C", "D"]

# UI Themes
THEMES = ["Dark", "Light"]

# Session State Keys
SESSION_USER_KEY = "authenticated_user"
SESSION_AUTHENTICATED = "is_authenticated"
SESSION_THEME = "ui_theme"
SESSION_CURRENT_PAGE = "current_page"

# Database defaults
DEFAULT_ADMIN_USER = {
    "username": "admin",
    "name": "System Administrator",
    "email": "admin@school.com",
    "role": "Admin"
}
