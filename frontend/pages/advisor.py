import streamlit as st

from common import ApiError, api_request, page_heading, require_user, show_api_error


def render() -> None:
    user = require_user()
    if user is None:
        return

    page_heading(
        "A FINANCIAL GUIDE, ON DEMAND",
        "Your AI money coach",
        "Ask about budgeting, tracked spending or savings goals. You control whether "
        "a question uses an external AI provider.",
    )
    st.caption(
        "Educational guidance only — the coach cannot guarantee returns or replace "
        "a qualified financial professional."
    )
    st.info(
        "Without consent, FinGenie uses a local budget-based response. If you opt in, "
        "your question and a summary of income, spending categories and goal balances "
        "are sent to the configured AI provider. Your name, email and transaction "
        "descriptions are not included."
    )
    use_ai = st.checkbox(
        "Allow the AI provider to receive my question and summarized finance data",
        value=False,
        key="advisor_ai_consent",
    )

    try:
        history = api_request("GET", f"/chat/{user['id']}")["messages"]
    except ApiError as error:
        show_api_error(error)
        return

    for message in history:
        with st.chat_message("user"):
            st.markdown(message["question"])
        with st.chat_message("assistant"):
            st.markdown(message["response"])
            if message["id"] == st.session_state.get("last_coach_message_id"):
                if st.session_state.get("last_coach_mode") == "ai":
                    st.caption("Answered by the configured AI provider.")
                elif st.session_state.get("last_coach_consent"):
                    st.caption(
                        "No provider key is configured; this response was generated locally."
                    )
                else:
                    st.caption(
                        "Answered locally; no finance summary was sent to an AI provider."
                    )

    prompt = st.chat_input("Ask a money question...")
    if prompt:
        try:
            with st.spinner("Thinking through your plan..."):
                result = api_request(
                    "POST",
                    "/chat",
                    payload={
                        "user_id": user["id"],
                        "question": prompt,
                        "use_ai": use_ai,
                    },
                )
            st.session_state["last_coach_message_id"] = result["id"]
            st.session_state["last_coach_mode"] = result["mode"]
            st.session_state["last_coach_consent"] = use_ai
            st.rerun()
        except ApiError as error:
            show_api_error(error)

