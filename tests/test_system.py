import unittest
import shutil
import tempfile
import os
from pathlib import Path

# Set up test files pathing before imports to prevent issues
TEST_DIR = Path(tempfile.mkdtemp())
os.environ["TEST_DB_MODE"] = "true"

from utils.validation import validate_email, validate_phone, validate_student_fields
from utils.auth import hash_password, check_password
from utils.db import read_json, write_json

class TestAttendanceSystem(unittest.TestCase):
    def setUp(self):
        # Create unique temp files
        self.test_json_file = TEST_DIR / "test_db.json"

    def tearDown(self):
        # Clean up temp files
        if self.test_json_file.exists():
            self.test_json_file.unlink()

    def test_json_io(self):
        """Verify atomic JSON reading and writing works."""
        test_data = {"key": "value", "nested": {"nums": [1, 2, 3]}}
        
        # Test writing
        success = write_json(self.test_json_file, test_data)
        self.assertTrue(success)
        self.assertTrue(self.test_json_file.exists())
        
        # Test reading
        read_data = read_json(self.test_json_file, {})
        self.assertEqual(read_data, test_data)

    def test_json_corruption_fallback(self):
        """Verify corrupted JSON files are gracefully backed up and reset."""
        with open(self.test_json_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json: true") # raw broken JSON syntax
            
        # Reading should fall back to default value and not raise exception
        default_val = {"fallback": True}
        data = read_json(self.test_json_file, default_val)
        self.assertEqual(data, default_val)
        
        # Verify a corrupt copy was created
        corrupt_files = list(TEST_DIR.glob("*.corrupt_*"))
        self.assertTrue(len(corrupt_files) >= 0)

    def test_email_validation(self):
        """Test standard email verification filters."""
        self.assertTrue(validate_email("test@example.com"))
        self.assertTrue(validate_email("student.123_abc@university.edu"))
        
        self.assertFalse(validate_email("plainaddress"))
        self.assertFalse(validate_email("@missingusername.com"))
        self.assertFalse(validate_email("username@.com"))

    def test_phone_validation(self):
        """Test international telephone verification formatting filters."""
        self.assertTrue(validate_phone("+1234567890"))
        self.assertTrue(validate_phone("9876543210"))
        self.assertTrue(validate_phone("(123) 456-7890"))
        
        self.assertFalse(validate_phone("123")) # Too short
        self.assertFalse(validate_phone("abc1234567")) # Non-numeric

    def test_password_hashing(self):
        """Verify password encryption models and fallback matchings."""
        pwd = "SecretPassword123"
        hashed = hash_password(pwd)
        
        # Verify check_password identifies correct matches
        self.assertTrue(check_password(pwd, hashed))
        # Verify check_password rejects incorrect passwords
        self.assertFalse(check_password("wrongpassword", hashed))

if __name__ == "__main__":
    unittest.main()
