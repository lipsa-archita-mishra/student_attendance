import hashlib
import os
import secrets
from typing import Optional, Dict, Any
from utils.db import get_all_users, save_users
from utils.logger import log_event, logger

# Attempt to import bcrypt for production-level hashing, fallback to hashlib PBKDF2 if missing
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    logger.warning("bcrypt module not found. Falling back to built-in hashlib PBKDF2 for password hashing.")
    HAS_BCRYPT = False

def hash_password(password: str) -> str:
    """
    Hashes a password. Uses bcrypt if available, otherwise falls back to PBKDF2-HMAC-SHA256.
    """
    if HAS_BCRYPT:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return f"bcrypt:${hashed.decode('utf-8')}"
    else:
        # Fallback to PBKDF2
        salt = secrets.token_hex(16)
        iterations = 100000
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        return f"pbkdf2:${salt}:${iterations}:${key.hex()}"

def check_password(password: str, hashed: str) -> bool:
    """
    Verifies a password against its stored hash.
    Supports verifying both bcrypt and PBKDF2 hashes.
    """
    try:
        if hashed.startswith("bcrypt:$"):
            if not HAS_BCRYPT:
                logger.error("Bcrypt is required to verify this password, but bcrypt package is missing.")
                return False
            raw_hash = hashed.replace("bcrypt:$", "", 1).encode('utf-8')
            return bcrypt.checkpw(password.encode('utf-8'), raw_hash)
            
        elif hashed.startswith("pbkdf2:$"):
            parts = hashed.split(":$")
            if len(parts) != 4:
                return False
            _, salt, iterations_str, key_hex = parts
            iterations = int(iterations_str)
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                iterations
            )
            return key.hex() == key_hex
            
        else:
            # Fallback for plain sha256 (old/raw hashes if any) or unhashed comparison for migration
            # Let's support verifying a raw SHA-256 just in case, but keep it secure.
            # If the hash is plain text (not recommended, but let's check)
            return password == hashed
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticates a user against the user database.
    Returns the user dictionary if successful, None otherwise.
    """
    users = get_all_users()
    user = users.get(username.strip().lower())
    if not user:
        log_event("login_failed", f"Failed login attempt: Username '{username}' does not exist.")
        return None
        
    stored_hash = user.get("password_hash")
    if check_password(password, stored_hash):
        log_event("login_success", f"User '{username}' logged in successfully.", username)
        return {
            "username": user["username"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    else:
        log_event("login_failed", f"Failed login attempt: Incorrect password for user '{username}'.")
        return None

def change_user_password(username: str, new_password: str, actor: str) -> bool:
    """
    Updates the password for a user.
    """
    users = get_all_users()
    user_key = username.strip().lower()
    if user_key not in users:
        logger.error(f"Cannot change password: User '{username}' does not exist.")
        return False
        
    hashed = hash_password(new_password)
    users[user_key]["password_hash"] = hashed
    if save_users(users):
        log_event("password_changed", f"Password changed for user '{username}'.", actor)
        return True
    return False

def register_user(username: str, password: str, name: str, email: str, role: str = "Admin", actor: str = "system") -> bool:
    """
    Registers a new user inside the database.
    """
    users = get_all_users()
    user_key = username.strip().lower()
    if user_key in users:
        logger.warning(f"Registration failed: User '{username}' already exists.")
        return False
        
    hashed = hash_password(password)
    users[user_key] = {
        "username": username,
        "password_hash": hashed,
        "name": name,
        "email": email,
        "role": role
    }
    
    if save_users(users):
        log_event("user_registered", f"New user '{username}' ({role}) registered.", actor)
        return True
    return False
