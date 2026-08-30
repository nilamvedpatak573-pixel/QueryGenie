import streamlit as st
import sqlite3
import pandas as pd
import os
from groq import Groq
import plotly.express as px
import speech_recognition as sr
import tempfile
from database_browser import browse_database

st.set_page_config(
    page_title="QueryGenie",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "querygenie.db"
)

client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)

if "app_page" not in st.session_state:
    st.session_state.app_page = "landing"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = None

if "query_result" not in st.session_state:
    st.session_state.query_result = None

if "user_question" not in st.session_state:
    st.session_state.user_question = ""

if "voice_question" not in st.session_state:
    st.session_state.voice_question = ""

if "last_question" not in st.session_state:
    st.session_state.last_question = ""

if "history" not in st.session_state:
    st.session_state.history = []

if "active_database_path" not in st.session_state:
    st.session_state.active_database_path = DATABASE_PATH

if "database_uploaded" not in st.session_state:
    st.session_state.database_uploaded = False

if "app_page" not in st.session_state:
    st.session_state.app_page = "landing"

def get_database_schema(connection):

    tables_query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """

    tables_df = pd.read_sql_query(
        tables_query,
        connection
    )

    schema_parts = []

    for table_name in tables_df["name"].tolist():

        columns_df = pd.read_sql_query(
            f'PRAGMA table_info("{table_name}")',
            connection
        )

        column_lines = []

        for _, row in columns_df.iterrows():

            column_lines.append(
                f"- {row['name']} ({row['type']})"
            )

        table_schema = (
            f"TABLE: {table_name}\n"
            + "\n".join(column_lines)
        )

        schema_parts.append(table_schema)

    return "\n\n".join(schema_parts)

# DYNAMIC SQL GENERATOR

def generate_sql(question, connection):

    # Get the complete database schema dynamically
    schema = get_database_schema(connection)

    prompt = f"""
You are QueryGenie, an expert SQLite database analyst.

Your task is to convert the user's natural-language
question into ONE valid SQLite SELECT query.

============================================================
DATABASE SCHEMA
============================================================

{schema}

============================================================
USER QUESTION
============================================================

{question}

============================================================
RULES
============================================================

1. Use ONLY tables and columns that exist in the database schema.
2. Never invent table names.
3. Never invent column names.
4. Use JOINs when information from multiple tables is required.
5. Use SQLite-compatible SQL.
6. Return ONLY one SQL query.
7. The query must start with SELECT.
8. Do not generate INSERT queries.
9. Do not generate UPDATE queries.
10. Do not generate DELETE queries.
11. Do not generate DROP queries.
12. Do not generate ALTER queries.
13. Do not generate CREATE queries.
14. Do not generate PRAGMA queries.
15. Do not generate ATTACH queries.
16. Do not generate DETACH queries.
17. Do not use markdown.
18. Do not provide explanations.
19. Return exactly one SQL query.

For text filtering:
- Use LOWER() when appropriate.
- Use LIKE for flexible text matching.

For highest values:
- Use ORDER BY ... DESC.

For lowest values:
- Use ORDER BY ... ASC.

If the user asks for the highest or lowest single item,
use LIMIT 1.

For questions asking for students, customers, employees,
products, or other entities where JOINs may produce duplicate
rows, use SELECT DISTINCT when the user wants a list of
unique entities.

For example:
SELECT DISTINCT s.student_id, s.student_name
FROM students s
JOIN marks m ON s.student_id = m.student_id
WHERE m.marks > 80

Do not use DISTINCT when the user is asking for individual
records, subject-wise marks, or all matching transactions.

