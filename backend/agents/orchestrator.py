from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .budget_agent import budget_plan
from .expense_agent import analyze_expense
from .goal_agent import create_goal_plan
from .health_agent import calculate_health_score
from .report_agent import generate_report
from .savings_agent import savings_plan


class FinanceState(TypedDict, total=False):
    salary: float
    expenses: list[dict[str, Any]]
    goals: list[dict[str, Any]]
    budget: dict[str, float]
    savings: dict[str, float]
    expense_analysis: dict[str, Any]
    goal_plans: list[dict[str, Any]]
    report: dict[str, float]
    health_score: float


def _budget_node(state: FinanceState) -> dict[str, Any]:
    return {"budget": budget_plan(state["salary"])}


def _savings_node(state: FinanceState) -> dict[str, Any]:
    return {"savings": savings_plan(state["salary"])}


def _expenses_node(state: FinanceState) -> dict[str, Any]:
    return {"expense_analysis": analyze_expense(state.get("expenses", []))}


def _goals_node(state: FinanceState) -> dict[str, Any]:
    return {
        "goal_plans": [
            {
                "id": goal.get("id"),
                "goal_name": goal["goal_name"],
                "target_amount": goal["target_amount"],
                **create_goal_plan(
                    float(goal["target_amount"]),
                    int(goal.get("months", 12)),
                    float(goal.get("saved_amount", 0)),
                ),
            }
            for goal in state.get("goals", [])
        ]
    }


def _report_node(state: FinanceState) -> dict[str, Any]:
    total_expenses = analyze_expense(state.get("expenses", []))["total_expense"]
    return {
        "report": generate_report(state["salary"], total_expenses),
        "health_score": calculate_health_score(state["salary"], total_expenses),
    }


_builder = StateGraph(FinanceState)
_builder.add_node("budget_agent", _budget_node)
_builder.add_node("savings_agent", _savings_node)
_builder.add_node("expense_agent", _expenses_node)
_builder.add_node("goal_agent", _goals_node)
_builder.add_node("health_and_report_agent", _report_node)
for _node in (
    "budget_agent",
    "savings_agent",
    "expense_agent",
    "goal_agent",
    "health_and_report_agent",
):
    _builder.add_edge(START, _node)
    _builder.add_edge(_node, END)

graph = _builder.compile()


def build_financial_plan(
    salary: float,
    expenses: list[dict[str, Any]] | None = None,
    goals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = graph.invoke(
        {
            "salary": salary,
            "expenses": expenses or [],
            "goals": goals or [],
        }
    )
    return {
        "budget": result["budget"],
        "savings": result["savings"],
        "expense_analysis": result["expense_analysis"],
        "goal_plans": result["goal_plans"],
        "report": result["report"],
        "health_score": result["health_score"],
    }
