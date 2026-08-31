"""Streamlit application with persistent local demo authentication."""

from collections.abc import Callable
from pathlib import Path

import streamlit as st
from sqlalchemy import Engine

from .auth import AuthenticationError, AuthenticationService, RegistrationError
from .database import check_database, create_database_engine
from .settings import Settings, get_settings

PageRenderer = Callable[[], None]


def render_home() -> None:
    st.title("Home")
    username = st.session_state.get("authenticated_username")
    st.write(f"Welcome, {username}.")
    st.info("Your personalized Japanese workplace learning home will appear here.")


def render_learn() -> None:
    st.title("Learn")
    st.info("Lesson generation will be added in a later increment.")


def render_translate() -> None:
    st.title("Translate")
    st.info("Workplace translation will be added in a later increment.")


def render_progress() -> None:
    st.title("Progress")
    st.info("Progress tracking will be added in a later increment.")


def render_profile() -> None:
    st.title("Profile")
    st.info("Learner profiles will be added in a later increment.")


PAGE_RENDERERS: dict[str, PageRenderer] = {
    "Home": render_home,
    "Learn": render_learn,
    "Translate": render_translate,
    "Progress": render_progress,
    "Profile": render_profile,
}


def render_health_panel(settings: Settings, engine: Engine) -> None:
    """Show operational readiness without revealing configuration values."""

    health = check_database(engine)

    with st.sidebar.expander("Startup health", expanded=True):
        if health.ready:
            st.success("Database: ready")
            st.caption("SQLite foreign keys: enabled")
        else:
            st.error(f"Database: {health.message.lower()}")

        if settings.model_configured:
            st.success("Model features: configured")
        else:
            st.warning("Model features unavailable: configuration is missing")
        st.caption("Secret values are never displayed.")


def render_authentication(service: AuthenticationService) -> bool:
    st.title("Demo authentication")
    st.caption("Local username and password access for this laptop demo.")
    authenticated = False

    sign_in_tab, register_tab = st.tabs(("Sign in", "Register"))
    with sign_in_tab:
        with st.form("sign_in_form"):
            username = st.text_input("Username", key="sign_in_username")
            password = st.text_input("Password", type="password", key="sign_in_password")
            sign_in = st.form_submit_button("Sign in", type="primary")
        if sign_in:
            try:
                user = service.authenticate(username, password)
            except AuthenticationError as error:
                st.error(str(error))
            else:
                st.session_state.authenticated_user_id = user.id
                st.session_state.authenticated_username = user.username
                authenticated = True

    with register_tab:
        with st.form("registration_form"):
            username = st.text_input("Username", key="registration_username")
            password = st.text_input(
                "Password",
                type="password",
                key="registration_password",
                help="Use 12-128 characters.",
            )
            register = st.form_submit_button("Create account", type="primary")
        if register:
            try:
                user = service.register(username, password)
            except RegistrationError as error:
                st.error(str(error))
            else:
                st.session_state.authenticated_user_id = user.id
                st.session_state.authenticated_username = user.username
                authenticated = True

    return authenticated


def clear_authenticated_session() -> None:
    st.session_state.pop("authenticated_user_id", None)
    st.session_state.pop("authenticated_username", None)


def main() -> None:
    settings = get_settings()
    st.set_page_config(page_title=settings.app_name, page_icon="🎌", layout="wide")
    project_root = Path(__file__).resolve().parents[2]
    engine = create_database_engine(settings, project_root)
    st.sidebar.title(settings.app_name)
    render_health_panel(settings, engine)

    service = AuthenticationService(engine)
    if "authenticated_user_id" not in st.session_state:
        authenticated = render_authentication(service)
        engine.dispose()
        if authenticated:
            st.rerun()
        return

    st.sidebar.caption(
        f"Signed in as {st.session_state.get('authenticated_username', 'local user')}"
    )
    if st.sidebar.button("Sign out"):
        clear_authenticated_session()
        engine.dispose()
        st.rerun()

    selected_page = st.sidebar.radio("Navigation", PAGE_RENDERERS.keys())
    PAGE_RENDERERS[selected_page]()
    engine.dispose()


if __name__ == "__main__":
    main()
