import os
import tempfile
import streamlit as st


def browse_database():

    st.subheader("🗄️ Select Database")

    uploaded_db = st.file_uploader(
        "Browse Database",
        type=["db", "sqlite", "sqlite3"],
        help="Select a SQLite database from your computer.",
        key="querygenie_database"
    )

    if uploaded_db is not None:

        # Create temporary location
        temp_dir = tempfile.gettempdir()

        db_path = os.path.join(
            temp_dir,
            uploaded_db.name
        )

        # Save uploaded database
        with open(db_path, "wb") as file:
            file.write(uploaded_db.getbuffer())

        # Store database path
        st.session_state.active_database_path = db_path

    # Get currently selected database
    active_db = st.session_state.get(
        "active_database_path"
    )

    # Show selected database
    if active_db:

        st.success(
            f"Database connected: {os.path.basename(active_db)}"
        )

    else:

        st.info(
            "Please select a SQLite database first."
        )

    return active_db