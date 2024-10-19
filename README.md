# Streamlit-MSAL-2

![cd](https://github.com/xiepei1/streamlit-msal-2/actions/workflows/cd.yml/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This is a workaround for streamlit to use msal authentication process in an
enterprise environment.

## How it works?

* this package is using streamlit-msal in the background for the authentication.
    * however, streamlit-msal does not specially integrate msal ConfidentialClientApplication, while this is usually mandatorily required by enterprise use cases
* to simplify enterprise use cases, this package adds some additional role checking after streamlit-msal sign in
    * these required roles can be directly configured in the Microsoft Azure App registration.
    * by assigning user roles in App registration enterprise configuration, the authentication
process can automatically check the signed in user's App roles, if it fulfills the predefined user roles, users can go further in streamlit

## How to configure and use?

### Configure Azure App Registration

* go Microsoft [Azure portal](https://portal.azure.com)
* search `App registration`, and click into it
* select an existing `App registration`, or create a new one if you do not have
    * ![portal](./docs/assets/configure/app-regisration-azure-portal.png)

* click to copy your `tenant id` and `client id`
    * ![ids](./docs/assets/configure/copy-ids.png)

* add `App roles`
    * ![app-roles](./docs/assets/configure/add-app-roles.png)

* in `Authentication`, you have to add single-page application. for local test runs, if using streamlit default port, add `http://localhost:8501`

### Configure Enterprise Application

* go to `Enterprise Application` in `Overview` page
    * ![overview](./docs/assets/configure/overview-enterprise.png)

* add your target users, and remember to select the corresponding App roles you just created
    * ![users-groups](./docs/assets/configure/users-groups.png)

### Streamlit Python Code

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

Details check [example folder](./example/)
