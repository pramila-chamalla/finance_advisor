import streamlit as st

from common import ApiError, api_request, show_sidebar_user
from pages import advisor, dashboard, expenses, goals, profile, register


st.set_page_config(
    page_title="FinGenie | Your money, in focus",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #17251f;
        --muted: #718078;
        --green: #2f684d;
        --mint: #e8f2eb;
        --paper: #f7f8f5;
        --line: #e7ebe6;
    }
    html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: #fff;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.4rem; }
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; letter-spacing: -0.035em; color: var(--ink); }
    h1 { font-size: clamp(2rem, 3.2vw, 2.7rem) !important; font-weight: 800 !important; }
    .eyebrow {
        color: var(--green); text-transform: uppercase; letter-spacing: .13em;
        font-size: .73rem; font-weight: 700; margin-bottom: -.8rem;
    }
    [data-testid="stMetric"] {
        background: white; border: 1px solid var(--line); border-radius: 18px;
        padding: 1.1rem 1.2rem; box-shadow: 0 4px 16px rgba(27,49,36,.035);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ink); font-family: 'Segoe UI', sans-serif; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: white; border-radius: 18px; border-color: var(--line);
    }
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 10px; font-weight: 600; min-height: 2.65rem;
    }
    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
        background: var(--green); border-color: var(--green);
    }
    [data-testid="stProgressBar"] > div > div { background: var(--green); }
    .sidebar-email { color: #78847d; font-size: .78rem; }
    .welcome-card {
        background: linear-gradient(120deg, #173b2a, #2f684d);
        color: #f5faf6; border-radius: 22px; padding: 1.8rem 2rem;
        margin: .5rem 0 1.5rem;
    }
    .welcome-card h2 { color: white; margin: .15rem 0 .45rem; }
    .welcome-card p { color: #d3e4d8; margin: 0; }
    .recommendation {
        border: 1px solid var(--line); border-left: 4px solid #5e9271;
        border-radius: 12px; background: white; padding: .9rem 1rem;
        margin: .55rem 0;
    }
    .recommendation.warning { border-left-color: #d49a3a; }
    .recommendation p { color: #68766e; margin: .3rem 0 0; font-size: .92rem; }
    .recommendation small { color: #829087; }
    .small-note { color: #78847d; font-size: .82rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=10, show_spinner=False)
def check_api_connection() -> None:
    api_request("GET", "/health")


st.sidebar.markdown(
    "<div style='font-family:Segoe UI;font-size:1.55rem;font-weight:800;"
    "letter-spacing:-.06em;color:#173b2a'>🌱 FinGenie</div>"
    "<div style='color:#718078;font-size:.82rem;margin:.15rem 0 1rem'>"
    "Your money, in focus</div>",
    unsafe_allow_html=True,
)
show_sidebar_user()

try:
    check_api_connection()
    st.sidebar.caption("● API connected")
except ApiError as error:
    st.sidebar.warning(str(error))

navigation_pages = {
    "dashboard": st.Page(
        dashboard.render,
        title="Overview",
        icon=":material/dashboard:",
        url_path="overview",
        default=True,
    ),
    "expenses": st.Page(
        expenses.render,
        title="Transactions",
        icon=":material/receipt_long:",
        url_path="transactions",
    ),
    "goals": st.Page(
        goals.render,
        title="Savings goals",
        icon=":material/flag:",
        url_path="goals",
    ),
    "advisor": st.Page(
        advisor.render,
        title="AI money coach",
        icon=":material/auto_awesome:",
        url_path="advisor",
    ),
    "profile": st.Page(
        profile.render,
        title="My profile",
        icon=":material/person:",
        url_path="profile",
    ),
    "register": st.Page(
        register.render,
        title="Get started",
        icon=":material/person_add:",
        url_path="get-started",
    ),
}
st.session_state["_fingenie_pages"] = navigation_pages
page = st.navigation(list(navigation_pages.values()), position="sidebar")
page.run()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div class='small-note'>Educational guidance only — not financial, "
    "tax or investment advice.</div>",
    unsafe_allow_html=True,
)
