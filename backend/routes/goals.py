from contextlib import closing

from fastapi import APIRouter, HTTPException

if __package__ and "." in __package__:
    from ..db import get_connection
    from ..schemas import GoalContribution, GoalCreate
else:
    from db import get_connection
    from schemas import GoalContribution, GoalCreate

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post("")
def add_goal(goal: GoalCreate) -> dict:
    if goal.current_amount > goal.target_amount:
        raise HTTPException(
            status_code=422, detail="Saved amount cannot exceed the target"
        )
    with closing(get_connection()) as connection:
        if not connection.execute(
            "SELECT 1 FROM users WHERE id = ?", (goal.user_id,)
        ).fetchone():
            raise HTTPException(status_code=404, detail="Profile not found")
        cursor = connection.execute(
            """
            INSERT INTO goals (user_id, goal_name, target_amount, saved_amount)
            VALUES (?, ?, ?, ?)
            """,
            (
                goal.user_id,
                goal.goal_name,
                goal.target_amount,
                goal.current_amount,
            ),
        )
        connection.commit()
        return {"message": "Goal added", "goal_id": cursor.lastrowid}


@router.get("/{user_id}")
def list_goals(user_id: int) -> dict:
    with closing(get_connection()) as connection:
        if not connection.execute(
            "SELECT 1 FROM users WHERE id = ?", (user_id,)
        ).fetchone():
            raise HTTPException(status_code=404, detail="Profile not found")
        rows = connection.execute(
            """
            SELECT id, goal_name, target_amount, saved_amount
            FROM goals WHERE user_id = ? ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()
    return {"goals": [dict(row) for row in rows]}


@router.post("/{goal_id}/contributions")
def add_contribution(goal_id: int, contribution: GoalContribution) -> dict:
    with closing(get_connection()) as connection:
        goal = connection.execute(
            """
            SELECT target_amount, saved_amount FROM goals
            WHERE id = ? AND user_id = ?
            """,
            (goal_id, contribution.user_id),
        ).fetchone()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        if goal["saved_amount"] + contribution.amount > goal["target_amount"]:
            raise HTTPException(
                status_code=422, detail="Contribution exceeds the remaining target"
            )
        connection.execute(
            "UPDATE goals SET saved_amount = saved_amount + ? WHERE id = ?",
            (contribution.amount, goal_id),
        )
        connection.commit()
        updated = connection.execute(
            "SELECT saved_amount FROM goals WHERE id = ?", (goal_id,)
        ).fetchone()
    return {"message": "Contribution recorded", "saved_amount": updated["saved_amount"]}


@router.delete("/{goal_id}")
def delete_goal(goal_id: int, user_id: int) -> dict:
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "DELETE FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Goal not found")
        connection.commit()
    return {"message": "Goal deleted"}