Return ONLY the SQL query.
"""

    try:
        # AUTOMATICALLY FIND AN AVAILABLE GROQ MODEL
        available_models = client.models.list()

        available_model_ids = [
            model.id
            for model in available_models.data
            if getattr(model, "active", True)
        ]

        # Preferred models for SQL generation.
        preferred_models = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ]

        selected_model = None

        for model_name in preferred_models:

            if model_name in available_model_ids:
                selected_model = model_name
                break

        # NO MODEL AVAILABLE
        if selected_model is None:

            return (
                "Error: No compatible Groq model is currently "
                "available for your API key."
            )
        # GENERATE SQL

        response = client.chat.completions.create(

            model=selected_model,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0
        )

        generated_sql = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )
        generated_sql = generated_sql.replace(
            "```sql",
            ""
        )

        generated_sql = generated_sql.replace(
            "```",
            ""
        )

        return generated_sql.strip()

    except Exception as e:

        return f"Error: {str(e)}"

# MAIN THEME

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL APP
       ======================================================== */

    .stApp {
        background-color: #F5F8F6 !important;
        color: #203C35 !important;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 25px;
        padding-bottom: 60px;
    }


    /* ========================================================
       REMOVE TOP HEADER
       ======================================================== */

    header[data-testid="stHeader"] {
        background-color: transparent !important;
        height: 0rem !important;
    }

    header[data-testid="stHeader"] > div {
        background-color: transparent !important;
    }

    div[data-testid="stDecoration"] {
        display: none !important;
    }


    /* ========================================================
       MAIN TEXT
       ======================================================== */

    h1,
    h2,
    h3,
    h4 {
        color: #24443C !important;
    }

    p {
        color: #4E6860 !important;
    }

    label {
        color: #42635A !important;
        font-weight: 600 !important;
    }


    /* ========================================================
       NAVIGATION
       ======================================================== */

    div[data-testid="stRadio"] {
        margin-top: 5px;
        margin-bottom: 25px;
    }

    div[data-testid="stRadio"] > label {
        display: none !important;
    }

    div[data-testid="stRadio"] > div {
        gap: 8px !important;
    }

    div[data-testid="stRadio"] label {
        background-color: #E6EFEB !important;
        border: 1px solid #C7DCD4 !important;
        border-radius: 11px !important;
        padding: 9px 18px !important;
        color: #35574E !important;
        font-weight: 700 !important;
        cursor: pointer !important;
    }

    div[data-testid="stRadio"] label p {
        color: #35574E !important;
    }

    div[data-testid="stRadio"] label:hover {
        background-color: #D9E8E2 !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) {
        background-color: #24443C !important;
        border-color: #24443C !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) p {
        color: #FFFFFF !important;
    }


    /* ========================================================
       SELECT BOX
       ======================================================== */

    div[data-baseweb="select"] > div {
        background-color: #EEF2F5 !important;
        border: 1px solid #E0E6EA !important;
        border-radius: 11px !important;
        min-height: 54px !important;
    }

    div[data-baseweb="select"] span {
        color: #18352E !important;
    }

    div[data-baseweb="select"] input {
        color: #18352E !important;
    }

    div[data-baseweb="select"] svg {
        fill: #273B38 !important;
    }


    /* ========================================================
       DROPDOWN POPUP
       ======================================================== */

    div[data-baseweb="popover"] {
        background-color: #FFF9F2 !important;
        border: 1px solid #D9C8B8 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="popover"] ul {
        background-color: #FFF9F2 !important;
    }

    div[data-baseweb="popover"] li {
        background-color: #FFF9F2 !important;
        color: #3B403D !important;
    }

    div[data-baseweb="popover"] li:hover {
        background-color: #F1E6D9 !important;
        color: #24443C !important;
    }

    div[role="option"] {
        background-color: #FFF9F2 !important;
        color: #3B403D !important;
    }

    div[role="option"]:hover {
        background-color: #F1E6D9 !important;
        color: #24443C !important;
    }


    /* ========================================================
       TEXT INPUT
       ======================================================== */

    div[data-baseweb="input"] > div {
        background-color: #EEF2F5 !important;
        border: 1px solid #E0E6EA !important;
        border-radius: 11px !important;
        min-height: 54px !important;
    }

    input {
        color: #18352E !important;
    }

    input::placeholder {
        color: #7A8D87 !important;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {
        background-color: #24443C !important;
        color: #FFFFFF !important;
        border: 1px solid #24443C !important;
        border-radius: 11px !important;
        font-weight: 700 !important;
        min-height: 48px !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button p,
    .stButton > button span,
    .stButton > button div {
        color: #FFFFFF !important;
    }

    .stButton > button:hover {
        background-color: #315B50 !important;
        border-color: #315B50 !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
    }

    .stButton > button:hover p,
    .stButton > button:hover span,
    .stButton > button:hover div {
        color: #FFFFFF !important;
    }


    /* ========================================================
       METRIC CARDS
       ======================================================== */

    div[data-testid="stMetric"] {
        background-color: #E8F0EC !important;
        border: 1px solid #C9DDD5 !important;
        padding: 18px !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 12px rgba(36, 68, 60, 0.08);
    }

    div[data-testid="stMetric"] label {
        color: #557269 !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #24443C !important;
        font-weight: 800 !important;
    }


    /* ========================================================
       DATAFRAME
       ======================================================== */

    div[data-testid="stDataFrame"] {
        border: 1px solid #D6E1DD !important;
        border-radius: 13px !important;
        overflow: hidden !important;
        background-color: #FFFFFF !important;
    }


    /* ========================================================
       SQL CODE BLOCK
       ======================================================== */

    div[data-testid="stCodeBlock"] {
        border: 1px solid #D6E1DD !important;
        border-radius: 13px !important;
        overflow: hidden !important;
    }


    /* ========================================================
       WORKFLOW CARDS
       ======================================================== */

    .workflow-card {
        background-color: #E8F0EC;
        border: 1px solid #C9DDD5;
        border-radius: 15px;
        padding: 18px;
        min-height: 145px;
        box-shadow: 0 4px 12px rgba(36, 68, 60, 0.06);
    }

    .workflow-card h3 {
        color: #3A806D !important;
    }

    .workflow-card h4 {
        color: #24443C !important;
    }

    .workflow-card p {
        color: #5A7169 !important;
    }


    /* ========================================================
       TECHNOLOGY CARDS
       ======================================================== */

    .tech-card {
        background-color: #E8F0EC;
        border: 1px solid #C9DDD5;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
    }

    .tech-card h4 {
        color: #24443C !important;
    }

    .tech-card p {
        color: #5A7169 !important;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background-color: #24443C !important;
        border-right: 1px solid #315B50 !important;
    }

    section[data-testid="stSidebar"] > div {
        background-color: #24443C !important;
    }

    /* Sidebar headings */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: #FFFFFF !important;
    }

    /* Sidebar normal text */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] li {
        color: #F1F7F4 !important;
    }

    /* Sidebar markdown text */
    section[data-testid="stSidebar"]
    div[data-testid="stMarkdownContainer"] p {
        color: #F1F7F4 !important;
    }

    /* Sidebar captions */
    section[data-testid="stSidebar"] small {
        color: #D8E9E3 !important;
    }

    /* Sidebar divider */
    section[data-testid="stSidebar"] hr {
        border-color: #4E7067 !important;
    }

    /* Sidebar history buttons */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #315B50 !important;
        border: 1px solid #4E7067 !important;
        color: #FFFFFF !important;
        text-align: left !important;
    }

    section[data-testid="stSidebar"] .stButton > button p,
    section[data-testid="stSidebar"] .stButton > button span,
    section[data-testid="stSidebar"] .stButton > button div {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #3D6A5D !important;
        border-color: #60867A !important;
    }


    /* ========================================================
       DIVIDER
       ======================================================== */

    hr {
        border-color: #D7E1DD !important;
    }


    /* ========================================================
       INFO / SUCCESS / WARNING
       ======================================================== */

    div[data-testid="stAlert"] p {
        color: inherit !important;
    }


    /* ========================================================
       FOOTER
       ======================================================== */

    .footer-text {
        text-align: center;
        color: #6B8179 !important;
        font-size: 14px;
        padding-top: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

def show_login_page():

    st.markdown(
        """
        <style>

        .qg-login-wrapper {
            max-width: 620px;
            margin: 60px auto 0 auto;
            text-align: center;
        }

        .qg-login-icon {
            font-size: 52px;
            margin-bottom: 12px;
        }

        .qg-login-title {
            font-size: 38px;
            font-weight: 800;
            color: #24443C;
            margin-bottom: 8px;
        }

        .qg-login-subtitle {
            font-size: 17px;
            color: #71867F;
            margin-bottom: 40px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    st.write("CURRENT PAGE:", st.session_state.app_page)
    
    # LOGIN HEADER
    
    st.title("🧞 Welcome to QueryGenie")
    st.markdown("AI-powered database assistant")

    email = st.text_input(
        "Email",
        placeholder="Enter your email",
    )

    # PASSWORD

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
    )

    st.write("")

    # CONTINUE and LOGIN buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Continue", use_container_width=True):
            if email.strip() and password.strip():
                st.session_state.user_email = email.strip()
                st.session_state.app_page = "main"
                st.session_state.current_page = "Home"
                st.rerun()
            else:
                st.warning("Please enter your email and password.")
    with col2:
        if st.button("Back to Landing Page", use_container_width=True,type="secondary"):
            st.session_state.app_page = "landing"
            st.rerun()

