# FinGenie — Personal Finance Advisor

FinGenie is a local-first personal finance management app. A user creates a
profile, enters monthly income, records transactions and savings goals, and
receives an explainable monthly plan in a Streamlit dashboard. FastAPI serves
the application API and SQLite stores profile, expense, goal and chat data.

> **Scope and safety:** This is a learning/demo app, not a bank or a regulated
> financial service. Its guidance is educational, not tax, investment or
> individualized financial advice. It does not connect to bank accounts,
> execute payments or guarantee returns. Profile switching is email-only and
> is not authentication; do not expose this version to the public internet or
> enter sensitive data.

## What users can do

- Create and update a local profile with name, email, age and monthly take-home
  income.
- View a monthly dashboard with spending, remaining income, budget allocations,
  category chart, financial-health score, goal progress and practical next steps.
- Add, review and delete dated expenses with categories and descriptions.
- Create savings goals, record contributions and track progress.
- Ask a finance-coach question using the saved profile and recent financial
  context. The local response is the default. The user must explicitly opt in
  before a question and summarized, non-identifying finance context is sent to the
  configured OpenAI-compatible provider.
- Browse the interactive API docs at `http://127.0.0.1:8000/docs`.

## Agent responsibilities

The LangGraph plan runs focused agents over the same monthly profile:

1. **Budget agent** — allocates a starting guideline of 50% needs, 30% wants and
   20% savings. Users should adapt this to their actual costs.
2. **Savings agent** — suggests splitting the 20% savings guideline into 10%
   emergency-fund savings, 8% long-term savings and 2% goal savings. These are
   illustrative starting points, not investment recommendations.
3. **Expense agent** — totals this month's recorded expenses by category.
4. **Goal agent** — estimates the monthly contribution needed to reach each goal
   over 12 months.
5. **Financial-health/report agent** — compares income with tracked expenses and
   calculates a capped savings-rate score. It is an indicator, not a credit score.
6. **AI money coach** — responds to a question with the above context, or uses a
   local fallback when provider credentials are absent.

## Architecture

```text
Streamlit UI (frontend/)
        | HTTP / JSON
FastAPI routes (backend/routes/)
        |             \
LangGraph agents      AI service (optional provider)
        |
SQLite (backend/database/finance.db)
```

### SQLite tables

- `users`: profile and monthly salary.
- `expenses`: dated category, amount and optional description.
- `goals`: target amount and saved amount.
- `chats`: question, response and creation time.

The database is created on API startup. Startup also adds the missing date and
chat timestamp columns to older databases without deleting existing records.

### Main API routes

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | API readiness |
| `POST` | `/users/register` | Create profile |
| `POST` | `/users/login` | Open local profile by email |
| `GET`, `PUT` | `/users/{user_id}` | Read or update profile |
| `GET` | `/dashboard/{user_id}` | Monthly dashboard and agent insights |
| `POST`, `GET` | `/expenses`, `/expenses/{user_id}` | Add/list expenses |
| `DELETE` | `/expenses/{expense_id}?user_id=...` | Delete an expense |
| `POST`, `GET` | `/goals`, `/goals/{user_id}` | Add/list savings goals |
| `POST` | `/goals/{goal_id}/contributions` | Record a goal contribution |
| `DELETE` | `/goals/{goal_id}?user_id=...` | Delete a goal |
| `POST` | `/financial-plan` | Generate a financial plan |
| `POST`, `GET` | `/chat`, `/chat/{user_id}` | Ask questions and read chat history |

## Run locally on Windows

Open PowerShell in this project folder.

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r req.txt
   ```

   If PowerShell blocks activation, run commands using `.\.venv\Scripts\python.exe`.

2. (Optional) Enable the live AI coach:

   - Immediately revoke/rotate any provider key previously shared in chat.
   - Copy `.env.example` to `.env` and place the replacement key only in `.env`.
     Never paste the key into source files, screenshots or commits.
   - Set `MODEL` to a model available to your account. For an OpenAI-compatible
     service that hosts `gpt-oss-120b`, also set that provider's `OPENAI_BASE_URL`.
   - `OPENAI_API_KEY` is the standard variable. `OPEN_API_KEY` is accepted only
     as a compatibility alias.

   The dashboard, budget agents and local coach work without any API key.

3. Start the API in the first terminal. Port `8000` is the default; if it is
   already in use, use `8001`:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001
   ```

   The backend can also be started from inside the `backend` folder with
   `uvicorn main:app --reload`.

4. If you used port `8001`, point Streamlit at it, then start the UI in a second
   terminal from the project folder:

   ```powershell
   $env:FINANCE_API_URL = "http://127.0.0.1:8001"
   .\.venv\Scripts\python.exe -m streamlit run frontend/app.py
   ```

5. Open the Streamlit URL printed by the command (normally
   `http://localhost:8501`) and create a profile.

For a separate local database, set `FINANCE_DB_PATH` before starting the API.
For a non-default API URL, set `FINANCE_API_URL` before starting Streamlit.

## Test

Run the project tests with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The integration tests use a temporary SQLite database and never modify the
project's saved finance data.

## Suggested development roadmap

### MVP — included here

- Profile onboarding and salary-based monthly plans.
- Transaction and savings-goal tracking.
- Agent-driven dashboard insights and conversational coach.
- Local SQLite storage, API validation and a polished Streamlit interface.

### Next: safer accounts and better planning

- Add password-based authentication, password hashing, session tokens and
  per-user authorization before supporting multiple users or network access.
- Add user-selected currency, expense recurrence, custom budget percentages and
  user-defined goal deadlines.
- Add month selectors, month-over-month comparisons, export and database backup.
- Add tests for authorization, migrations, malformed input and provider failures.

### Later: production-grade AI and deployment

- Add provider selection, rate limits and audit controls around the included
  opt-in, minimized context sent to external models.
- Keep financial calculations deterministic and auditable; use the LLM only to
  explain them in plain language.
- Add structured logs without storing secrets, monitoring, HTTPS, deployment
  configuration, backups and a privacy/data-retention policy.
- Consider bank integrations only through regulated providers and explicit
  consent; never collect banking credentials directly.
