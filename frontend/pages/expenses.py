from datetime import date

import streamlit as st

from common import ApiError, api_request, money, page_heading, require_user, show_api_error


CATEGORIES = [
    "Housing",
    "Food",
    "Transport",
    "Utilities",
    "Health",
    "Shopping",
    "Entertainment",
    "Education",
    "Debt payment",
    "Other",
]


def render() -> None:
    user = require_user()
    if user is None:
        return

    page_heading(
        "SPENDING, MADE VISIBLE",
        "Transactions",
        "Log everyday spending to uncover patterns and make your monthly plan real.",
    )
    add_column, history_column = st.columns([0.85, 1.15], gap="large")
    with add_column:
        with st.container(border=True):
            st.subheader("Add an expense")
            with st.form("add_expense", clear_on_submit=True):
                category = st.selectbox("Category", CATEGORIES)
                amount = st.number_input(
                    "Amount (₹)", min_value=0.0, step=100.0, format="%.2f"
                )
                expense_date = st.date_input("Date", value=date.today())
                description = st.text_input(
                    "What was it for?", max_chars=500, placeholder="e.g. Weekly groceries"
                )
                submitted = st.form_submit_button(
                    "Save transaction", type="primary", width="stretch"
                )
            if submitted:
                if amount <= 0:
                    st.warning("Enter an amount greater than zero.")
                else:
                    try:
                        api_request(
                            "POST",
                            "/expenses",
                            payload={
                                "user_id": user["id"],
                                "category": category,
                                "amount": amount,
                                "description": description,
                                "expense_date": expense_date.isoformat(),
                            },
                        )
                        st.success("Expense saved.")
                        st.rerun()
                    except ApiError as error:
                        show_api_error(error)

    with history_column:
        with st.container(border=True):
            st.subheader("Your transaction history")
            month_only = st.toggle("Only this month", value=True)
            try:
                params = {"month": date.today().strftime("%Y-%m")} if month_only else None
                transactions = api_request(
                    "GET", f"/expenses/{user['id']}", params=params
                )["expenses"]
            except ApiError as error:
                show_api_error(error)
                return

            if not transactions:
                st.info("No transactions here yet. Your first entry will show up here.")
            else:
                st.dataframe(
                    transactions,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "id": None,
                        "amount": st.column_config.NumberColumn(
                            "Amount", format="₹%.2f"
                        ),
                        "category": "Category",
                        "description": "Description",
                        "expense_date": "Date",
                    },
                )
                options = {
                    f"{row['expense_date']} · {row['category']} · "
                    f"{money(row['amount'])} · {row['description'] or 'No note'}":
                    row["id"]
                    for row in transactions
                }
                selected = st.selectbox(
                    "Select a transaction to remove", list(options), key="expense_delete"
                )
                if st.button("Delete selected transaction", icon=":material/delete:"):
                    try:
                        api_request(
                            "DELETE",
                            f"/expenses/{options[selected]}",
                            params={"user_id": user["id"]},
                        )
                        st.success("Transaction deleted.")
                        st.rerun()
                    except ApiError as error:
                        show_api_error(error)
