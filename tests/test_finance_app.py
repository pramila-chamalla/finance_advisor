import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend import db
from backend.agents.budget_agent import budget_plan
from backend.agents.goal_agent import create_goal_plan
from backend.agents.health_agent import calculate_health_score
from backend.main import app


class FinanceAgentTests(unittest.TestCase):
    def test_budget_allocations_total_monthly_income(self) -> None:
        plan = budget_plan(50_000)
        self.assertEqual(plan, {"needs": 25_000, "wants": 15_000, "savings": 10_000})
        self.assertEqual(sum(plan.values()), 50_000)

    def test_health_score_is_bounded_and_handles_missing_income(self) -> None:
        self.assertEqual(calculate_health_score(0, 100), 0)
        self.assertEqual(calculate_health_score(100, 150), 0)
        self.assertEqual(calculate_health_score(100, 0), 100)

    def test_goal_plan_uses_remaining_balance(self) -> None:
        self.assertEqual(
            create_goal_plan(12_000, 12, 3_000),
            {"remaining_amount": 9_000, "required_per_month": 750, "months": 12},
        )
        with self.assertRaises(ValueError):
            create_goal_plan(12_000, 0)


class FinanceApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "finance.db"
        self.db_patch = patch.object(db, "DB_NAME", self.database_path)
        self.db_patch.start()
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.db_patch.stop()
        self.temporary_directory.cleanup()

    def create_profile(self) -> int:
        response = self.client.post(
            "/users/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "salary": 50_000,
                "age": 30,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["user"]["id"]

    def test_profile_expenses_goals_and_dashboard_flow(self) -> None:
        user_id = self.create_profile()
        duplicate = self.client.post(
            "/users/register",
            json={
                "name": "Other",
                "email": "TEST@example.com",
                "salary": 10_000,
                "age": 25,
            },
        )
        self.assertEqual(duplicate.status_code, 409)

        expense = self.client.post(
            "/expenses",
            json={
                "user_id": user_id,
                "category": "Food",
                "amount": 1_250,
                "description": "Groceries",
            },
        )
        self.assertEqual(expense.status_code, 200, expense.text)

        goal = self.client.post(
            "/goals",
            json={
                "user_id": user_id,
                "goal_name": "Emergency fund",
                "target_amount": 20_000,
                "current_amount": 2_000,
            },
        )
        self.assertEqual(goal.status_code, 200, goal.text)
        goal_id = goal.json()["goal_id"]

        contribution = self.client.post(
            f"/goals/{goal_id}/contributions",
            json={"user_id": user_id, "amount": 1_000},
        )
        self.assertEqual(contribution.status_code, 200, contribution.text)
        self.assertEqual(contribution.json()["saved_amount"], 3_000)

        dashboard = self.client.get(f"/dashboard/{user_id}")
        self.assertEqual(dashboard.status_code, 200, dashboard.text)
        data = dashboard.json()
        self.assertEqual(data["plan"]["budget"]["savings"], 10_000)
        self.assertEqual(data["plan"]["expense_analysis"]["total_expense"], 1_250)
        self.assertEqual(data["goals"][0]["saved_amount"], 3_000)

    def test_chat_uses_local_coach_when_no_provider_key_is_configured(self) -> None:
        user_id = self.create_profile()
        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "", "OPEN_API_KEY": ""}, clear=False
        ):
            response = self.client.post(
                "/chat",
                json={"user_id": user_id, "question": "How can I budget my salary?"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["mode"], "local")
        self.assertIn("50/30/20", response.json()["answer"])
        history = self.client.get(f"/chat/{user_id}")
        self.assertEqual(history.status_code, 200, history.text)
        self.assertEqual(len(history.json()["messages"]), 1)

    def test_external_chat_requires_consent_and_omits_profile_identifiers(self) -> None:
        user_id = self.create_profile()
        self.client.post(
            "/expenses",
            json={
                "user_id": user_id,
                "category": "Food",
                "amount": 500,
                "description": "private transaction note",
            },
        )
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "OPEN_API_KEY": ""},
            clear=False,
        ):
            with patch("backend.services.llm_service.ChatOpenAI") as client:
                client.return_value.invoke.return_value.content = "Test answer"
                local_response = self.client.post(
                    "/chat",
                    json={"user_id": user_id, "question": "How do I save?"},
                )
                self.assertEqual(local_response.status_code, 200, local_response.text)
                self.assertEqual(local_response.json()["mode"], "local")
                client.assert_not_called()

                ai_response = self.client.post(
                    "/chat",
                    json={
                        "user_id": user_id,
                        "question": "How do I save?",
                        "use_ai": True,
                    },
                )
        self.assertEqual(ai_response.status_code, 200, ai_response.text)
        self.assertEqual(ai_response.json()["mode"], "ai")
        sent_context = client.return_value.invoke.call_args.args[0][1].content
        self.assertNotIn("Demo User", sent_context)
        self.assertNotIn("test@example.com", sent_context)
        self.assertNotIn("private transaction note", sent_context)

    def test_rejects_invalid_expense_amount(self) -> None:
        user_id = self.create_profile()
        response = self.client.post(
            "/expenses",
            json={
                "user_id": user_id,
                "category": "Food",
                "amount": -50,
                "description": "Invalid",
            },
        )
        self.assertEqual(response.status_code, 422)


class DatabaseMigrationTests(unittest.TestCase):
    def test_upgrades_legacy_tables_without_losing_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "legacy.db"
            with patch.object(db, "DB_NAME", path):
                connection = sqlite3.connect(path)
                connection.executescript(
                    """
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY, name TEXT, email TEXT,
                        salary REAL, age INTEGER
                    );
                    CREATE TABLE expenses (
                        id INTEGER PRIMARY KEY, user_id INTEGER, category TEXT,
                        amount REAL, description TEXT
                    );
                    CREATE TABLE chats (
                        id INTEGER PRIMARY KEY, user_id INTEGER,
                        question TEXT, response TEXT
                    );
                    INSERT INTO users VALUES (1, 'Legacy', 'legacy@example.com', 2000, 30);
                    INSERT INTO expenses VALUES (1, 1, 'Food', 20, 'Lunch');
                    INSERT INTO chats VALUES (1, 1, 'Question', 'Answer');
                    """
                )
                connection.close()

                db.init_db()

                with closing(db.get_connection()) as migrated:
                    expense = migrated.execute(
                        "SELECT amount, expense_date FROM expenses WHERE id = 1"
                    ).fetchone()
                    chat = migrated.execute(
                        "SELECT response, created_at FROM chats WHERE id = 1"
                    ).fetchone()
                    self.assertEqual(expense["amount"], 20)
                    self.assertIsNotNone(expense["expense_date"])
                    self.assertEqual(chat["response"], "Answer")
                    self.assertIsNotNone(chat["created_at"])


if __name__ == "__main__":
    unittest.main()
