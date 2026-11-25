import streamlit as st

from common import ApiError, api_request, money, page_heading, require_user, show_api_error


def render() -> None:
    user = require_user()
    if user is None:
        return

    page_heading(
        "SMALL STEPS, BIG PLANS",
        "Savings goals",
        "Give your future plans a name, a target and a steady monthly contribution.",
    )
    try:
        goals = api_request("GET", f"/goals/{user['id']}")["goals"]
    except ApiError as error:
        show_api_error(error)
        return

    add_column, goals_column = st.columns([0.85, 1.15], gap="large")
    with add_column:
        with st.container(border=True):
            st.subheader("Create a goal")
            with st.form("create_goal", clear_on_submit=True):
                name = st.text_input(
                    "What are you saving for?", max_chars=100, placeholder="Emergency fund"
                )
                target = st.number_input(
                    "Target amount (₹)", min_value=0.0, step=5000.0
                )
                saved = st.number_input(
                    "Already saved (₹)", min_value=0.0, step=1000.0
                )
                submitted = st.form_submit_button(
                    "Add savings goal", type="primary", width="stretch"
                )
            if submitted:
                if target <= 0:
                    st.warning("Set a target greater than zero.")
                elif saved > target:
                    st.warning("Your saved amount cannot exceed the target.")
                else:
                    try:
                        api_request(
                            "POST",
                            "/goals",
                            payload={
                                "user_id": user["id"],
                                "goal_name": name,
                                "target_amount": target,
                                "current_amount": saved,
                            },
                        )
                        st.success("Your goal is ready.")
                        st.rerun()
                    except ApiError as error:
                        show_api_error(error)

    with goals_column:
        if not goals:
            with st.container(border=True):
                st.subheader("Your goals")
                st.info(
                    "Create a goal to track an emergency fund, a trip, a home deposit "
                    "or anything meaningful to you."
                )
        else:
            for goal in goals:
                with st.container(border=True):
                    target = float(goal["target_amount"])
                    saved = float(goal["saved_amount"])
                    progress = min(saved / target, 1.0)
                    st.subheader(goal["goal_name"])
                    st.progress(progress)
                    st.caption(
                        f"{money(saved)} saved · {money(max(target - saved, 0))} to go "
                        f"· {progress:.0%} complete"
                    )

            goal_options = {
                f"{goal['goal_name']} · {money(goal['saved_amount'])} saved "
                f"of {money(goal['target_amount'])}": goal
                for goal in goals
            }
            selected_label = st.selectbox(
                "Choose a goal to update", list(goal_options), key="goal_selected"
            )
            selected_goal = goal_options[selected_label]
            remaining = max(
                float(selected_goal["target_amount"])
                - float(selected_goal["saved_amount"]),
                0,
            )
            action_columns = st.columns([1, 1])
            with action_columns[0]:
                with st.form("add_contribution", clear_on_submit=True):
                    contribution = st.number_input(
                        "Add a contribution (₹)",
                        min_value=0.0,
                        max_value=remaining if remaining > 0 else 0.0,
                        step=500.0,
                    )
                    submitted = st.form_submit_button(
                        "Record contribution", width="stretch"
                    )
                if submitted:
                    if contribution <= 0:
                        st.warning("Enter a contribution greater than zero.")
                    else:
                        try:
                            api_request(
                                "POST",
                                f"/goals/{selected_goal['id']}/contributions",
                                payload={
                                    "user_id": user["id"],
                                    "amount": contribution,
                                },
                            )
                            st.success("Contribution recorded.")
                            st.rerun()
                        except ApiError as error:
                            show_api_error(error)
            with action_columns[1]:
                st.write("")
                st.write("")
                if st.button(
                    "Delete this goal",
                    icon=":material/delete:",
                    width="stretch",
                ):
                    try:
                        api_request(
                            "DELETE",
                            f"/goals/{selected_goal['id']}",
                            params={"user_id": user["id"]},
                        )
                        st.success("Goal deleted.")
                        st.rerun()
                    except ApiError as error:
                        show_api_error(error)