# LANDING PAGE
def show_landing_page():
    st.html("""
    <style>
        .qg-hero {
            padding: 34px 8px 25px 8px;
        }

        .qg-brand {
            display: flex;
            align-items: center;
            gap: 0;
            font-size: 18px;
            font-weight: 700;
            color: #24443C;
            letter-spacing: 0.3px;
            margin-bottom: 48px;
        }

        .qg-brand-icon {
            font-size: 22px;
            line-height: 1;
            margin-right: 8px;
        }

        .qg-brand-name {
            color: #24443C;
            font-weight: 800;
        }

        .qg-brand-tagline {
            color: #71867F;
            font-weight: 500;
            margin-left: 7px;
        }

        .qg-eyebrow {
            display: inline-block;
            padding: 8px 15px;
            border-radius: 30px;
            background: #E5F0EB;
            border: 1px solid #C9DED6;
            color: #35665A;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.4px;
            margin-bottom: 18px;
        }

        .qg-title {
            font-size: 54px;
            line-height: 1.04;
            font-weight: 800;
            color: #24443C;
            letter-spacing: -2px;
            margin: 0;
        }

        .qg-title-highlight {
            color: #4F776C;
        }

        .qg-description {
            font-size: 18px;
            line-height: 1.7;
            color: #71867F;
            max-width: 620px;
            margin-top: 22px;
            margin-bottom: 28px;
        }

        .qg-tech-line {
            margin-top: 16px;
            color: #81958F;
            font-size: 13px;
            letter-spacing: 0.1px;
        }

        .qg-visual {
            background: #E7F0EC;
            border: 1px solid #CBDDD6;
            border-radius: 28px;
            min-height: 390px;
            padding: 30px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 12px 35px rgba(36, 68, 60, 0.08);
        }

        .qg-visual::before {
            content: "";
            position: absolute;
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: rgba(255,255,255,0.28);
            top: -70px;
            right: -60px;
        }

        .qg-visual-title {
            color: #24443C;
            font-size: 18px;
            font-weight: 750;
            margin-bottom: 20px;
            position: relative;
        }

        .qg-ai-circle {
            width: 82px;
            height: 82px;
            border-radius: 50%;
            background: #24443C;
            margin: 18px auto 22px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 38px;
            box-shadow: 0 10px 25px rgba(36, 68, 60, 0.20);
            position: relative;
        }

        .qg-visual-flow {
            text-align: center;
            color: #55746B;
            font-size: 14px;
            line-height: 1.4;
            position: relative;
        }

        .qg-flow-item {
            background: #F5F8F6;
            border: 1px solid #D6E4DF;
            border-radius: 12px;
            padding: 10px 12px;
            margin: 7px 0;
            color: #355C52;
            font-weight: 600;
        }

        .qg-flow-arrow {
            color: #6B897F;
            font-size: 17px;
            line-height: 1;
        }

        .qg-section-title {
            font-size: 28px;
            font-weight: 800;
            color: #24443C;
            margin-top: 58px;
            margin-bottom: 8px;
        }

        .qg-section-subtitle {
            color: #81958F;
            font-size: 16px;
            margin-bottom: 25px;
        }

        .qg-card {
            background: #EAF2EE;
            border: 1px solid #D0E0DA;
            border-radius: 18px;
            padding: 24px;
            min-height: 185px;
            box-shadow: 0 6px 20px rgba(36, 68, 60, 0.05);
        }

        .qg-card-icon {
            font-size: 27px;
            margin-bottom: 14px;
        }

        .qg-card-title {
            color: #24443C;
            font-size: 19px;
            font-weight: 750;
            margin-bottom: 9px;
        }

        .qg-card-text {
            color: #71867F;
            font-size: 14px;
            line-height: 1.6;
        }

        .qg-workflow {
            background: #F0F5F2;
            border: 1px solid #D4E2DC;
            border-radius: 20px;
            padding: 20px 24px;
            margin-top: 42px;
            margin-bottom: 18px;
        }

        .qg-workflow-label {
            color: #24443C;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .qg-step {
            text-align: center;
            color: #42675D;
            font-size: 14px;
            font-weight: 650;
            padding: 7px 4px;
        }

        .qg-step-number {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            background: #D8E8E1;
            color: #24443C;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 8px auto;
            font-weight: 800;
        }

        .qg-bottom {
            text-align: center;
            padding: 52px 20px 18px 20px;
        }

        .qg-bottom-title {
            color: #24443C;
            font-size: 28px;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .qg-bottom-text {
            color: #81958F;
            font-size: 15px;
        }

        @media (max-width: 900px) {
            .qg-title {
                font-size: 42px;
            }

            .qg-visual {
                margin-top: 25px;
            }
        }
    </style>
    """)

    # BRAND
    
    st.html("""
    <div class="qg-hero">
        <div class="qg-brand">
            <span class="qg-brand-icon">🧞</span>
            <span class="qg-brand-name">QueryGenie</span>
            <span class="qg-brand-tagline">· AI Database Assistant</span>
        </div>
    </div>
    """)

    # HERO SECTION

    hero_left, hero_right = st.columns([1.15, 0.85], gap="large")

    with hero_left:
        st.html("""
        <div class="qg-eyebrow">✦ NATURAL LANGUAGE → SQL</div>

        <div class="qg-title">
            Talk to your<br>
            <span class="qg-title-highlight">database.</span>
        </div>

        <div class="qg-description">
            QueryGenie lets you ask questions about your database in plain English.
            AI understands your question, generates SQL, executes it safely,
            and helps you understand the results.
        </div>
        """)

        if st.button(
            "🚀  Start with QueryGenie",
            key="landing_start",
            use_container_width=True
        ):
            st.session_state.app_page = "login"
            st.rerun()

        st.html("""
        <div class="qg-tech-line">
            Python &nbsp;•&nbsp; Streamlit &nbsp;•&nbsp; SQLite &nbsp;•&nbsp; Groq AI &nbsp;•&nbsp; Plotly
        </div>
        """)

    with hero_right:
        st.html("""
        <div class="qg-visual">
            <div class="qg-visual-title">🧠 QueryGenie AI</div>

            <div class="qg-ai-circle">🧞</div>

            <div class="qg-visual-flow">
                <div class="qg-flow-item">💬 Natural Language Question</div>
                <div class="qg-flow-arrow">↓</div>
                <div class="qg-flow-item">🧠 AI Understanding</div>
                <div class="qg-flow-arrow">↓</div>
                <div class="qg-flow-item">⚡ SQL Generation</div>
                <div class="qg-flow-arrow">↓</div>
                <div class="qg-flow-item">📊 Results &amp; Visualization</div>
            </div>
        </div>
        """)

    # FEATURE SECTION
    st.html("""
    <div class="qg-section-title">Everything you need to work with data</div>
    <div class="qg-section-subtitle">
        Powerful database interaction without manually writing SQL.
    </div>
    """)

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.html("""
        <div class="qg-card">
            <div class="qg-card-icon">✨</div>
            <div class="qg-card-title">AI SQL Generation</div>
            <div class="qg-card-text">
                Ask questions naturally and let QueryGenie generate SQL queries using AI.
            </div>
        </div>
        """)

    with col2:
        st.html("""
        <div class="qg-card">
            <div class="qg-card-icon">🗄️</div>
            <div class="qg-card-title">Database Explorer</div>
            <div class="qg-card-text">
                Browse tables, inspect records and understand your database structure easily.
            </div>
        </div>
        """)

    with col3:
        st.html("""
        <div class="qg-card">
            <div class="qg-card-icon">📊</div>
            <div class="qg-card-title">Data Visualization</div>
            <div class="qg-card-text">
                Transform query results into clear, interactive visualizations for analysis.
            </div>
        </div>
        """)

    # WORKFLOW
    st.html("""
    <div class="qg-workflow">
        <div class="qg-workflow-label">How QueryGenie works</div>
    </div>
    """)

    step1, step2, step3, step4 = st.columns(4)

    with step1:
        st.html("""
        <div class="qg-step">
            <div class="qg-step-number">01</div>
            💬 Ask
        </div>
        """)

    with step2:
        st.html("""
        <div class="qg-step">
            <div class="qg-step-number">02</div>
            🧠 Understand
        </div>
        """)

    with step3:
        st.html("""
        <div class="qg-step">
            <div class="qg-step-number">03</div>
            ⚡ Generate
        </div>
        """)

    with step4:
        st.html("""
        <div class="qg-step">
            <div class="qg-step-number">04</div>
            📈 Analyze
        </div>
        """)
