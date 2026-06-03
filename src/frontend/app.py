import streamlit as st

from views.dashboard import render_main_dashboard


st.set_page_config(
    page_title="AI Gesture QA Dashboard",
    page_icon="🤖",
    layout="wide",
)


def init_app_state():
    if "token" not in st.session_state:
        st.session_state.token = None

    if "demo_user" not in st.session_state:
        st.session_state.demo_user = "demo_guest"


def main():
    init_app_state()
    render_main_dashboard()


if __name__ == "__main__":
    main()