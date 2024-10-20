"""Yet another msal Single-Sign-On module of streamlit applications also for
`ConfidentialClientApplication` by checking required App roles of signed-in
users in the enterprise setup.

Functions:
    init_auth: Initializes the authentication process.
    refresh_obo_token: Checks if the user is logged in and refreshes the
        obo access token if necessary. This can be only used after configure
        the `init_auth` function with `init_obo_process=True`.

Examples:
    >>> import streamlit as st
    >>> from streamlit_msal_2 import init_auth, refresh_obo_token
    >>> st.title("Streamlit MSAL Example")
    >>> client_id = "your_client_id"
    >>> tenant_id = "your_tenant_id"
    >>> user_roles = {
    ...     "ExampleApp.Admin": "ExampleApp.Admin",
    ...     "ExampleApp.User": "ExampleApp.User",
    ... }
    >>> init_auth(user_roles, tenant_id, client_id, init_obo_process=True)
    >>> st.write(f"Welcome, {st.session_state.username}")
    >>> refresh_obo_token(tenant_id, client_id, client_secret, scope)
"""

import os
import requests
import datetime
import time

import streamlit as st
from loguru import logger
from streamlit_msal import Msal


def init_auth(
    user_roles: dict = None,
    tenant_id: str = None,
    client_id: str = None,
    email_suffix: str = None,
    init_obo_process: bool = False,
    client_secret: str = None,
    downstream_scope=None,
    retry_times: int = 5,
) -> None:
    """
    Initializes the authentication process for streamlit applications. This
    function also supports obo (on-behalf-of) token acquisition process, which
    can be enabled by setting the `init_obo_process=True`. Note that
    `client_secret`, `downstream_scope`, and `retry_times` are only used when
    `init_obo_process=True`. The sign-in button is by default on the st.sidebar

    This function initializes the authentication process by checking the user's
    account and role. If the user's account is not valid or does not have the
    required role, the function stops and displays an error message. If the
    user's account is valid and has the required role, the function sets the
    necessary information to the session state. The user sign information is
    stored in `st.session_state.auth_data`, the user name is stored in
    `st.session_state.username`, and the user roles are stored in
    `st.session_state.roles`.

    The obo process can be triggered by setting the `init_obo_process=True`.
    The obo token information is stored in `st.session_state.obo_info`, this
    is a dictionary containing the `access_token`, `refresh_token`, and the
    `expires_at`. The `access_token` will be stored in system environment
    variables as `OBO_TOKEN`, and also `st.session_state.obo_token` for easy
    access.

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
        init_obo_process (bool): A boolean value to enable the obo token
            acquisition process. The default value is False. If set to True,
            the function will acquire the obo token.
        client_secret (str): The client secret for the `cliend_id` above. If
            the `CLIENT_SECRET` is already set in the environment variables,
            this argument is not required. If no `CLIENT_SECRET` is found in
            the environment variables, and no passed value is provided, error
            will be raised.
        downstream_scope (str): The scope for the obo token acquisition
            process. This is required when `init_obo_process=True`. Note that
            the scope here is the downstream API scope, not the scope of the
            provided `client_id` above.
        retry_times (int): The number of times to retry the token acquisition
            process. The default value is 5.

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

        if init_obo_process:
            obo_token = _acquire_access_token_obo(
                auth_data["idToken"],
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
                downstream_scope=downstream_scope,
                retry_times=retry_times,
            )
            if not obo_token:
                st.write(
                    "Failed acquiring token, refresh the page and login again!"
                )
                st.stop()
            st.session_state.obo_info = {
                "access_token": obo_token.get("access_token"),
                "refresh_token": obo_token.get("refresh_token"),
                "expires_at": datetime.datetime.now()
                + datetime.timedelta(seconds=obo_token.get("expires_in")),
            }
            os.environ["OBO_TOKEN"] = obo_token.get("access_token")
            st.session_state.obo_token = obo_token.get("access_token")


def refresh_obo_token(
    tenant_id: str = None,
    client_id: str = None,
    client_secret: str = None,
    downstream_scope=None,
) -> str:
    """
    Checks if the user is logged in and refreshes the obo access token if
    necessary.

    This function will store the full obo token information in the
    `st.session_state.obo_info` and the current access token in the
    `st.session_state.obo_token`. This function can be only run after
    the `init_auth` function is called, and the `init_obo_process` is set to
    `True`, in the background, it uses the `st.session_state.obo_info` in
    user sign in process.

    Returns:
        str: The refreshed access token.

    Raises:
        None
    """
    tokens = st.session_state.obo_info

    if not tokens:
        st.write("User not logged in")
        return None

    if tokens.get("expires_at") < datetime.datetime.now():
        logger.info("Refreshing access token...")

        new_tokens = _refresh_access_token(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            downstream_scope=downstream_scope,
            refresh_token=tokens.get("refresh_token"),
        )
        tokens["access_token"] = new_tokens.get("access_token")
        tokens["refresh_token"] = new_tokens.get("refresh_token")
        tokens["expires_at"] = datetime.datetime.now() + datetime.timedelta(
            seconds=new_tokens.get("expires_in")
        )
        st.session_state.obo_info = tokens
        os.environ["OBO_TOKEN"] = tokens["access_token"]
        st.session_state.obo_token = tokens["access_token"]
    return st.session_state.obo_info


def _refresh_access_token(
    tenant_id: str = None,
    client_id: str = None,
    client_secret: str = None,
    downstream_scope=None,
    refresh_token=None,
):
    """
    Refreshes the access token using the provided refresh token.

    Args:
        refresh_token (str): The refresh token to use for refreshing the
            access token.

    Returns:
        dict: A dictionary containing the response from the token endpoint.

    Raises:
        None
    """
    tenant_id = tenant_id or os.getenv("TENANT_ID", None)
    client_id = client_id or os.getenv("CLIENT_ID", None)
    client_secret = client_secret or os.getenv("CLIENT_SECRET", None)
    if tenant_id is None or client_id is None or client_secret is None:
        raise ValueError(
            "Tenant ID, Client ID, and Client Secret cannot be None!"
        )

    if refresh_token is None:
        refresh_token = st.session_state.obo_info["refresh_token"]
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": downstream_scope,
    }
    response = requests.post(
        "https://login.microsoftonline.com/"
        + tenant_id
        + "/oauth2/v2.0/token",
        data=payload,
    )
    return response.json()


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


def _acquire_access_token_obo(
    auth_id_token,
    tenant_id: str = None,
    client_id: str = None,
    client_secret: str = None,
    downstream_scope=None,
    retry_times=5,
):
    """
    Acquires an access token on behalf of a user using the provided token.

    Args:
        token (str): The token to be used for acquiring the access token.

    Returns:
        dict: The JSON response containing the acquired access token.

    Raises:
        requests.exceptions.RequestException
    """
    times = 1
    tenant_id = tenant_id or os.getenv("TENANT_ID", None)
    client_id = client_id or os.getenv("CLIENT_ID", None)
    client_secret = client_secret or os.getenv("CLIENT_SECRET", None)

    if tenant_id is None or client_id is None or client_secret is None:
        raise ValueError(
            "Tenant ID, Client ID, and Client Secret cannot be None!"
        )

    token_url = (
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    )

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "requested_token_use": "on_behalf_of",
        "scope": downstream_scope,
        "assertion": auth_id_token,
    }

    while times < retry_times:
        response = requests.post(token_url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                f"Token acquisition failed: {response.status_code} - {response.text}"
            )
            time.sleep(5)
            times += 1

    raise requests.exceptions.RequestException(
        f"Error acquiring token after {times} attempts"
    )
