from contextlib import asynccontextmanager

from fastapi import FastAPI

if __package__:
    from .db import init_db
    from .routes.chatbot import router as chat_router
    from .routes.dashboard import router as dashboard_router
    from .routes.expenses import router as expense_router
    from .routes.goals import router as goal_router
    from .routes.plans import router as plan_router
    from .routes.users import router as user_router
else:
    from db import init_db
    from routes.chatbot import router as chat_router
    from routes.dashboard import router as dashboard_router
    from routes.expenses import router as expense_router
    from routes.goals import router as goal_router
    from routes.plans import router as plan_router
    from routes.users import router as user_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="FinGenie | Personal Finance Advisor",
    description=(
        "A personal finance dashboard with explainable budgeting, savings, "
        "expense, goal, and financial-health agents."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(user_router)
app.include_router(expense_router)
app.include_router(goal_router)
app.include_router(plan_router)
app.include_router(dashboard_router)
app.include_router(chat_router)


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "FinGenie"}


@app.get("/", tags=["System"])
def home() -> dict[str, str]:
    return {
        "message": "FinGenie is ready",
        "docs": "/docs",
        "health": "/health",
    }
