from datetime import date
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    salary: float = Field(ge=0, le=1_000_000_000)
    age: int = Field(ge=18, le=120)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("Enter a valid email address")
        return normalized


class ExpenseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: int = Field(gt=0)
    category: str = Field(min_length=1, max_length=60)
    amount: float = Field(gt=0, le=1_000_000_000)
    description: str = Field(default="", max_length=500)
    expense_date: date = Field(default_factory=date.today)


class GoalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: int = Field(gt=0)
    goal_name: str = Field(min_length=1, max_length=100)
    target_amount: float = Field(gt=0, le=1_000_000_000)
    current_amount: float = Field(default=0, ge=0, le=1_000_000_000)


class GoalContribution(BaseModel):
    user_id: int = Field(gt=0)
    amount: float = Field(gt=0, le=1_000_000_000)


class PlanRequest(BaseModel):
    salary: float | None = Field(default=None, ge=0, le=1_000_000_000)
    user_id: int | None = Field(default=None, gt=0)


class ChatRequest(BaseModel):
    user_id: int = Field(gt=0)
    question: str = Field(min_length=1, max_length=4000)
    use_ai: bool = False
