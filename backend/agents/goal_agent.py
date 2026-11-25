def create_goal_plan(target_amount: float, months: int, saved_amount: float = 0) -> dict:
    if target_amount <= 0:
        raise ValueError("target_amount must be greater than zero")
    if months <= 0:
        raise ValueError("months must be greater than zero")

    remaining = max(0.0, target_amount - saved_amount)
    return {
        "remaining_amount": round(remaining, 2),
        "required_per_month": round(remaining / months, 2),
        "months": months,
    }
