import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any


TEACHERS_FILE = Path(__file__).with_name("teachers.json")
SESSION_COOKIE_NAME = "teacher_session"
SESSION_MAX_AGE = 8 * 60 * 60
SESSION_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_urlsafe(32)
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def load_teacher_records(path: Path = TEACHERS_FILE) -> dict[str, Any]:
    if not path.exists():
        return {"teachers": []}

    with path.open(encoding="utf-8") as teachers_file:
        data = json.load(teachers_file)

    if not isinstance(data, dict) or not isinstance(data.get("teachers"), list):
        raise ValueError("Teacher file must contain a teachers list")
    if any(not isinstance(teacher, dict) for teacher in data["teachers"]):
        raise ValueError("Each teacher record must be an object")
    return data


def create_password_record(password: str) -> dict[str, str]:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    )
    return {"salt": salt.hex(), "password_hash": password_hash.hex()}


def verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(expected_hash_hex)
        actual_hash = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
        )
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(actual_hash, expected_hash)


def authenticate_teacher(
    username: str,
    password: str,
    path: Path = TEACHERS_FILE,
) -> str | None:
    if not isinstance(username, str):
        return None

    for teacher in load_teacher_records(path)["teachers"]:
        stored_username = teacher.get("username", "")
        if isinstance(stored_username, str) and hmac.compare_digest(
            stored_username.encode("utf-8"), username.encode("utf-8")
        ):
            if verify_password(password, teacher.get("salt", ""), teacher.get("password_hash", "")):
                return stored_username
            return None
    return None


def create_session_token(username: str, now: int | None = None) -> str:
    issued_at = int(time.time()) if now is None else now
    payload = json.dumps(
        {"username": username, "expires_at": issued_at + SESSION_MAX_AGE},
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{encoded_payload}.{encoded_signature}"


def verify_session_token(token: str | None, now: int | None = None) -> str | None:
    if not token or "." not in token:
        return None

    encoded_payload, encoded_signature = token.split(".", 1)
    expected_signature = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    try:
        supplied_signature = base64.urlsafe_b64decode(encoded_signature + "=" * (-len(encoded_signature) % 4))
        payload = base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4))
        session = json.loads(payload)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    if not isinstance(session, dict):
        return None

    if not hmac.compare_digest(expected_signature, supplied_signature):
        return None

    current_time = int(time.time()) if now is None else now
    username = session.get("username")
    expires_at = session.get("expires_at")
    if not isinstance(username, str) or not isinstance(expires_at, int) or expires_at <= current_time:
        return None
    return username


def get_session_username(
    token: str | None,
    path: Path = TEACHERS_FILE,
    now: int | None = None,
) -> str | None:
    username = verify_session_token(token, now)
    if username is None:
        return None

    for teacher in load_teacher_records(path)["teachers"]:
        stored_username = teacher.get("username", "")
        if isinstance(stored_username, str) and hmac.compare_digest(
            stored_username.encode("utf-8"), username.encode("utf-8")
        ):
            return username
    return None