import os
import streamlit as st
from streamlit_msal import Msal


def init_auth(
    user_roles: dict = None,
    tenant_id: str = None,
    client_id: str = None,
    email_suffix: str = None,
) -> None:
    """
    Initializes the authentication process.

    This function initializes the authentication process by checking the user's
    account and role. If the user's account is not valid or does not have the
    required role, the function stops and displays an error message. If the
    user's account is valid and has the required role, the function sets the
    necessary information to the session state. The user sign information is
    stored in `st.session_state.auth_data`, the user name is stored in
    `st.session_state.username`, and the user roles are stored in
    `st.session_state.roles`.

    Args:
        user_roles (dict): A dictionary containing the required roles. The keys
            are the role names and the values are the role descriptions. The
            default value is None. This corresponds to the user roles defined
            in the Azure App registration. The value of each key should be the
            value defined in the Azure App registration.
        tenant_id (str): The tenant ID in Microsoft Azure. If the `TENANT_ID`
            is already set in the environment variables, this argument is not
            required. If no `TENANT_ID` is found in the environment variables,
            and no passed value is provided, streamlit will stop.
        client_id (str): The client ID from Microsoft Azure App registration.
            If the `CLIENT_ID` is already set in the environment variables,
            this argument is not required. If no `CLIENT_ID` is found in the
            environment variables, and no passed value is provided, streamlit
            will stop.
        email_suffix (str): The email suffix to match with the enterprise email
            suffix. The default value is None. If it is None, the function will
            not check the email suffix. The email suffix such as
            `@microsoft.com` is used to check whether the login user's email
            has valid enterprise email.

    Examples:
        >>> user_roles = {
        ...     "Admin": "Admin role",
        ...     "User": "User role",
        ... }
        >>> tenant_id = "your_tenant_id"
        >>> client_id = "your_client_id"
        >>> email_suffix = "@microsoft.com"
        >>> init_auth(user_roles, tenant_id, client_id, email_suffix)
    """
    client_id = client_id or os.getenv("CLIENT_ID", None)
    tenant_id = tenant_id or os.getenv("TENANT_ID", None)

    if tenant_id is None or client_id is None:
        st.warning(
            "Tenant ID and client ID cannot be None! "
            f"Your input: tenant_id={tenant_id}, client_id={client_id}. \n"
            "Please set the TENANT_ID environment variable"
        )
        st.stop()

    with st.sidebar:
        auth_data = Msal.initialize_ui(
            client_id=client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            scopes=[],
            connecting_label="Connecting",
            disconnected_label="Disconnected",
            sign_in_label="Sign in",
            sign_out_label="Sign out",
        )

        if not auth_data:
            # not valid enterprise account
            st.warning("Invalid account! No permission found for you")
            st.stop()

        if email_suffix is not None:
            # in case to match with enterprise email suffix
            # e.g., @microsoft.com
            if email_suffix not in auth_data["account"]["username"]:
                st.warning("Invalid account! No permission found for you")
                st.stop()

        if _check_role(auth_data["idTokenClaims"], user_roles) is False:
            # check the login user has the required roles defined
            # in the Microsoft Azure App registration
            st.warning(
                f"Hello, {auth_data['account']['name']}, "
                "No permission found for you"
            )
            st.stop()

        if "auth_data" not in st.session_state:
            # set the names to the session state
            st.session_state.auth_data = auth_data
            st.session_state.username = auth_data["account"]["name"]

            st.session_state.roles = auth_data["idTokenClaims"]["roles"]


def _check_role(auth: dict, user_roles: dict) -> bool:
    """
    Check if the given authentication object has the required role.

    Args:
        auth (dict): The authentication object containing the user's roles.

    Returns:
        bool: True if the authentication object has the required role, False
            otherwise.
    """
    if not auth:
        return False
    if "roles" not in auth:
        return False

    for role in user_roles.values():
        if role in auth["roles"]:
            return True

    return False
