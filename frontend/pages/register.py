import streamlit as st

from common import ApiError, api_request, money, page_heading, show_api_error


def render() -> None:
    page_heading(
        "WELCOME TO FINGENIE",
        "Start with your money story",
        "Create a local profile to get a plan shaped around your monthly income.",
    )
    create_tab, return_tab = st.tabs(["Create a profile", "Open existing profile"])

    with create_tab:
        with st.form("create_profile", clear_on_submit=False):
            name = st.text_input("Your name", max_chars=100)
            email = st.text_input("Email address", max_chars=254)
            first, second = st.columns(2)
            age = first.number_input("Age", min_value=18, max_value=120, value=25)
            salary = second.number_input(
                "Monthly take-home income (₹)",
                min_value=0,
                step=1000,
                help="Enter your regular monthly income after tax.",
            )
            accepted = st.checkbox(
                "I understand this app stores my finance data locally for this demo."
            )
            submitted = st.form_submit_button(
                "Create my finance profile", type="primary", width="stretch"
            )
        if submitted:
            if not accepted:
                st.warning("Please confirm how your profile data is stored.")
            else:
                try:
                    result = api_request(
                        "POST",
                        "/users/register",
                        payload={
                            "name": name,
                            "email": email,
                            "age": int(age),
                            "salary": salary,
                        },
                    )
                    st.session_state["user"] = result["user"]
                    st.success(f"Welcome, {result['user']['name']}!")
                    st.switch_page(st.session_state["_fingenie_pages"]["dashboard"])
                except ApiError as error:
                    show_api_error(error)

    with return_tab:
        with st.form("open_profile"):
            email = st.text_input("Email address used for your profile")
            submitted = st.form_submit_button(
                "Open my profile", type="primary", width="stretch"
            )
        if submitted:
            try:
                result = api_request(
                    "POST", "/users/login", payload={"email": email}
                )
                st.session_state["user"] = result["user"]
                st.success(
                    f"Welcome back, {result['user']['name']} — "
                    f"monthly income {money(result['user']['salary'])}."
                )
                st.switch_page(st.session_state["_fingenie_pages"]["dashboard"])
            except ApiError as error:
                show_api_error(error)

    st.caption(
        "This demo uses email-only profile selection, not secure authentication. "
        "Do not enter sensitive personal, bank or card details."
    )
