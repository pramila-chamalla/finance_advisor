from collections import defaultdict
from typing import Any


def analyze_expense(expense_list: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, float] = defaultdict(float)
    total = 0.0
    for expense in expense_list:
        amount = float(expense["amount"])
        total += amount
        totals[str(expense["category"])] += amount

    return {
        "total_expense": round(total, 2),
        "by_category": {
            category: round(amount, 2)
            for category, amount in sorted(
                totals.items(), key=lambda item: item[1], reverse=True
            )
        },
    }
