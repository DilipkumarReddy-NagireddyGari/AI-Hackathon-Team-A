"""Streamlit application shell for the T01 foundation."""

from collections.abc import Callable
from pathlib import Path

import streamlit as st

from .database import check_database, create_database_engine
from .settings import Settings, get_settings

PageRenderer = Callable[[], None]


def render_home() -> None:
    st.title("Home")
    st.write("Your personalized Japanese workplace learning home will appear here.")


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
    st.info("Demo authentication and learner profiles will be added in later increments.")


PAGE_RENDERERS: dict[str, PageRenderer] = {
    "Home": render_home,
    "Learn": render_learn,
    "Translate": render_translate,
    "Progress": render_progress,
    "Profile": render_profile,
}


def render_health_panel(settings: Settings) -> None:
    """Show operational readiness without revealing configuration values."""

    project_root = Path(__file__).resolve().parents[2]
    engine = create_database_engine(settings, project_root)
    health = check_database(engine)
    engine.dispose()

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


def main() -> None:
    settings = get_settings()
    st.set_page_config(page_title=settings.app_name, page_icon="🎌", layout="wide")
    st.sidebar.title(settings.app_name)
    selected_page = st.sidebar.radio("Navigation", PAGE_RENDERERS.keys())
    render_health_panel(settings)
    PAGE_RENDERERS[selected_page]()


if __name__ == "__main__":
    main()
