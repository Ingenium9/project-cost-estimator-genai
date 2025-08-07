import streamlit as st
import pandas as pd
from utils.cocomo import calculate_cocomo, calculate_cost
from utils.ai_helper import get_ai_insights
from utils.export_utils import df_to_excel_bytes, create_pdf_report, generate_cost_pie_chart_bytes
from io import BytesIO
import json

CURRENCY_SYMBOL = "₹" 
TECH_STACK_OPTIONS = ["Python", "JavaScript", "Java", "C#", "Ruby", "PHP", "Swift", "Kotlin", "Go", "Rust", "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring Boot", "SQL", "NoSQL"]
PROJECT_TYPE_OPTIONS = ["Web Application", "Mobile Application (iOS)", "Mobile Application (Android)", "Mobile Application (Cross-Platform)", "Desktop Application", "API / Backend Service", "Data Science / ML Project", "Cloud Infrastructure", "Other"]
ROLE_TYPE_OPTIONS = ["Frontend", "Backend", "Full Stack", "Mobile Developer", "QA Engineer", "DevOps Engineer", "Project Manager", "Business Analyst", "UI/UX Designer", "Data Scientist"]
WORKFLOW_COMPLEXITY_OPTIONS = ["Simple (1-5 steps)", "Medium (6-15 steps)", "Complex (16-30 steps)", "Highly Complex (30+ steps)"]
USER_TYPES_OPTIONS = ["Public Users", "Registered Users", "Admin Users", "Internal Staff", "Third-party Integrations"]


