def budget_plan(salary: float) -> dict[str, float]:
    if salary < 0:
        raise ValueError("salary cannot be negative")

    return {
        "needs": round(salary * 0.50, 2),
        "wants": round(salary * 0.30, 2),
        "savings": round(salary * 0.20, 2),
    }
