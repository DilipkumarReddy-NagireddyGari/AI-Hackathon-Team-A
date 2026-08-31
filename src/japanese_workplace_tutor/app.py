"""Streamlit application with persistent local demo authentication."""

from collections.abc import Callable
from pathlib import Path

import streamlit as st
from sqlalchemy import Engine

from .auth import AuthenticationError, AuthenticationService, RegistrationError
from .database import check_database, create_database_engine
from .profile import (
    JapaneseLevel,
    ProfileRecord,
    ProfileService,
    ProfileValidationError,
    ROLE_TASK_SUGGESTIONS,
)
from .settings import Settings, get_settings

PageRenderer = Callable[[], None]


def render_home(profile: ProfileRecord | None = None) -> None:
    st.title("Home")
    username = st.session_state.get("authenticated_username")
    st.write(f"Welcome, {username}.")
    if profile is None:
        st.info("Complete your learner profile to personalize your learning.")
        return
    st.subheader(f"{profile.role} · {profile.declared_level.value}")
    st.write("Focus tasks: " + ", ".join(profile.tasks))
    if profile.tools_domain:
        st.caption(f"Tools and domain: {profile.tools_domain}")
    st.info("Your first personalized lesson will be available in the next increment.")


def render_learn() -> None:
    st.title("Learn")
    st.info("Lesson generation will be added in a later increment.")


def render_translate() -> None:
    st.title("Translate")
    st.info("Workplace translation will be added in a later increment.")


def render_progress() -> None:
    st.title("Progress")
    st.info("Progress tracking will be added in a later increment.")


def _set_suggested_tasks(role_key: str, tasks_key: str) -> None:
    selected_role = st.session_state.get(role_key, "")
    st.session_state[tasks_key] = list(ROLE_TASK_SUGGESTIONS.get(selected_role, ()))


def render_profile_editor(
    service: ProfileService,
    user_id: int,
    profile: ProfileRecord | None,
) -> None:
    onboarding = profile is None
    prefix = f"{'onboarding' if onboarding else 'profile'}_{user_id}"
    role_key = f"{prefix}_role"
    tasks_key = f"{prefix}_tasks"

    if onboarding:
        st.title("Set up your learner profile")
        st.write("Tell us about your work so lessons can match your day-to-day needs.")
    else:
        st.title("Profile")
        st.caption("Update the details used to personalize future lessons.")

    role_options = list(ROLE_TASK_SUGGESTIONS)
    if profile is not None and profile.role not in role_options:
        role_options.insert(0, profile.role)
    selected_role = st.selectbox(
        "Role or title",
        role_options,
        index=role_options.index(profile.role) if profile is not None else 0,
        accept_new_options=True,
        key=role_key,
        help="Search common roles or enter your own.",
        on_change=(
            _set_suggested_tasks
            if onboarding
            else None
        ),
        args=(role_key, tasks_key) if onboarding else None,
    )

    suggested_tasks = list(ROLE_TASK_SUGGESTIONS.get(selected_role, ()))
    selected_tasks = list(profile.tasks) if profile is not None else suggested_tasks
    task_options = list(dict.fromkeys([*selected_tasks, *suggested_tasks]))
    tasks = st.multiselect(
        "Typical tasks",
        task_options,
        default=None if tasks_key in st.session_state else selected_tasks,
        accept_new_options=True,
        key=tasks_key,
        help="Remove suggestions that do not fit, or enter edited and additional tasks.",
    )
    tools_domain = st.text_area(
        "Technologies, tools, or business domain (optional)",
        value=profile.tools_domain or "" if profile is not None else "",
        max_chars=2000,
        key=f"{prefix}_tools_domain",
    )
    level_values = [level.value for level in JapaneseLevel]
    declared_level = st.selectbox(
        "Self-reported Japanese level",
        level_values,
        index=(
            level_values.index(profile.declared_level.value)
            if profile is not None
            else 0
        ),
        key=f"{prefix}_declared_level",
    )
    romaji_preference = st.toggle(
        "Show romaji support",
        value=profile.romaji_preference if profile is not None else False,
        key=f"{prefix}_romaji",
        help="Optional reading support, especially for complete beginners.",
    )

    if profile is None or profile.estimated_working_level is None:
        st.caption("Estimated working level: Not set")
    else:
        st.caption(f"Estimated working level: {profile.estimated_working_level.value}")
    st.button(
        "Take optional placement",
        disabled=True,
        help="Optional placement will be available in a later increment.",
        key=f"{prefix}_placement",
    )

    submit_label = "Save profile" if onboarding else "Save changes"
    if st.button(submit_label, type="primary", key=f"{prefix}_submit"):
        try:
            if onboarding:
                service.create_profile(
                    user_id,
                    role=selected_role,
                    tasks=tasks,
                    tools_domain=tools_domain,
                    declared_level=declared_level,
                    romaji_preference=romaji_preference,
                )
            else:
                service.update_profile(
                    user_id,
                    role=selected_role,
                    tasks=tasks,
                    tools_domain=tools_domain,
                    declared_level=declared_level,
                    romaji_preference=romaji_preference,
                )
        except ProfileValidationError as error:
            st.error(str(error))
        else:
            if onboarding:
                st.rerun()
            st.success("Profile saved.")


def render_profile(
    service: ProfileService | None = None,
    user_id: int | None = None,
    profile: ProfileRecord | None = None,
) -> None:
    if service is None or user_id is None:
        st.title("Profile")
        st.info("Sign in to view your learner profile.")
        return
    render_profile_editor(service, user_id, profile)


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

    user_id = int(st.session_state.authenticated_user_id)
    profile_service = ProfileService(engine)
    profile = profile_service.get_profile(user_id)
    if profile is None:
        render_profile_editor(profile_service, user_id, None)
        engine.dispose()
        return

    selected_page = st.sidebar.radio("Navigation", PAGE_RENDERERS.keys())
    if selected_page == "Home":
        render_home(profile)
    elif selected_page == "Profile":
        render_profile(profile_service, user_id, profile)
    else:
        PAGE_RENDERERS[selected_page]()
    engine.dispose()


if __name__ == "__main__":
    main()
