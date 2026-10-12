# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Create a teacher account. The password is prompted securely and only its salted hash is saved:

   ```
   python add_teacher.py teachername
   ```

3. Set a stable session secret before running the app. For local development, generate one with:

   ```
   export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```

   For an HTTPS deployment, also set `COOKIE_SECURE=true`.

4. Run the application:

   ```
   python app.py
   ```

5. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| GET    | `/auth/session`                                                    | Check whether a teacher is signed in                                 |
| POST   | `/auth/login`                                                       | Sign in as a teacher                                                 |
| POST   | `/auth/logout`                                                      | Sign out                                                             |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.

Only signed-in teachers can register or unregister students. Activity and participant lists remain publicly viewable. Teacher credentials are stored in `teachers.json` as salted scrypt hashes; do not commit populated teacher credential files. Set `SESSION_SECRET` to a stable secret in deployments so sessions remain valid across restarts and workers.
