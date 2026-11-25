from contextlib import closing
from datetime import date

from fastapi import APIRouter, HTTPException

if __package__ and "." in __package__:
    from ..agents.orchestrator import build_financial_plan
    from ..db import get_connection
    from ..schemas import ChatRequest
    from ..services.llm_service import ask_ai
else:
    from agents.orchestrator import build_financial_plan
    from db import get_connection
    from schemas import ChatRequest
    from services.llm_service import ask_ai

router = APIRouter(prefix="/chat", tags=["Advisor"])


@router.post("")
def chat(request: ChatRequest) -> dict:
    with closing(get_connection()) as connection:
        user = connection.execute(
            "SELECT id, name, salary FROM users WHERE id = ?", (request.user_id,)
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Profile not found")
        month = date.today().strftime("%Y-%m")
        expenses = [
            dict(row)
            for row in connection.execute(
                """
                SELECT category, amount, description, expense_date
                FROM expenses
                WHERE user_id = ? AND substr(expense_date, 1, 7) = ?
                """,
                (request.user_id, month),
            ).fetchall()
        ]
        goals = [
            dict(row)
            for row in connection.execute(
                """
                SELECT goal_name, target_amount, saved_amount
                FROM goals WHERE user_id = ?
                """,
                (request.user_id,),
            ).fetchall()
        ]

    plan = build_financial_plan(float(user["salary"]), expenses, goals)
    result = ask_ai(
        request.question,
        {
            "profile": {"salary": float(user["salary"])},
            "plan": plan,
            "goals": [
                {
                    "target_amount": goal["target_amount"],
                    "saved_amount": goal["saved_amount"],
                }
                for goal in goals
            ],
            "expenses": [
                {"category": expense["category"], "amount": expense["amount"]}
                for expense in expenses
            ],
        },
        use_ai=request.use_ai,
    )
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "INSERT INTO chats (user_id, question, response) VALUES (?, ?, ?)",
            (request.user_id, request.question, result["answer"]),
        )
        connection.commit()
        result["id"] = cursor.lastrowid
    return result


@router.get("/{user_id}")
def chat_history(user_id: int) -> dict:
    with closing(get_connection()) as connection:
        if not connection.execute(
            "SELECT 1 FROM users WHERE id = ?", (user_id,)
        ).fetchone():
            raise HTTPException(status_code=404, detail="Profile not found")
        rows = connection.execute(
            """
            SELECT id, question, response, created_at
            FROM chats WHERE user_id = ?
            ORDER BY id DESC LIMIT 50
            """,
            (user_id,),
        ).fetchall()
    return {"messages": [dict(row) for row in reversed(rows)]}
