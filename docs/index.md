# Streamlit-MSAL-2: Yet Another MSAL for Streamlit

Yet another msal Single-Sign-On module of streamlit applications also for ConfidentialClientApplication by checking required App roles of signed-in users in the enterprise setup, and support obo flow.

![ci](https://github.com/xiepei1/streamlit-msal-2/actions/workflows/ci.yml/badge.svg)
![cd](https://github.com/xiepei1/streamlit-msal-2/actions/workflows/cd.yml/badge.svg)
![pylint](./badge/quality.svg)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/streamlit-msal-2)](https://pypi.org/project/streamlit-msal-2/)
[![PyPI](https://img.shields.io/pypi/v/streamlit-msal-2)](https://pypi.org/project/streamlit-msal-2/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/streamlit-msal-2)](https://pypi.org/project/streamlit-msal-2/)
[![Release](https://img.shields.io/github/v/release/xiepei1/streamlit-msal-2)](https://github.com/xiepei1/streamlit-msal-2/releases)
[![GitHub](https://img.shields.io/github/license/xiepei1/streamlit-msal-2)](https://github.com/xiepei1/streamlit-msal-2/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 1. Motivation

This is a workaround for streamlit to use msal authentication process in an enterprise environment, which in many cases using **ConfidentialClientApplication**, and requiring checking user roles.

## 2. How to Install

```bash
pip install streamlit-msal-2
```

## 3. How It Works

* this package is using [streamlit-msal](https://github.com/WilianZilv/streamlit_msal) in the background for the authentication.
    * however, [streamlit-msal](https://github.com/WilianZilv/streamlit_msal) does not specially integrate msal ConfidentialClientApplication, while this is usually mandatorily required by enterprise use cases
* to simplify enterprise use cases, this package adds some additional role checking after [streamlit-msal](https://github.com/WilianZilv/streamlit_msal) sign in
    * these required roles can be directly configured in the Microsoft Azure App registration.
    * by assigning user roles in App registration enterprise configuration, the authentication
process can automatically check the signed in user's App roles, if it fulfills the predefined user roles, users can go further in streamlit

## 4. How to Configure and Use

### 4.1 Configure Azure App Registration

* go Microsoft [Azure portal](https://portal.azure.com)
* search `App registration`, and click into it
* select an existing `App registration`, or create a new one if you do not have
    * ![portal](./assets/configure/app-regisration-azure-portal.png)

* click to copy your `tenant id` and `client id`
    * ![ids](./assets/configure/copy-ids.png)

* add `App roles`
    * ![app-roles](./assets/configure/add-app-roles.png)

* in `Authentication`, you have to add single-page application. for local test runs, if using streamlit default port, add `http://localhost:8501`

### 4.2 Configure Enterprise Application

* go to `Enterprise Application` in `Overview` page
    * ![overview](./assets/configure/overview-enterprise.png)

* add your target users, and remember to select the corresponding App roles you just created
    * ![users-groups](./assets/configure/users-groups.png)

### 4.3 Authentication Base Use Case

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

Details check [example folder](https://github.com/xiepei1/streamlit-msal-2/tree/main/docs/example)

### 4.4 OBO Process

* obo token generation process can be triggered in `init_auth`, by setting the argument `init_obo_process=True`
* if you do not need obo process, just keep the default setting, not to set `init_obo_process` to `True`, since it will raise error if you miss additionally required arguments

* additional arguments need to be provided for obo process, including the `client_secret` of the original `client_id`, the scope of the downstream API
* obo token generation process stores the information in `st.session_state.obo_info`

* `st.session_state.obo_info` is a dictionary:

```python
{
    "obo_token": "...",
    "refresh_token": "...",
    "expires_at": "..."
}
```

* For easy-to-use reasons, the 'obo_token' is also stored at `st.session_state.obo_token` and system environment variable 'OBO_TOKEN'

* Usage example:

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

## 5. Known Issues and Limitations

* the client_secret is not actually integrated into the process, the [streamlit-msal](https://github.com/WilianZilv/streamlit_msal) package is in the background using PublicClientApplication sign in process. yet by defining the required App roles of user, it still can work to certain extend to make sure the sign-in user is the actually the target user
