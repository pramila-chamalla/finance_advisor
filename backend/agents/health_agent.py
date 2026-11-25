def calculate_health_score(salary: float, expenses: float) -> float:
    if salary <= 0:
        return 0.0

    savings_rate = (salary - expenses) / salary
    score = max(0.0, min(100.0, savings_rate * 100))
    return round(score, 2)
