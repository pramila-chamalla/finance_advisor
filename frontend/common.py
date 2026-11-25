import os
from typing import Any

import requests
import streamlit as st


API_URL = os.getenv("FINANCE_API_URL", "http://127.0.0.1:8000").rstrip("/")


class ApiError(RuntimeError):
    pass


def api_request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            json=payload,
            params=params,
            timeout=15,
        )
    except requests.ConnectionError as error:
        raise ApiError(
            "The API is not reachable. Start the FastAPI server and try again."
        ) from error
    except requests.Timeout as error:
        raise ApiError("The API request timed out. Please try again.") from error

    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ApiError(str(detail))
    try:
        return response.json()
    except ValueError as error:
        raise ApiError("The API returned an invalid response.") from error


def current_user() -> dict[str, Any] | None:
    return st.session_state.get("user")


def require_user() -> dict[str, Any] | None:
    user = current_user()
    if user is None:
        st.info("Create your free profile to see your personal finance dashboard.")
        st.page_link(
            st.session_state["_fingenie_pages"]["register"],
            label="Create or open your profile",
        )
    return user


def page_heading(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)


def money(value: float | int) -> str:
    return f"₹{float(value):,.0f}"


def show_api_error(error: ApiError) -> None:
    st.error(str(error))


def show_sidebar_user() -> None:
    user = current_user()
    if not user:
        st.sidebar.caption("Your personal money workspace")
        return
    st.sidebar.markdown(
        f"**{user['name']}**  \n"
        f"<span class='sidebar-email'>{user['email']}</span>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Switch profile", width="stretch"):
        st.session_state.pop("user", None)
        st.rerun()
