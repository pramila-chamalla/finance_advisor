import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SYSTEM_PROMPT = """You are FinGenie, a supportive personal finance education assistant.
Use the provided profile and tracked numbers to answer clearly and practically.
Never claim to be a licensed financial adviser, guarantee returns, or recommend a
specific security. Explain uncertainty and encourage users to verify important
decisions. Do not ask for bank passwords, card numbers, or authentication codes."""


def _local_answer(question: str, context: dict[str, Any]) -> dict[str, str]:
    profile = context.get("profile", {})
    plan = context.get("plan", {})
    report = plan.get("report", {})
    budget = plan.get("budget", {})
    question_text = question.lower()
    if "goal" in question_text or "save" in question_text:
        goal_plans = plan.get("goal_plans", [])
        if goal_plans:
            details = "; ".join(
                f"{goal['goal_name']}: ₹{goal['required_per_month']:,.0f}/month"
                for goal in goal_plans[:3]
            )
            focus = f"Your current goal targets are {details} over 12 months."
        else:
            focus = (
                "You have not added a savings goal yet. Add one in the Goals page "
                "to get a monthly contribution target."
            )
    elif "expense" in question_text or "spend" in question_text:
        categories = plan.get("expense_analysis", {}).get("by_category", {})
        highest = next(iter(categories), None)
        focus = (
            f"Your highest tracked category this month is {highest} "
            f"(₹{categories[highest]:,.0f})."
            if highest
            else "You have not logged any expenses this month yet."
        )
    else:
        focus = (
            f"The 50/30/20 starting guide allocates ₹{budget.get('needs', 0):,.0f} "
            f"for needs, ₹{budget.get('wants', 0):,.0f} for wants and "
            f"₹{budget.get('savings', 0):,.0f} for savings."
        )
    answer = (
        f"Hi {profile.get('name', 'there')}! {focus} "
        f"You have ₹{report.get('savings', 0):,.0f} left after this month's "
        "logged expenses. This is general educational guidance, not individualized "
        "investment advice."
    )
    return {"answer": answer, "mode": "local"}


def ask_ai(
    question: str, context: dict[str, Any], *, use_ai: bool = False
) -> dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY")
    if not use_ai or not api_key:
        return _local_answer(question, context)

    model = os.getenv("MODEL", "gpt-oss-120b")
    client_options: dict[str, Any] = {
        "model": model,
        "api_key": api_key,
        "temperature": 0.3,
        "timeout": 30,
        "max_retries": 1,
    }
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        client_options["base_url"] = base_url

    response = ChatOpenAI(**client_options).invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Financial context (JSON): {context}\n\n"
                    f"User question: {question}"
                )
            ),
        ]
    )
    content = response.content
    if isinstance(content, str):
        answer = content
    elif isinstance(content, list):
        answer = " ".join(
            item["text"]
            for item in content
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        )
    else:
        answer = str(content)
    if not answer.strip():
        raise RuntimeError("The AI provider returned an empty response")
    return {"answer": answer, "mode": "ai"}