# APPLICATION PAGE CONTROLLER

if st.session_state.app_page == "landing":

    show_landing_page()

    st.stop()


elif st.session_state.app_page == "login":

    show_login_page()

    st.stop()

# NAVIGATION
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

col1, col2, col3 = st.columns([1,1,1])

with col1:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.current_page = "Overview"

with col2:
    if st.button("🤖 SQL Generator", use_container_width=True):
        st.session_state.current_page = "SQL Generator"

with col3:
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.current_page = "Dashboard"

current_page = st.session_state.current_page

# HOME PAGE
if current_page == "Home":

    st.title("✦ QueryGenie Overview")

    st.markdown(
        """
        ### Making database querying simple and accessible

        QueryGenie helps users interact with databases using
        natural language instead of writing SQL manually.
        """
    )
    st.divider()

    # ADVANTAGES

    st.header("✨ Advantages of QueryGenie")

    st.markdown("### 💡 Easy to Use")
    st.write(
        "Ask questions in simple natural language instead "
        "of writing SQL manually."
    )

    st.markdown("### ⚡ Saves Time")
    st.write(
        "Generate SQL queries quickly with AI-powered "
        "query generation."
    )

    st.markdown("### 🎤 Voice Interaction")
    st.write(
        "Ask database questions using your voice "
        "instead of typing."
    )

    st.markdown("### 📊 Interactive Results")
    st.write(
        "View query results and understand your data "
        "through interactive visualizations."
    )

    st.markdown("### 🎓 Beginner Friendly")
    st.write(
        "Makes database querying easier for users "
        "who are new to SQL."
    )

    st.markdown("### 🔄 Flexible")
    st.write(
        "Work with your database and ask different "
        "types of questions."
    )

    st.divider()

    # WHO CAN USE QUERYGENIE

    st.header("👥 Who Can Use QueryGenie?")

    st.markdown("### 🎓 Students")
    st.write(
        "Learn SQL concepts and practice database "
        "queries using natural language."
    )

    st.markdown("### 📊 Data Analysts")
    st.write(
        "Retrieve information and explore database "
        "results more efficiently."
    )

    st.markdown("### 👨‍💻 Developers")
    st.write(
        "Speed up SQL query creation during "
        "application development."
    )

    st.markdown("### 🏢 Business Users")
    st.write(
        "Access database information without needing "
        "advanced SQL knowledge."
    )

    st.divider()

    # GETTING STARTED
    st.header("🚀 Getting Started")

    st.markdown("### 01 — 💬 Ask")
    st.write(
        "Enter or speak your database question "
        "in natural language."
    )

    st.markdown("### 02 — 🤖 Generate")
    st.write(
        "QueryGenie converts your question into "
        "a SQL query using AI."
    )

    st.markdown("### 03 — 📈 Explore")
    st.write(
        "View the results and explore your data "
        "using visualizations."
    )
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("Back to Login", use_container_width=True,type="secondary"):
            st.session_state.app_page = "login"
            st.rerun()
    
