def generate_report(salary: float, expenses: float) -> dict[str, float]:
    savings = salary - expenses
    return {
        "salary": round(salary, 2),
        "expenses": round(expenses, 2),
        "savings": round(savings, 2),
        "savings_rate": round((savings / salary) * 100, 2) if salary else 0.0,
    }
