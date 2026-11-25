from contextlib import closing
from datetime import date

from fastapi import APIRouter, HTTPException

if __package__ and "." in __package__:
    from ..agents.orchestrator import build_financial_plan
    from ..db import get_connection
    from ..services.advisor_service import build_recommendations
else:
    from agents.orchestrator import build_financial_plan
    from db import get_connection
    from services.advisor_service import build_recommendations

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/{user_id}")
def get_dashboard(user_id: int) -> dict:
    month = date.today().strftime("%Y-%m")
    with closing(get_connection()) as connection:
        user = connection.execute(
            "SELECT id, name, email, salary, age FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Profile not found")

        expenses = [
            dict(row)
            for row in connection.execute(
                """
                SELECT id, category, amount, description, expense_date
                FROM expenses
                WHERE user_id = ? AND substr(expense_date, 1, 7) = ?
                ORDER BY expense_date DESC, id DESC
                """,
                (user_id, month),
            ).fetchall()
        ]
        goals = [
            dict(row)
            for row in connection.execute(
                """
                SELECT id, goal_name, target_amount, saved_amount
                FROM goals WHERE user_id = ? ORDER BY id DESC
                """,
                (user_id,),
            ).fetchall()
        ]

    profile = dict(user)
    plan = build_financial_plan(float(profile["salary"]), expenses, goals)
    return {
        "month": month,
        "profile": profile,
        "plan": plan,
        "recommendations": build_recommendations(plan),
        "recent_expenses": expenses[:6],
        "goals": goals,
    }