def initialize_session_state_estimator():
    """Initializes session state variables for the estimator page."""
    defaults = {
        "roles_estimator_ui": [{"id": 0, "role_name": "Developer", "role_type": "Full Stack", "tech_stack_role": ["Python"], "count": 1, "rate_ph": 2000.0}],
        "next_role_id_estimator_ui": 1,
        "project_name_val_ui": "New Web Application",
        "project_description_val_ui": "A web application for...",
        "primary_tech_stack_val_ui": ["Python", "JavaScript"],
        "project_type_val_ui": "Web Application",
        "kloc_val_ui": 50.0,
        "cocomo_mode_selected_val_ui": "semi-detached",
        "contingency_val_ui": 10,
        "workflow_complexity_val_ui": WORKFLOW_COMPLEXITY_OPTIONS[0],
        "types_of_users_val_ui": [USER_TYPES_OPTIONS[0]],
        "show_results_estimator_ui": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def estimator_tool_page():
    st.set_page_config(layout="wide", page_title="Project Cost Estimator")
    
    if not st.session_state.get("logged_in", False):
        st.warning("Please log in to access the Estimator Tool.")
        st.page_link("pages/2_👤_Account.py", label="Go to Login/Register Page", icon="👤")
        st.stop()

    initialize_session_state_estimator() 

    st.title(f"🚀 Project Cost Estimator Tool")
    st.caption(f"Provide project details to get a cost estimate (in {CURRENCY_SYMBOL})")
    st.markdown("---")

    st.subheader("1. Basic Project Information")
    with st.container(border=True): 
        project_name_input = st.text_input(
            "Project Name", 
            value=st.session_state.project_name_val_ui, 
            key="project_name_widget_ui"
        )
        project_description_input = st.text_area(
            "Project Description", 
            value=st.session_state.project_description_val_ui, 
            key="project_description_widget_ui",
            height=100
        )

    st.subheader("2. Technical Details")
    with st.container(border=True):
        col_tech1, col_tech2 = st.columns(2)
        with col_tech1:
            primary_tech_stack_input = st.multiselect(
                "Primary Tech Stack", 
                options=TECH_STACK_OPTIONS, 
                default=st.session_state.primary_tech_stack_val_ui,
                key="primary_tech_stack_widget_ui"
            )
        with col_tech2:
            project_type_input = st.selectbox(
                "Project Type", 
                options=PROJECT_TYPE_OPTIONS, 
                index=PROJECT_TYPE_OPTIONS.index(st.session_state.project_type_val_ui) if st.session_state.project_type_val_ui in PROJECT_TYPE_OPTIONS else 0,
                key="project_type_widget_ui"
            )

    st.subheader("3. Development Team")
    st.caption("Add your team members with their roles and rates")
    with st.container(border=True):
        for i, role_item in enumerate(st.session_state.roles_estimator_ui):
            st.markdown(f"**Team Member {i+1}**")
            cols_role = st.columns([2, 2, 2, 1, 2, 0.5]) 
            with cols_role[0]:
                role_item["role_name"] = st.text_input("Role Name", value=role_item["role_name"], key=f"role_name_ui_{role_item['id']}", label_visibility="collapsed")
            with cols_role[1]:
                role_item["role_type"] = st.selectbox("Type", options=ROLE_TYPE_OPTIONS, 
                                                      index=ROLE_TYPE_OPTIONS.index(role_item["role_type"]) if role_item["role_type"] in ROLE_TYPE_OPTIONS else 0, 
                                                      key=f"role_type_ui_{role_item['id']}", label_visibility="collapsed")
            with cols_role[2]:
                role_item["tech_stack_role"] = st.multiselect("Tech Stack (Role)", options=TECH_STACK_OPTIONS, 
                                                              default=role_item["tech_stack_role"], 
                                                              key=f"role_tech_ui_{role_item['id']}", label_visibility="collapsed")
            with cols_role[3]:
                role_item["count"] = st.number_input("Count", min_value=1, value=role_item["count"], step=1, key=f"role_count_ui_{role_item['id']}", label_visibility="collapsed")
            with cols_role[4]:
                role_item["rate_ph"] = st.number_input(f"Rate/hr ({CURRENCY_SYMBOL})", min_value=0.0, value=role_item["rate_ph"], step=100.0, format="%.2f", key=f"role_rate_ui_{role_item['id']}", label_visibility="collapsed")
            with cols_role[5]:
                if st.button("🗑️", key=f"remove_role_ui_{role_item['id']}", help="Remove Team Member"):
                    st.session_state.roles_estimator_ui.pop(i)
                    st.rerun()
            if i < len(st.session_state.roles_estimator_ui) -1:
                 st.markdown("---")

        if st.button("➕ Add Team Member", key="add_team_member_ui_btn"):
            st.session_state.roles_estimator_ui.append({
                "id": st.session_state.next_role_id_estimator_ui,
                "role_name": "New Member", "role_type": ROLE_TYPE_OPTIONS[0], 
                "tech_stack_role": [TECH_STACK_OPTIONS[0]], "count": 1, "rate_ph": 1500.0
            })
            st.session_state.next_role_id_estimator_ui += 1
            st.rerun()

    st.subheader("4. Project Scope & Complexity")
    with st.container(border=True):
        col_scope1, col_scope2, col_scope3 = st.columns(3)
        with col_scope1:
            kloc_input = st.number_input(
                "Estimated KLOC (Kilo Lines of Code)", 
                min_value=0.1, value=st.session_state.kloc_val_ui, 
                step=0.1, format="%.1f", key="kloc_widget_ui"
            )
        with col_scope2:
            cocomo_options = ["organic", "semi-detached", "embedded"]
            cocomo_mode_input = st.selectbox(
                "COCOMO Project Mode", options=cocomo_options, 
                index=cocomo_options.index(st.session_state.cocomo_mode_selected_val_ui) if st.session_state.cocomo_mode_selected_val_ui in cocomo_options else 1, 
                key="cocomo_mode_widget_ui"
            )
        with col_scope3:
            contingency_percentage_input = st.slider(
                "Contingency Buffer (%)", 0, 30, 
                value=st.session_state.contingency_val_ui, 
                key="contingency_widget_ui"
            )

    st.subheader("5. User Workflow")
    with st.container(border=True):
        col_wf1, col_wf2 = st.columns(2)
        with col_wf1:
            workflow_complexity_input = st.selectbox(
                "Workflow Complexity", options=WORKFLOW_COMPLEXITY_OPTIONS,
                index=WORKFLOW_COMPLEXITY_OPTIONS.index(st.session_state.workflow_complexity_val_ui) if st.session_state.workflow_complexity_val_ui in WORKFLOW_COMPLEXITY_OPTIONS else 0,
                key="workflow_complexity_widget_ui"
            )
        with col_wf2:
            types_of_users_input = st.multiselect(
                "Types of Users", options=USER_TYPES_OPTIONS,
                default=st.session_state.types_of_users_val_ui,
                key="types_of_users_widget_ui"
            )
    
    st.markdown("---")

    if st.button(f"💰 Calculate Estimate & Get AI Insights", type="primary", use_container_width=True, key="main_calc_button_ui"):
        st.session_state.project_name_val_ui = project_name_input
        st.session_state.project_description_val_ui = project_description_input
        st.session_state.primary_tech_stack_val_ui = primary_tech_stack_input
        st.session_state.project_type_val_ui = project_type_input
        st.session_state.kloc_val_ui = kloc_input
        st.session_state.cocomo_mode_selected_val_ui = cocomo_mode_input
        st.session_state.contingency_val_ui = contingency_percentage_input
        st.session_state.workflow_complexity_val_ui = workflow_complexity_input
        st.session_state.types_of_users_val_ui = types_of_users_input

        active_roles_data = [
            {
                "role_name": role.get("role_name", "N/A"), 
                "count": role.get("count", 0),
                "rate_ph": role.get("rate_ph", 0.0)
            }
            for role in st.session_state.roles_estimator_ui
            if role.get("count", 0) > 0 and role.get("rate_ph", 0) >= 0
        ]
        
        valid_input = True
        if not active_roles_data and not any(role.get("count", 0) > 0 for role in st.session_state.roles_estimator_ui):
            st.error("Please define at least one team member with a count greater than zero.")
            valid_input = False
        elif kloc_input <= 0:
            st.error("KLOC must be greater than zero.")
            valid_input = False
        
        if not any(r.get('rate_ph',0) > 0 for r in active_roles_data) and any(r.get('count',0) > 0 for r in active_roles_data) and valid_input:
            st.warning(f"At least one role should have a rate greater than zero to calculate meaningful costs. Proceeding with {CURRENCY_SYMBOL}0 for roles with {CURRENCY_SYMBOL}0 rate.")

        if valid_input:
            with st.spinner("Calculating COCOMO and initial cost..."):
                effort_pm, duration_m = calculate_cocomo(kloc_input, cocomo_mode_input)
                
                if effort_pm is None: 
                    st.error("Invalid COCOMO mode selected.")
                    st.stop()

                subtotal_cost, total_cost_with_contingency, cost_breakdown_details = calculate_cost(
                    active_roles_data, duration_m, contingency_percentage_input
                )
                
                st.session_state.show_results_estimator_ui = True 
                st.session_state.cocomo_results_ui = {"effort_pm": effort_pm, "duration_m": duration_m}
                st.session_state.cost_summary_ui = {
                    "subtotal": subtotal_cost,
                    "total_with_contingency": total_cost_with_contingency,
                    "contingency_percentage": contingency_percentage_input,
                    "breakdown_details": cost_breakdown_details
                }
                project_all_inputs = {
                    "name": project_name_input, 
                    "description": project_description_input,
                    "primary_tech_stack": primary_tech_stack_input, # Keep as list for now, handle in export
                    "project_type": project_type_input,
                    "kloc": kloc_input, 
                    "cocomo_mode": cocomo_mode_input,
                    "roles_data": active_roles_data, 
                    "team_details_full": st.session_state.roles_estimator_ui, 
                    "contingency": contingency_percentage_input,
                    "workflow_complexity": workflow_complexity_input,
                    "types_of_users": types_of_users_input # Keep as list for now
                }
                st.session_state.project_inputs_ui = project_all_inputs

            with st.spinner("🤖 Generating AI-powered insights and optimizations... (This may take a moment)"):
                roles_details_for_ai = []
                for r_item in st.session_state.roles_estimator_ui:
                    if r_item.get("count",0) > 0:
                        role_str = (f"- Name: {r_item.get('role_name', 'N/A')}, "
                                    f"Type: {r_item.get('role_type', 'N/A')}, "
                                    f"Tech: {', '.join(r_item.get('tech_stack_role', ['N/A'])) if r_item.get('tech_stack_role') else 'N/A'}, "
                                    f"Count: {r_item.get('count',0)}, "
                                    f"Rate: {CURRENCY_SYMBOL}{r_item.get('rate_ph',0):,}/hr")
                        roles_details_for_ai.append(role_str)
                roles_data_str_for_ai = "\n".join(roles_details_for_ai)
                
                ai_context_for_prompt = (
                    f"Project Description: {project_description_input}\n"
                    f"Primary Tech Stack: {', '.join(primary_tech_stack_input) if primary_tech_stack_input else 'N/A'}\n"
                    f"Project Type: {project_type_input}\n"
                    f"Workflow Complexity: {workflow_complexity_input}\n"
                    f"User Types: {', '.join(types_of_users_input) if types_of_users_input else 'N/A'}\n"
                    f"Team Details:\n{roles_data_str_for_ai}"
                )

                ai_response = get_ai_insights( 
                    project_name_input, kloc_input, cocomo_mode_input, 
                    effort_pm, duration_m, total_cost_with_contingency, 
                    ai_context_for_prompt 
                )
                st.session_state.ai_insights_ui = ai_response
            
            st.success("Estimation and AI insights generated successfully!")

    if st.session_state.get("show_results_estimator_ui", False):
        st.markdown("---")
        st.header("📈 Estimation Results")

        cocomo_results = st.session_state.cocomo_results_ui
        cost_summary = st.session_state.cost_summary_ui
        project_inputs_for_export = st.session_state.project_inputs_ui
        ai_insights_for_display = st.session_state.ai_insights_ui

        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.metric(label="COCOMO Effort", value=f"{cocomo_results['effort_pm']} PM")
        with col_res2:
            st.metric(label="COCOMO Duration", value=f"{cocomo_results['duration_m']} Months")
        with col_res3:
            st.metric(label="Total Estimated Cost", 
                      value=f"{CURRENCY_SYMBOL}{cost_summary['total_with_contingency']:,.2f}",
                      help=f"Includes {cost_summary['contingency_percentage']}% contingency. Subtotal: {CURRENCY_SYMBOL}{cost_summary['subtotal']:,.2f}")

        st.markdown("---")
        
        tab_bd, tab_ai, tab_ex = st.tabs([f"📊 Cost Breakdown", f"💡 AI Insights & Optimizations", f"📥 Export Report"])

        with tab_bd:
            st.subheader(f"Detailed Cost Breakdown (in {CURRENCY_SYMBOL})")
            if cost_summary['breakdown_details']:
                breakdown_list = []
                for role, details in cost_summary['breakdown_details'].items():
                    breakdown_list.append({
                        "Item/Role": role,
                        "Count/Multiplier": details.get('count', '-'),
                        f"Rate/hr or Factor ({CURRENCY_SYMBOL})": details.get('rate_ph', '-'),
                        f"Monthly Cost ({CURRENCY_SYMBOL})": details.get('monthly_cost_per_person', '-'),
                        f"Total Cost ({CURRENCY_SYMBOL})": details.get('total_role_cost', 0)
                    })
                
                cost_df_for_export = pd.DataFrame(breakdown_list) 
                st.session_state.cost_breakdown_df_ui = cost_df_for_export

                cost_df_display = cost_df_for_export.copy()
                currency_cols_display = [
                    f"Rate/hr or Factor ({CURRENCY_SYMBOL})", 
                    f"Monthly Cost ({CURRENCY_SYMBOL})", 
                    f"Total Cost ({CURRENCY_SYMBOL})"
                ]
                for col_name in currency_cols_display:
                    if col_name in cost_df_display.columns:
                        is_numeric_col = pd.to_numeric(cost_df_display[col_name], errors='coerce').notna().all()
                        if is_numeric_col:
                             cost_df_display[col_name] = cost_df_display[col_name].apply(
                                 lambda x: f"{CURRENCY_SYMBOL}{float(x):,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x
                             )
                st.dataframe(cost_df_display, use_container_width=True, hide_index=True)
                
                chart_bytes = generate_cost_pie_chart_bytes(cost_summary['breakdown_details'])
                if chart_bytes:
                    st.image(chart_bytes, caption="Cost Distribution by Role/Item")
            else:
                st.info("No cost breakdown details available.")

        with tab_ai:
            st.subheader("🤖 AI-Powered Insights")
            if ai_insights_for_display:
                st.markdown(ai_insights_for_display)
            else:
                st.info("AI insights will appear here after estimation or if an error occurred.")
        
        with tab_ex:
            st.subheader("Download Your Report")
            if 'cost_breakdown_df_ui' in st.session_state and not st.session_state.cost_breakdown_df_ui.empty:
                cost_breakdown_df_to_export = st.session_state.cost_breakdown_df_ui
                
                # --- CORRECTED EXCEL INPUTS DATA PREPARATION ---
                excel_inputs_data = {}
                for k, v in project_inputs_for_export.items():
                    if k == "team_details_full" or k == "roles_data": # Handle list of dicts specifically
                        try:
                            excel_inputs_data[k] = json.dumps(v) # Convert list of dicts to JSON string
                        except TypeError:
                            excel_inputs_data[k] = str(v) # Fallback to generic string conversion
                    elif isinstance(v, list): # For other lists (like tech stack, user types)
                        excel_inputs_data[k] = ", ".join(str(item) for item in v) # Ensure all items are strings before joining
                    else:
                        excel_inputs_data[k] = v
                # --- END OF CORRECTION ---

                excel_dfs = {
                    "Inputs": pd.DataFrame([excel_inputs_data]), 
                    "COCOMO & Cost Summary": pd.DataFrame([{
                        **cocomo_results, 
                        f"Subtotal Cost ({CURRENCY_SYMBOL})": cost_summary['subtotal'], 
                        f"Total Cost with Contingency ({CURRENCY_SYMBOL})": cost_summary['total_with_contingency'],
                        "Contingency Percentage": cost_summary['contingency_percentage']
                    }]),
                    f"Cost Breakdown ({CURRENCY_SYMBOL})": cost_breakdown_df_to_export,
                    "AI Insights": pd.DataFrame({"Insights": [ai_insights_for_display if ai_insights_for_display else "N/A"]})
                }
                excel_bytes = df_to_excel_bytes(excel_dfs)
                st.download_button(
                    label="📥 Download Excel Report", data=excel_bytes,
                    file_name=f"{project_inputs_for_export.get('name', 'Project').replace(' ','_')}_Cost_Estimation_INR.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                pdf_bytes = create_pdf_report( 
                    project_data=project_inputs_for_export,
                    cocomo_results=cocomo_results, cost_summary=cost_summary,
                    cost_breakdown_df=cost_breakdown_df_to_export, 
                    ai_insights_raw=ai_insights_for_display if ai_insights_for_display else "No AI insights generated."
                )
                st.download_button(
                    label="📄 Download PDF Report", data=pdf_bytes,
                    file_name=f"{project_inputs_for_export.get('name', 'Project').replace(' ','_')}_Cost_Estimation_Report_INR.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("Generate an estimate to enable report downloads. Ensure a cost breakdown was calculated.")

    st.markdown("""
    <style>
        .stContainer [data-testid="stVerticalBlock"] { 
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        h3 { 
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }
        /* Add other styles from previous version if needed */
        .stButton>button {
            font-weight: bold;
        }
        .stMetric {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 15px;
        }
        .stTabs [data-baseweb="tab-list"] {
    		gap: 24px;
    	}
    	.stTabs [data-baseweb="tab"] {
    		height: 50px;
            white-space: pre-wrap;
    		background-color: #F0F0F0;
    		border-radius: 4px 4px 0px 0px;
    		gap: 1px;
    		padding-top: 10px;
    		padding-bottom: 10px;
    	}
    	.stTabs [aria-selected="true"] {
      		background-color: #FFFFFF; 
    	}
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    estimator_tool_page()