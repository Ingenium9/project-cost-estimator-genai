import streamlit as st
from utils.auth import register_page, login_page, logout

def account_management_page():
    st.set_page_config(layout="centered", page_title="Account Management")
    st.title("🔐 Account Management")

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        st.success(f"You are logged in as: **{st.session_state.get('username', '')}**")
        if st.button("Logout", type="primary"):
            logout()
    else:
        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab:
            login_page()
        with register_tab:
            register_page()

if __name__ == "__main__":
    account_management_page()