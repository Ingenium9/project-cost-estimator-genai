import streamlit as st
from dotenv import load_dotenv
from utils.db import connect_db 

load_dotenv()

if connect_db() is None:
    st.error("CRITICAL: Failed to connect to the database. User authentication and data storage will not work.")
else:
    print("Database connection appears successful from app.py.")


if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None


st.set_page_config(
    page_title="Project Cost Estimator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.sidebar.title("Navigation")


if st.session_state.get("logged_in", False):
    st.sidebar.success(f"Logged in as: {st.session_state.get('username', 'User')}")
    st.sidebar.page_link("pages/1_📈_Estimator.py", label="Estimator Tool")
    st.sidebar.page_link("pages/2_👤_Account.py", label="Manage Account")
else:
    st.sidebar.info("Please log in or register.")
    st.sidebar.page_link("pages/2_👤_Account.py", label="Login / Register")


# --- Landing Page Content (if not logged in, or general info) ---
st.header("Welcome to the Project Cost Estimator!")

if not st.session_state.get("logged_in", False):
    st.markdown("""
    This tool helps you estimate software project costs using the COCOMO model
    and provides AI-driven insights for optimization.

    **Please navigate to the Account page from the sidebar to Login or Register.**
    """)
else:
    st.markdown(f"""
    Hello **{st.session_state.get('username', 'User')}**! 
    
    You are logged in. Please use the sidebar navigation to access the **Estimator Tool** or manage your account.
    
    This tool helps you:
    -   Estimate project effort and duration using the **COCOMO model**.
    -   Calculate costs based on team composition and rates.
    -   Receive **AI-powered suggestions** for cost optimization and project insights.
    -   Export detailed cost breakdowns to **PDF or Excel**.
    """)

st.markdown("---")
st.caption("Powered by Python, Streamlit, MongoDB, and Groq AI.")