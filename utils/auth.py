import streamlit as st
from utils.db import create_user, check_user

def register_page():
    st.subheader("Create New Account")
    with st.form("RegisterForm"):
        new_username = st.text_input("Username", key="reg_username")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        submitted = st.form_submit_button("Register")

        if submitted:
            if not new_username or not new_password or not confirm_password:
                st.error("All fields are required.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = create_user(new_username, new_password)
                if success:
                    st.success(message)
                    st.info("Please proceed to login.")
                else:
                    st.error(message)

def login_page():
    st.subheader("Login to Your Account")
    with st.form("LoginForm"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if check_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

def logout():
    if "logged_in" in st.session_state:
        del st.session_state["logged_in"]
    if "username" in st.session_state:
        del st.session_state["username"]
    st.success("You have been logged out.")
    st.rerun()