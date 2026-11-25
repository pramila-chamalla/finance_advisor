from contextlib import closing

from fastapi import APIRouter, HTTPException

if __package__ and "." in __package__:
    from ..db import get_connection
    from ..schemas import UserCreate
else:
    from db import get_connection
    from schemas import UserCreate

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register")
def register(user: UserCreate) -> dict:
    with closing(get_connection()) as connection:
        existing = connection.execute(
            "SELECT id FROM users WHERE lower(email) = ?", (user.email,)
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists. Sign in instead.",
            )

        cursor = connection.execute(
            "INSERT INTO users (name, email, salary, age) VALUES (?, ?, ?, ?)",
            (user.name, user.email, user.salary, user.age),
        )
        connection.commit()
        return {
            "message": "Your profile is ready",
            "user": {
                "id": cursor.lastrowid,
                "name": user.name,
                "email": user.email,
                "salary": user.salary,
                "age": user.age,
            },
        }


@router.post("/login")
def login(credentials: dict) -> dict:
    email = str(credentials.get("email", "")).strip().lower()
    if not email:
        raise HTTPException(status_code=422, detail="Email is required")
    with closing(get_connection()) as connection:
        user = connection.execute(
            "SELECT id, name, email, salary, age FROM users WHERE lower(email) = ?",
            (email,),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="No profile found for that email")
        return {"user": dict(user)}


@router.get("/{user_id}")
def get_user(user_id: int) -> dict:
    with closing(get_connection()) as connection:
        user = connection.execute(
            "SELECT id, name, email, salary, age FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"user": dict(user)}


@router.put("/{user_id}")
def update_user(user_id: int, updates: UserCreate) -> dict:
    with closing(get_connection()) as connection:
        duplicate = connection.execute(
            "SELECT id FROM users WHERE lower(email) = ? AND id != ?",
            (updates.email, user_id),
        ).fetchone()
        if duplicate:
            raise HTTPException(
                status_code=409, detail="That email belongs to another profile"
            )
        cursor = connection.execute(
            """
            UPDATE users
            SET name = ?, email = ?, salary = ?, age = ?
            WHERE id = ?
            """,
            (updates.name, updates.email, updates.salary, updates.age, user_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Profile not found")
        connection.commit()
        user = connection.execute(
            "SELECT id, name, email, salary, age FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return {"user": dict(user)}
