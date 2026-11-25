def build_recommendations(plan: dict) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    budget = plan["budget"]
    analysis = plan["expense_analysis"]
    report = plan["report"]
    expenses_by_category = analysis["by_category"]

    essential_categories = {"rent", "housing", "bills", "utilities", "food", "groceries"}
    essential_spend = sum(
        amount
        for category, amount in expenses_by_category.items()
        if category.strip().lower() in essential_categories
    )
    if essential_spend > budget["needs"]:
        recommendations.append(
            {
                "title": "Review essential spending",
                "detail": (
                    "Your tracked essentials are above the 50% needs guideline. "
                    "Check recurring bills and housing costs before cutting necessities."
                ),
                "agent": "Budget agent",
                "tone": "warning",
            }
        )

    if report["savings"] < 0:
        recommendations.append(
            {
                "title": "Spending is above income",
                "detail": (
                    "Your logged expenses exceed this month's income. Review recent "
                    "transactions and prioritize essential payments."
                ),
                "agent": "Financial health agent",
                "tone": "warning",
            }
        )
    elif report["savings_rate"] < 20:
        recommendations.append(
            {
                "title": "Build your savings buffer",
                "detail": (
                    f"Your current tracked savings rate is {report['savings_rate']:.1f}%. "
                    "The 50/30/20 guideline aims for 20%; try a small, sustainable "
                    "automatic transfer after payday."
                ),
                "agent": "Savings agent",
                "tone": "info",
            }
        )
    else:
        recommendations.append(
            {
                "title": "Good savings momentum",
                "detail": (
                    f"You have {report['savings_rate']:.1f}% of this month's income "
                    "left after logged expenses. Keep your emergency fund liquid "
                    "before considering long-term investments."
                ),
                "agent": "Savings agent",
                "tone": "success",
            }
        )

    if not expenses_by_category:
        recommendations.append(
            {
                "title": "Add your first expenses",
                "detail": (
                    "Your budget is ready. Log a few transactions to get category "
                    "insights and a more useful monthly health score."
                ),
                "agent": "Expense agent",
                "tone": "info",
            }
        )

    for goal in plan["goal_plans"][:2]:
        if goal["remaining_amount"] > 0:
            recommendations.append(
                {
                    "title": f"Make progress on {goal['goal_name']}",
                    "detail": (
                        f"Setting aside about ₹{goal['required_per_month']:,.0f} per "
                        "month would reach the target in 12 months, based on your "
                        "current saved amount."
                    ),
                    "agent": "Goal agent",
                    "tone": "info",
                }
            )
    return recommendations
