def savings_plan(salary: float) -> dict[str, float]:
    if salary < 0:
        raise ValueError("salary cannot be negative")

    return {
        "emergency_fund": round(salary * 0.10, 2),
        "long_term_investing": round(salary * 0.08, 2),
        "goal_savings": round(salary * 0.02, 2),
    }
