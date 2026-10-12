import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

from teacher_auth import (
    SESSION_MAX_AGE,
    authenticate_teacher,
    create_password_record,
    create_session_token,
    get_session_username,
    verify_session_token,
)
from app import activities, signup_for_activity, unregister_from_activity


class TeacherAuthTests(unittest.TestCase):
    def setUp(self):
        self.request = Request({
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [],
            "query_string": b"",
        })

    def test_teacher_password_is_verified_without_storing_plaintext(self):
        record = create_password_record("correct horse battery staple")
        with tempfile.TemporaryDirectory() as directory:
            teachers_path = Path(directory) / "teachers.json"
            teachers_path.write_text(
                json.dumps({"teachers": [{"username": "teacher1", **record}]}),
                encoding="utf-8",
            )

            self.assertEqual(
                authenticate_teacher("teacher1", "correct horse battery staple", teachers_path),
                "teacher1",
            )
            self.assertIsNone(authenticate_teacher("teacher1", "wrong password", teachers_path))

    def test_session_requires_valid_signature_and_expiration(self):
        token = create_session_token("teacher1", now=1000)

        self.assertEqual(verify_session_token(token, now=1001), "teacher1")
        self.assertIsNone(verify_session_token(token, now=1000 + SESSION_MAX_AGE))

        payload, signature = token.split(".")
        tampered_token = f"{payload}.{signature[:-1]}x"
        self.assertIsNone(verify_session_token(tampered_token, now=1001))

    def test_removed_teacher_cannot_keep_using_existing_session(self):
        token = create_session_token("teacher1", now=1000)
        with tempfile.TemporaryDirectory() as directory:
            teachers_path = Path(directory) / "teachers.json"
            teachers_path.write_text('{"teachers":[]}', encoding="utf-8")

            self.assertIsNone(get_session_username(token, teachers_path, now=1001))

    def test_anonymous_users_cannot_register_or_unregister(self):
        with self.assertRaises(HTTPException) as signup_error:
            signup_for_activity("Chess Club", "new-student@mergington.edu", self.request)
        self.assertEqual(signup_error.exception.status_code, 401)

        with self.assertRaises(HTTPException) as unregister_error:
            unregister_from_activity("Chess Club", "michael@mergington.edu", self.request)
        self.assertEqual(unregister_error.exception.status_code, 401)

    def test_teacher_can_register_and_unregister(self):
        email = "admin-mode-test@mergington.edu"
        with patch("app.get_session_username", return_value="teacher1"):
            signup_for_activity("Chess Club", email, self.request)
            self.assertIn(email, activities["Chess Club"]["participants"])
            unregister_from_activity("Chess Club", email, self.request)

        self.assertNotIn(email, activities["Chess Club"]["participants"])


if __name__ == "__main__":
    unittest.main()