# SQL GENERATOR
elif current_page == "SQL Generator":

    st.title(
        "🤖 AI SQL Generator"
    )

    st.markdown(
        """
        ### Ask your database questions naturally.

        Select or upload a database, browse its tables,
        type or speak your question, and QueryGenie will
        generate the SQL for you.
        """
    )
    # sidebar
    with st.sidebar:
        st.markdown("## 🤖 QueryGenie")
        st.caption("AI SQL Generator")
        st.divider()
        st.markdown("### 🍃 Quick Start")
        st.markdown("**1.** Select or upload a database")
        st.markdown("**2.** Ask your question")
        st.markdown("**3.** Generate SQL")
        st.markdown("**4.** Explore the result")
        st.divider()

        st.markdown("### ✨ Module Features")
        st.markdown("✓ Natural Language to SQL")
        st.markdown("✓ SQLite Database Support")
        st.markdown("✓ Voice Assistant")
        st.markdown("✓ Query Results")
        st.markdown("✓ Data Visualization")
        st.divider()

        st.markdown("### 🕘 Query History")

        if not st.session_state.history:

            st.caption(
                "Your recent queries will appear here."
            )

        else:

            for item in reversed(
                st.session_state.history
            ):

                question_text = item["question"]

                if len(question_text) > 35:

                    question_text = (
                        question_text[:35] + "..."
                    )

                st.markdown(
                    f"💬 {question_text}"
                )

    # DATABASE SELECTION

    st.subheader("🗄️ Select Database")

    uploaded_database = st.file_uploader(
        "Upload a SQLite database",
        type=["db", "sqlite", "sqlite3"],
        key="sql_database_uploader"
    )

    if uploaded_database is not None:

        database_folder = "uploaded_databases"

        os.makedirs(
            database_folder,
            exist_ok=True
        )

        database_path = os.path.join(
            database_folder,
            uploaded_database.name
        )

        with open(
            database_path,
            "wb"
        ) as file:

            file.write(
                uploaded_database.getbuffer()
            )

        st.session_state["active_database_path"] = (
            database_path
        )
        st.session_state["database_uploaded"] = True
        st.success("✅ Database uploaded successfully")

    # active database
    active_database_path = st.session_state.get(
        "active_database_path"
    )
    if not active_database_path:
        st.warning("Please upload/select a database first.")
        st.stop()

    database_name = os.path.basename(
        active_database_path
    )
    st.markdown(
        f"""
        <div class="dashboard-db">
            🗄️ <b>Active Database:</b> {database_name}
        </div>
        """,
        unsafe_allow_html=True
    )

    # database connection
    connection = sqlite3.connect(active_database_path)

    # GET TABLES

    tables_query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """

    tables_df = pd.read_sql_query(
        tables_query,
        connection
    )

    tables = tables_df[
        "name"
    ].tolist()

    if not tables:

        st.error("❌ No tables found in this database.")
    else:
        selected_table = st.selectbox(
            "📂 Select a table",
            tables,
            key="sql_table"
        )
        st.divider()

        # QUESTION

        question = st.text_input(
            "💬 Ask your question",
            placeholder="Example: Show all products",
            key="question_input"
        )

        # BUTTONS

        col1, col2 = st.columns(2)

        with col1:

            speak_button = st.button(
                "🎤 Speak Question",
                key="voice_input",
                use_container_width=True
            )

        with col2:

            generate_button = st.button(
                "✨ Generate SQL",
                key="generate_sql",
                use_container_width=True
            )

        # VOICE INPUT

        if speak_button:

            recognizer = sr.Recognizer()

            try:

                with sr.Microphone() as source:

                    st.write(
                        "🎤 Listening... Please speak now."
                    )

                    recognizer.adjust_for_ambient_noise(
                        source,
                        duration=1
                    )

                    audio = recognizer.listen(
                        source,
                        timeout=10,
                        phrase_time_limit=10
                    )

                st.write(
                    "🔄 Converting speech to text..."
                )

                voice_question = (
                    recognizer.recognize_google(
                        audio,
                        language="en-US"
                    )
                )

                st.session_state.voice_question = (
                    voice_question
                )

                st.success(
                    "🗣️ You said: "
                    + voice_question
                )

            except sr.WaitTimeoutError:

                st.warning(
                    "⏱️ No speech detected. "
                    "Please try again."
                )

            except sr.UnknownValueError:

                st.warning(
                    "⚠️ Sorry, I could not "
                    "understand your speech."
                )

            except sr.RequestError as e:

                st.error(
                    "❌ Speech recognition "
                    "service error: "
                    + str(e)
                )

            except Exception as e:

                st.error(
                    "❌ Microphone error: "
                    + str(e)
                )
        # SHOW VOICE QUESTION

        if st.session_state.voice_question:

            st.write(
                "🎤 Voice question: "
                + st.session_state.voice_question
            )

        # GENERATE SQL

        if generate_button:

            if st.session_state.voice_question:

                active_question = (
                    st.session_state.voice_question
                )

            else:

                active_question = question

            active_question = (
                active_question.strip()
            )

            st.session_state.user_question = (
                active_question
            )
            # SIMPLE COMMANDS

            simple_commands = {

                "products":
                    "show all products",

                "product":
                    "show all products",

                "show products":
                    "show all products",

                "all products":
                    "show all products",

                "show all products":
                    "show all products"
            }

            command = (
                active_question.lower()
            )

            if command in simple_commands:

                active_question = (
                    simple_commands[command]
                )
            # EMPTY QUESTION

            if active_question == "":

                st.warning(
                    "⚠️ Please enter or speak "
                    "a question."
                )

            else:

                try:

                    # GENERATE SQL
                    generated_sql = generate_sql(
                        active_question,
                        connection
                    )

                    # safety check
                    cleaned_sql = (
                        generated_sql
                        .strip()
                        .lower()
                    )
                    if not cleaned_sql.startswith(
                        "select"
                    ):
                        st.error("⚠️ Only SELECT queries"
                                 "are allowed"
                        )
                    else:
                        # SAVE STATE
                        st.session_state.generated_sql = (
                            generated_sql
                        )

                        st.session_state.last_question = (
                            active_question
                        )
                        # ADD HISTORY
                        history_item = {
                            "question": active_question,
                            "table": selected_table,
                            "sql": generated_sql
                        }
                        # Avoid duplicate questions
                        st.session_state.history = [
                            item for item in st.session_state.history
                            if item["question"] != active_question
                        ]
                        # Add newest question at the end
                        st.session_state.history.append(history_item)

                        # Keep only latest 10
                        if len(st.session_state.history) > 10:
                            st.session_state.history = st.session_state.history[-10:]

                        # Make this question the currently selected history item
                        st.session_state.selected_history_question = active_question

                        # EXECUTE SQL
                        result = pd.read_sql_query(
                            generated_sql,
                            connection
                        )

                        st.session_state.query_result = (
                            result
                        )
                        # GENERATED SQL
                        st.subheader(
                            "🔎 Generated SQL"
                        )

                        st.code(
                            generated_sql,
                            language="sql"
                        )
                        # RESULT
                        st.subheader(
                            "📊 Query Result"
                        )

                        st.dataframe(
                            result,
                            use_container_width=True,
                            hide_index=True
                        )
                        # VISUALIZATION
                        if not result.empty:

                            numeric_columns = (
                                result
                                .select_dtypes(
                                    include=["number"]
                                )
                                .columns
                                .tolist()
                            )

                            categorical_columns = (
                                result
                                .select_dtypes(
                                    include=[
                                        "object",
                                        "category"
                                    ]
                                )
                                .columns
                                .tolist()
                            )

                            if (
                                numeric_columns
                                and categorical_columns
                            ):

                                st.subheader(
                                    "📈 Data Visualization"
                                )

                                col1, col2 = st.columns(2)

                                with col1:

                                    x_column = st.selectbox(
                                        "X-Axis",
                                        categorical_columns,
                                        key="sql_visualization_x"
                                    )

                                with col2:

                                    y_column = st.selectbox(
                                        "Y-Axis",
                                        numeric_columns,
                                        key="sql_visualization_y"
                                    )

                                chart = px.bar(
                                    result,
                                    x=x_column,
                                    y=y_column,
                                    title=f"{y_column} by {x_column}",
                                    color_discrete_sequence=[
                                        "#3A806D"
                                    ]
                                )

                                chart.update_layout(
                                    paper_bgcolor="#F5F8F6",
                                    plot_bgcolor="#F5F8F6",
                                    font=dict(
                                        color="#24443C"
                                    ),
                                    title_font=dict(
                                        color="#24443C",
                                        size=20
                                    ),
                                    margin=dict(
                                        l=20,
                                        r=20,
                                        t=60,
                                        b=20
                                    )
                                )

                                st.plotly_chart(
                                    chart,
                                    use_container_width=True
                                )

                            else:

                                st.write(
                                    "ℹ️ This result does not contain "
                                    "suitable columns for visualization."
                                )
                        # CLEAR VOICE
                        st.session_state.voice_question = ""

                except Exception as e:

                    st.error(
                        f"❌ Error: {e}"
                    )
        # back to login
        back_col1, back_col2, back_col3 = st.columns([1, 2, 1])
        with back_col2:
            if st.button("← Back to Login", use_container_width=True,type="secondary"):
                st.session_state.app_page = "login"
                st.rerun()

        # CLOSE DATABASE
        connection.close()

# DASHBOARD

elif current_page == "Dashboard":

    active_database_path = st.session_state.get(
        "active_database_path",
        DATABASE_PATH
    )

    st.title("📊 QueryGenie Dashboard")

    st.markdown(
        """
        ### Your database at a glance.

        View database statistics and QueryGenie activity
        from one place.
        """
    )

    st.divider()

    # database connection

    try:

        dashboard_connection = sqlite3.connect(
            active_database_path
        )

        # Get all tables from the default database
        tables_query = """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """

        tables_df = pd.read_sql_query(
            tables_query,
            dashboard_connection
        )

        tables = tables_df["name"].tolist()

    except Exception:

        tables = []

        dashboard_connection = None
        st.error(f"❌ Could not open database: {e}")

    # CALCULATE DATABASE STATISTICS
    total_tables = len(tables)

    total_records = 0
    total_columns = 0

    table_statistics = []

    if dashboard_connection is not None:

        for table in tables:

            try:
                # Number of records
                count_query = (
                    f'SELECT COUNT(*) AS count '
                    f'FROM "{table}"'
                )

                count_df = pd.read_sql_query(
                    count_query,
                    dashboard_connection
                )

                row_count = int(
                    count_df.iloc[0]["count"]
                )
                # Number of columns
                columns_query = (
                    f'PRAGMA table_info("{table}")'
                )

                columns_df = pd.read_sql_query(
                    columns_query,
                    dashboard_connection
                )

                column_count = len(
                    columns_df
                )

                total_records += row_count
                total_columns += column_count

                table_statistics.append(
                    {
                        "Table": table,
                        "Records": row_count,
                        "Columns": column_count
                    }
                )

            except Exception:
                pass

        dashboard_connection.close()

    # TOP METRICS
    col1, col2, col3, col4 = st.columns(4)

    # TOTAL TABLES
    with col1:

        st.metric(
            "🗄️ Tables",
            total_tables
        )
    # TOTAL RECORDS
    with col2:

        st.metric(
            "📊 Total Records",
            f"{total_records:,}"
        )

    # TOTAL COLUMNS

    with col3:

        st.metric(
            "📋 Total Columns",
            total_columns
        )
    # TOTAL QUERIES ASKED

        query_history = st.session_state.get(
            "history",
            []
        )

        st.metric(
            "🤖 Queries Asked",
            len(query_history)
        )

    st.divider()
    # TABLE OVERVIEW

    st.subheader(
        "📋 Table Overview"
    )

    if table_statistics:

        statistics_df = pd.DataFrame(
            table_statistics
        )

        st.dataframe(
            statistics_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.write(
            "No tables found in the default database."
        )

    if table_statistics:

        st.subheader(
            "📈 Records by Table"
        )

        chart_df = pd.DataFrame(
            table_statistics
        )

        chart = px.bar(
            chart_df,
            x="Table",
            y="Records",
            title="Number of Records in Each Table",
            color_discrete_sequence=["#3A806D"]
        )

        chart.update_layout(
            paper_bgcolor="#F5F8F6",
            plot_bgcolor="#F5F8F6",
            font=dict(
                color="#24443C"
            ),
            title_font=dict(
                color="#24443C",
                size=20
            ),
            xaxis_title="Table",
            yaxis_title="Records",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )
        )

        st.plotly_chart(
            chart,
            use_container_width=True
        )
    # back button
    back_col1, back_col2, back_col3 = st.columns([1, 2, 1])
    with back_col2:
        if st.button("← Back to Login", use_container_width=True,type="secondary"):
            st.session_state.app_page = "login"
            st.rerun()

    # FOOTER
    st.divider()

    st.markdown(
        """
        <div class="footer-text">
            🧞 QueryGenie • AI-Powered Database Assistant
            • Python + Streamlit + SQLite + Groq AI
        </div>
        """,
        unsafe_allow_html=True
    )