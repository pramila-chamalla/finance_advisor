from contextlib import closing
from datetime import date

from fastapi import APIRouter, HTTPException

if __package__ and "." in __package__:
    from ..agents.orchestrator import build_financial_plan
    from ..db import get_connection
    from ..schemas import PlanRequest
else:
    from agents.orchestrator import build_financial_plan
    from db import get_connection
    from schemas import PlanRequest

router = APIRouter(tags=["Financial plan"])


@router.post("/financial-plan")
def plan(request: PlanRequest) -> dict:
    if request.user_id is None and request.salary is None:
        raise HTTPException(
            status_code=422, detail="Provide a user_id or a monthly salary"
        )

    user = None
    expenses: list[dict] = []
    goals: list[dict] = []
    if request.user_id is not None:
        with closing(get_connection()) as connection:
            user = connection.execute(
                "SELECT id, name, salary FROM users WHERE id = ?",
                (request.user_id,),
            ).fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="Profile not found")
            today = date.today()
            expenses = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT category, amount, description, expense_date
                    FROM expenses
                    WHERE user_id = ? AND substr(expense_date, 1, 7) = ?
                    """,
                    (request.user_id, today.strftime("%Y-%m")),
                ).fetchall()
            ]
            goals = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT id, goal_name, target_amount, saved_amount
                    FROM goals WHERE user_id = ?
                    """,
                    (request.user_id,),
                ).fetchall()
            ]

    salary = float(user["salary"] if user else request.salary or 0)
    if salary <= 0:
        raise HTTPException(
            status_code=422,
            detail="Add a monthly income greater than zero to generate a plan",
        )

    plan_result = build_financial_plan(salary, expenses, goals)
    return plan_result
