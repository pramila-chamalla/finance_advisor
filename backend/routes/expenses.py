from contextlib import closing

from fastapi import APIRouter, HTTPException, Query

if __package__ and "." in __package__:
    from ..db import get_connection
    from ..schemas import ExpenseCreate
else:
    from db import get_connection
    from schemas import ExpenseCreate

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("")
def add_expense(expense: ExpenseCreate) -> dict:
    with closing(get_connection()) as connection:
        if not connection.execute(
            "SELECT 1 FROM users WHERE id = ?", (expense.user_id,)
        ).fetchone():
            raise HTTPException(status_code=404, detail="Profile not found")
        cursor = connection.execute(
            """
            INSERT INTO expenses (user_id, category, amount, description, expense_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                expense.user_id,
                expense.category,
                expense.amount,
                expense.description,
                expense.expense_date.isoformat(),
            ),
        )
        connection.commit()
        return {"message": "Expense added", "expense_id": cursor.lastrowid}


@router.get("/{user_id}")
def list_expenses(
    user_id: int,
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> dict:
    with closing(get_connection()) as connection:
        if not connection.execute(
            "SELECT 1 FROM users WHERE id = ?", (user_id,)
        ).fetchone():
            raise HTTPException(status_code=404, detail="Profile not found")
        if month:
            rows = connection.execute(
                """
                SELECT id, category, amount, description, expense_date
                FROM expenses
                WHERE user_id = ? AND substr(expense_date, 1, 7) = ?
                ORDER BY expense_date DESC, id DESC
                """,
                (user_id, month),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, category, amount, description, expense_date
                FROM expenses
                WHERE user_id = ?
                ORDER BY expense_date DESC, id DESC
                """,
                (user_id,),
            ).fetchall()
    return {"expenses": [dict(row) for row in rows]}


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, user_id: int) -> dict:
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Expense not found")
        connection.commit()
    return {"message": "Expense deleted"}
