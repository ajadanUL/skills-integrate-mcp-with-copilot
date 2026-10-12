import argparse
import getpass
import json
import os

from teacher_auth import TEACHERS_FILE, create_password_record, load_teacher_records


def main() -> int:
    parser = argparse.ArgumentParser(description="Add a teacher login to teachers.json")
    parser.add_argument("username", help="Assigned teacher username")
    args = parser.parse_args()

    username = args.username.strip()
    if not username:
        parser.error("username cannot be empty")

    try:
        records = load_teacher_records()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(f"cannot read {TEACHERS_FILE}: {error}")

    if any(teacher.get("username") == username for teacher in records["teachers"]):
        parser.error("that username already exists")

    password = getpass.getpass("Assigned password (minimum 12 characters): ")
    if len(password) < 12:
        parser.error("password must be at least 12 characters")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        parser.error("passwords do not match")

    records["teachers"].append({"username": username, **create_password_record(password)})
    temporary_file = TEACHERS_FILE.with_suffix(".json.tmp")
    temporary_file.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary_file, 0o600)
    temporary_file.replace(TEACHERS_FILE)
    print(f"Added teacher {username} to {TEACHERS_FILE}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())