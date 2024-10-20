# Streamlit-MSAL-2: Yet Another MSAL for Streamlit

Yet another msal Single-Sign-On module of streamlit applications also for ConfidentialClientApplication by checking required App roles of signed-in users in the enterprise setup, and support obo flow.

![ci](https://github.com/xiepei1/streamlit-msal-2/actions/workflows/ci.yml/badge.svg)
![cd](https://github.com/xiepei1/streamlit-msal-2/actions/workflows/cd.yml/badge.svg)
![pylint](/docs/badge/quality.svg)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/streamlit-msal-2)](https://pypi.org/project/streamlit-msal-2/)
[![PyPI](https://img.shields.io/pypi/v/streamlit-msal-2)](https://pypi.org/project/streamlit-msal-2/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/streamlit-msal-2)](https://pypi.org/project/streamlit-msal-2/)
[![Release](https://img.shields.io/github/v/release/xiepei1/streamlit-msal-2)](https://github.com/xiepei1/streamlit-msal-2/releases)
[![GitHub](https://img.shields.io/github/license/xiepei1/streamlit-msal-2)](https://github.com/xiepei1/streamlit-msal-2/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This is a workaround of streamlit to use msal authentication process in an enterprise environment for ConfidentialClientApplication.

## How to install and use

* run pip install

```bash
pip install streamlit-msal-2
```

* integrate the package in your streamlit code

```python
import streamlit as st
from streamlit_msal_2 import init_auth


st.title("Streamlit MSAL Example")

client_id = "your_client_id"
tenant_id = "your_tenant_id"
user_roles = {
    "ExampleApp.Admin": "ExampleApp.Admin",
    "ExampleApp.User": "ExampleApp.User",
}

init_auth(user_roles, tenant_id, client_id)

st.write(f"Welcome, {st.session_state.username}")
```

The user sign information is stored in `st.session_state.auth_data`, the user name is stored in `st.session_state.username`, and the user roles are stored in `st.session_state.roles`.

## OBO Process

The obo token generation process can be triggered in `init_auth`, additional
arguments need to be provided. The obo token generation process stores the
information in `st.session_state.obo_info` and `st.session_state.obo_token`.

```python
import streamlit as st
from streamlit_msal_2 import init_auth, refresh_obo_token


st.title("Streamlit MSAL Example")

client_id = "your_client_id"
tenant_id = "your_tenant_id"
user_roles = {
    "ExampleApp.Admin": "ExampleApp.Admin",
    "ExampleApp.User": "ExampleApp.User",
}

client_secret = "your_client_secret"
downstream_scope = "your downstream API scope to be called on-behalf-of user"

init_auth(user_roles, tenant_id, client_id,
  init_obo_process=True, client_secret=client_secret, downstream_scope=downstream_scope)

st.write(f"Welcome, {st.session_state.username}")

st.write(f"token for downstream API call {st.session_state.obo_token}")

# after a long time your token expires
refresh_obo_token(tenant_id, client_id, downstream_scope)
```

## How it works?

* this package is using streamlit-msal in the background for the authentication.
    * however, streamlit-msal does not specially integrate msal ConfidentialClientApplication, while this is usually mandatorily required by enterprise use cases
* to simplify enterprise use cases, this package adds some additional role checking after streamlit-msal sign in
    * these required roles can be directly configured in the Microsoft Azure App registration.
    * by assigning user roles in App registration enterprise configuration, the authentication
process can automatically check the signed in user's App roles, if it fulfills the predefined user roles, users can go further in streamlit

More to see [documentation site](https://xiepei1.github.io/streamlit-msal-2/).
