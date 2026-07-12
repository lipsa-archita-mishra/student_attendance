import os
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

# Ensure directories exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Configure Loguru
LOG_FILE = LOGS_DIR / "app.log"
logger.add(
    LOG_FILE,
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)

AUDIT_LOG_FILE = DATA_DIR / "logs.json"

def log_event(event_type: str, description: str, username: str = "system"):
    """
    Log an event to the main Loguru log file and append it to logs.json
    for in-app activity tracking.
    """
    message = f"[{event_type.upper()}] by User '{username}': {description}"
    logger.info(message)

    # Load existing json logs
    logs = []
    if AUDIT_LOG_FILE.exists():
        try:
            with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load logs.json: {e}")
            logs = []

    # Add new log entry
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "description": description,
        "username": username
    }
    
    # Prepend to keep latest first, cap at 1000 entries
    logs.insert(0, new_entry)
    logs = logs[:1000]

    # Write back atomically
    temp_file = AUDIT_LOG_FILE.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        if os.path.exists(AUDIT_LOG_FILE):
            os.remove(AUDIT_LOG_FILE)
        os.rename(temp_file, AUDIT_LOG_FILE)
    except Exception as e:
        logger.error(f"Failed to write to logs.json: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
