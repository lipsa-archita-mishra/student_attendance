import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import log_event, logger

DATA_DIR = Path("data")
BACKUPS_DIR = DATA_DIR / "backups"
UPLOADS_DIR = Path("uploads")
REPORTS_DIR = Path("reports")

# Ensure base folders exist
for folder in [DATA_DIR, BACKUPS_DIR, UPLOADS_DIR, REPORTS_DIR]:
    folder.mkdir(exist_ok=True)

# File Paths
STUDENTS_FILE = DATA_DIR / "students.json"
ATTENDANCE_FILE = DATA_DIR / "attendance.json"
USERS_FILE = DATA_DIR / "users.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

def read_json(filepath: Path, default_val: Any) -> Any:
    """
    Safely reads a JSON file. If it doesn't exist, it creates it with default_val.
    If it's corrupted, it backs up the corrupted version and resets the file.
    """
    if not filepath.exists():
        write_json(filepath, default_val)
        return default_val

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error in {filepath.name}: {e}. Backing up corrupted file and resetting.")
        # Backup corrupted file
        corrupt_backup = filepath.with_suffix(f".corrupt_{int(datetime.now().timestamp())}")
        try:
            shutil.copy2(filepath, corrupt_backup)
            logger.info(f"Corrupted file backed up to {corrupt_backup.name}")
        except Exception as copy_err:
            logger.error(f"Failed to backup corrupted file: {copy_err}")
        
        # Reset file
        write_json(filepath, default_val)
        return default_val
    except Exception as e:
        logger.error(f"Unexpected error reading {filepath.name}: {e}")
        return default_val

def write_json(filepath: Path, data: Any) -> bool:
    """
    Writes data to a JSON file atomically using a temporary file.
    """
    temp_filepath = filepath.with_suffix(".tmp")
    try:
        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Rename is atomic on most platforms
        if filepath.exists():
            os.remove(filepath)
        os.rename(temp_filepath, filepath)
        return True
    except Exception as e:
        logger.error(f"Failed writing to {filepath.name}: {e}")
        if temp_filepath.exists():
            os.remove(temp_filepath)
        return False

# Database Initialization
def init_db():
    """Initializes all data files if they do not exist or are empty."""
    from utils.auth import hash_password
    
    # 1. Initialize Settings
    from config.constants import DEFAULT_ADMIN_USER
    read_json(SETTINGS_FILE, {
        "institution_name": "Antigravity Institute of Technology",
        "academic_year": "2026-2027",
        "theme": "Dark",
        "backup_frequency": "Manual"
    })

    # 2. Initialize Students
    read_json(STUDENTS_FILE, {})

    # 3. Initialize Attendance
    read_json(ATTENDANCE_FILE, {})

    # 4. Initialize Users (Authenticators)
    users = read_json(USERS_FILE, {})
    if not users:
        # Prepopulate default admin
        default_pwd = "admin123"
        hashed = hash_password(default_pwd)
        users[DEFAULT_ADMIN_USER["username"]] = {
            "username": DEFAULT_ADMIN_USER["username"],
            "password_hash": hashed,
            "name": DEFAULT_ADMIN_USER["name"],
            "email": DEFAULT_ADMIN_USER["email"],
            "role": DEFAULT_ADMIN_USER["role"]
        }
        write_json(USERS_FILE, users)
        log_event("database_init", "Database initialized with default administrator user 'admin'.")

def get_all_students() -> Dict[str, Any]:
    return read_json(STUDENTS_FILE, {})

def save_students(students: Dict[str, Any]) -> bool:
    return write_json(STUDENTS_FILE, students)

def get_all_attendance() -> Dict[str, Any]:
    return read_json(ATTENDANCE_FILE, {})

def save_attendance(attendance: Dict[str, Any]) -> bool:
    return write_json(ATTENDANCE_FILE, attendance)

def get_all_users() -> Dict[str, Any]:
    return read_json(USERS_FILE, {})

def save_users(users: Dict[str, Any]) -> bool:
    return write_json(USERS_FILE, users)

def get_settings() -> Dict[str, Any]:
    return read_json(SETTINGS_FILE, {})

def save_settings(settings: Dict[str, Any]) -> bool:
    return write_json(SETTINGS_FILE, settings)

# Backup & Restore Engine
def create_backup(username: str = "system") -> str:
    """
    Creates a ZIP backup of the 'data/' folder (excluding the backups/ folder itself)
    and stores it in 'data/backups/'. Returns the filename of the created backup.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}"
    backup_zip_path = BACKUPS_DIR / backup_filename
    
    # We will copy the JSON files to a temporary folder and zip it, or zip them directly.
    temp_dir = DATA_DIR / f"temp_backup_{timestamp}"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Copy database JSONs
        for f in DATA_DIR.glob("*.json"):
            shutil.copy2(f, temp_dir)
        
        # Make zip archive
        shutil.make_archive(str(backup_zip_path), 'zip', root_dir=temp_dir)
        
        # Log event
        log_event("backup_created", f"System backup created: {backup_filename}.zip", username)
        return f"{backup_filename}.zip"
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        return ""
    finally:
        # Clean up temp folder
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def list_backups() -> List[str]:
    """Returns a list of available zip backups sorted by date (latest first)."""
    if not BACKUPS_DIR.exists():
        return []
    backups = [f.name for f in BACKUPS_DIR.glob("*.zip")]
    backups.sort(reverse=True)
    return backups

def restore_backup(backup_name: str, username: str = "system") -> bool:
    """
    Restores the database state from a backup ZIP file.
    """
    backup_path = BACKUPS_DIR / backup_name
    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_name}")
        return False
        
    temp_extract_dir = DATA_DIR / f"temp_restore_{int(datetime.now().timestamp())}"
    temp_extract_dir.mkdir(exist_ok=True)
    
    try:
        # Extract zip
        shutil.unpack_archive(str(backup_path), extract_dir=temp_extract_dir, format='zip')
        
        # Validate extracted files
        required_files = ["students.json", "attendance.json", "users.json", "settings.json"]
        for rf in required_files:
            file_to_check = temp_extract_dir / rf
            if not file_to_check.exists():
                raise FileNotFoundError(f"Missing essential file in backup: {rf}")
            # Try parsing JSON to verify it's clean
            with open(file_to_check, "r", encoding="utf-8") as f:
                json.load(f)
                
        # Overwrite current active database files
        for rf in required_files:
            dest = DATA_DIR / rf
            src = temp_extract_dir / rf
            if dest.exists():
                os.remove(dest)
            shutil.copy2(src, dest)
            
        log_event("backup_restored", f"System restored from backup: {backup_name}", username)
        return True
    except Exception as e:
        logger.error(f"Restore failed for backup '{backup_name}': {e}")
        return False
    finally:
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
