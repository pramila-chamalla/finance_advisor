import streamlit as st

from common import ApiError, api_request, money, page_heading, require_user, show_api_error


def render() -> None:
    user = require_user()
    if user is None:
        return

    page_heading(
        "YOUR FINANCIAL SNAPSHOT",
        "A clearer view of your money",
        "Your monthly plan, spending and next best steps — together in one place.",
    )
    try:
        with st.spinner("Bringing your finances together..."):
            data = api_request("GET", f"/dashboard/{user['id']}")
    except ApiError as error:
        show_api_error(error)
        return

    profile = data["profile"]
    plan = data["plan"]
    report = plan["report"]
    salary = float(profile["salary"])
    spent = float(report["expenses"])
    saved = float(report["savings"])

    st.markdown(
        f"""
        <div class="welcome-card">
          <div style="font-size:.76rem;letter-spacing:.13em;text-transform:uppercase">
            {data['month']} · YOUR MONTHLY MONEY PLAN
          </div>
          <h2>Make room for what matters.</h2>
          <p>Your income is allocated across essentials, everyday choices and future goals.
          Update your transactions as you go to keep the picture current.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics = st.columns(4)
    metrics[0].metric("Monthly income", money(salary))
    metrics[1].metric("Tracked spending", money(spent))
    metrics[2].metric(
        "Left this month",
        money(saved),
        delta=f"{report['savings_rate']:.0f}% of income",
        delta_color="normal" if saved >= 0 else "inverse",
    )
    metrics[3].metric("Money health", f"{plan['health_score']:.0f} / 100")

    st.write("")
    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        with st.container(border=True):
            st.subheader("Your 50 / 30 / 20 starting point")
            st.caption("A flexible guide, not a rule. Adjust it to your real costs.")
            budget = plan["budget"]
            budget_columns = st.columns(3)
            budget_columns[0].metric("Needs · 50%", money(budget["needs"]))
            budget_columns[1].metric("Wants · 30%", money(budget["wants"]))
            budget_columns[2].metric("Savings · 20%", money(budget["savings"]))
            st.progress(min(max(spent / salary, 0.0), 1.0) if salary else 0.0)
            st.caption(
                f"{money(spent)} of {money(salary)} income is in this month's "
                "tracked expenses."
            )

        with st.container(border=True):
            st.subheader("Where your spending goes")
            categories = plan["expense_analysis"]["by_category"]
            if categories:
                st.bar_chart(
                    [
                        {"Category": category, "Amount": amount}
                        for category, amount in categories.items()
                    ],
                    x="Category",
                    y="Amount",
                    color="#2f684d",
                )
            else:
                st.info("Your category chart will appear after you add an expense.")
            st.page_link(
                st.session_state["_fingenie_pages"]["expenses"],
                label="View all transactions",
                icon=":material/arrow_forward:",
            )

    with right:
        with st.container(border=True):
            st.subheader("Your next best steps")
            for recommendation in data["recommendations"]:
                st.markdown(
                    f"**{recommendation['title']}**  \n"
                    f"{recommendation['detail']}"
                )
                st.caption(recommendation["agent"])
                st.divider()

        with st.container(border=True):
            st.subheader("Goals in progress")
            if data["goals"]:
                for goal in data["goals"][:3]:
                    progress = min(
                        float(goal["saved_amount"]) / float(goal["target_amount"]),
                        1.0,
                    )
                    st.markdown(f"**{goal['goal_name']}**")
                    st.progress(progress)
                    st.caption(
                        f"{money(goal['saved_amount'])} saved of "
                        f"{money(goal['target_amount'])}"
                    )
            else:
                st.caption("Give your savings a destination by creating a goal.")
            st.page_link(
                st.session_state["_fingenie_pages"]["goals"],
                label="Explore savings goals",
                icon=":material/arrow_forward:",
            )

    if data["recent_expenses"]:
        st.subheader("Latest transactions")
        st.dataframe(
            data["recent_expenses"],
            hide_index=True,
            width="stretch",
            column_config={
                "id": None,
                "amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
                "category": "Category",
                "description": "Description",
                "expense_date": "Date",
            },
        )
