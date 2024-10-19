import streamlit as st
from streamlit_msal_2 import init_auth


st.title("Streamlit MSAL Example")

client_id = "your_client_id"
tenant_id = "your_tenant_id"
user_roles = {
    "Admin": "Admin role",
    "User": "User role",
}

init_auth(user_roles, tenant_id, client_id)

st.write(f"Welcome, {st.session_state.username}")
