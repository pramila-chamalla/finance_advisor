import streamlit as st

from common import ApiError, api_request, page_heading, require_user, show_api_error


def render() -> None:
    user = require_user()
    if user is None:
        return

    page_heading(
        "YOUR PROFILE",
        "Your details, your control",
        "Keep your monthly income current so your budget suggestions stay useful.",
    )
    with st.container(border=True):
        st.subheader("Personal finance profile")
        with st.form("update_profile"):
            name = st.text_input("Name", value=user["name"], max_chars=100)
            email = st.text_input("Email", value=user["email"], max_chars=254)
            left, right = st.columns(2)
            age = left.number_input(
                "Age", min_value=18, max_value=120, value=int(user["age"])
            )
            salary = right.number_input(
                "Monthly take-home income (₹)",
                min_value=0.0,
                value=float(user["salary"]),
                step=1000.0,
            )
            submitted = st.form_submit_button(
                "Save profile", type="primary", width="stretch"
            )
        if submitted:
            try:
                result = api_request(
                    "PUT",
                    f"/users/{user['id']}",
                    payload={
                        "name": name,
                        "email": email,
                        "age": int(age),
                        "salary": salary,
                    },
                )
                st.session_state["user"] = result["user"]
                st.success("Your profile has been updated.")
                st.rerun()
            except ApiError as error:
                show_api_error(error)

    st.warning(
        "This local demo has no password-based authentication. "
        "Use it only with non-sensitive sample data on a trusted device."
    )
