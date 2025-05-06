# ballet_app.py
# ────────────────────────────────────────────────────────────────
# Folder structure pushed to GitHub:
#   ballet_app.py
#   grade 1 Ballet Theory.xlsx   ← workbook with sheets "Grade 1" & "Grade 2"
#   Dance HQ Logo.jpg
#   requirements.txt             ← streamlit, pandas, openpyxl
#
# When deployed on Streamlit Cloud the code will read files
# from the repo root thanks to the *relative* paths below.
# ────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
from pathlib import Path
import random

# ── CONFIG ──────────────────────────────────────────────────────
DATA_BOOK = Path("grade 1 Ballet Theory.xlsx")   # ← relative, not C:\...
LOGO_PATH = Path(__file__).with_name("Dance HQ Logo.jpg")
APP_TITLE = "Ballet Theory"
LOGO_WIDTH = 520            # tweak to resize logo
# ────────────────────────────────────────────────────────────────


# ── HELPERS ─────────────────────────────────────────────────────
@st.cache_data
def load_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    """Load a specific worksheet and normalise headers."""
    try:
        df = pd.read_excel(path, sheet_name=sheet_name).dropna(subset=["Question"])
    except ValueError:
        st.stop(f"❌ Sheet “{sheet_name}” not found in '{path.name}'. "
                "Open the workbook and add the tab.")
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace("-", "_", regex=False)
    )
    return df


def show_logo():
    """Large, centred Dance HQ logo (streamlit < 1.32 uses width param)."""
    col_l, col_c, col_r = st.columns([1, 3, 1])
    with col_c:
        st.image(LOGO_PATH, width=LOGO_WIDTH)


def reset_quiz_state():
    """Remove all keys related to quizzes."""
    for k in list(st.session_state.keys()):
        if k.startswith(("quiz_", "opts_", "radio_", "submit_")):
            del st.session_state[k]


# ── GENERIC QUIZ ENGINE (for any sheet) ─────────────────────────
def run_quiz(sheet_name: str):
    df = load_sheet(DATA_BOOK, sheet_name)

    idx_key  = f"quiz_idx_{sheet_name}"
    resp_key = f"quiz_resp_{sheet_name}"

    if idx_key not in st.session_state:
        st.session_state[idx_key]  = 0
        st.session_state[resp_key] = []

    q_idx  = st.session_state[idx_key]
    result = st.session_state[resp_key]

    # ── ask a question ──────────────────────────────────────────
    def ask_question(q_row):
        show_logo()

        col_home, _, col_q = st.columns([1, 0.1, 7])
        with col_home:
            if st.button("🏠 Home", key=f"home_{sheet_name}_{q_idx}"):
                reset_quiz_state()
                st.session_state.page = "landing"
                st.rerun()

        with col_q:
            letters = {
                "a": q_row.option_a,
                "b": q_row.option_b,
                "c": q_row.option_c,
                "d": q_row.option_d,
            }
            correct = letters[str(q_row.answer).strip().lower()]

            opt_key = f"opts_{sheet_name}_{q_idx}"
            if opt_key not in st.session_state:
                st.session_state[opt_key] = random.sample(list(letters.values()), k=4)
            options = st.session_state[opt_key]

            st.subheader(q_row.question)
            choice = st.radio("Choose one:", options, key=f"radio_{sheet_name}_{q_idx}")

            if st.button("Submit", key=f"submit_{sheet_name}_{q_idx}"):
                right = choice.strip().lower() == correct.strip().lower()
                result.append((q_row.question, choice, correct, right))

                if right:
                    st.balloons()
                    st.success("Correct!")
                    if pd.notna(q_row.get("image_url", "")):
                        st.image(q_row.image_url)
                else:
                    st.error("Incorrect.")
                    st.info(f"**Correct answer:** {correct}")

                st.session_state[idx_key] += 1
                st.rerun()

    # ── results screen ─────────────────────────────────────────
    def show_results():
        show_logo()
        total = len(df)
        right = sum(r[3] for r in result)
        st.header(f"{sheet_name} – Results")
        st.metric("Score", f"{right} / {total}")

        wrongs = [r for r in result if not r[3]]
        if wrongs:
            with st.expander("Review questions to practise"):
                for q, your, corr, _ in wrongs:
                    st.write(f"**Q:** {q}")
                    st.write(f"✘ Your answer: {your}")
                    st.write(f"✔ Correct: {corr}\n")

        col_home, _, col_play = st.columns([1, 0.5, 1])
        with col_home:
            if st.button("🏠 Home", key=f"home_results_{sheet_name}"):
                reset_quiz_state()
                st.session_state.page = "landing"
                st.rerun()
        with col_play:
            if st.button("Play again 🔄", key=f"play_{sheet_name}"):
                reset_quiz_state()
                run_quiz(sheet_name)
                st.rerun()

    # ── decide which part to show ───────────────────────────────
    if q_idx < len(df):
        ask_question(df.iloc[q_idx])
    else:
        show_results()


# ── LANDING & PLACEHOLDER PAGES ─────────────────────────────────
def landing_page():
    show_logo()
    st.title(APP_TITLE)
    st.markdown("### Select a section to begin:")

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        choice = st.radio(
            "",
            ("Grade 1", "Grade 2", "Additional Information – Flash Cards"),
            index=0,
        )
        if st.button("Submit"):
            st.session_state.page = (
                "grade1" if choice == "Grade 1"
                else "grade2" if choice == "Grade 2"
                else "flash"
            )
            st.rerun()


def placeholder_page(title):
    show_logo()
    col_home, _, col_body = st.columns([1, 0.2, 6])
    with col_home:
        if st.button("🏠 Home"):
            st.session_state.page = "landing"
            st.rerun()
    with col_body:
        st.header(title)
        st.info("🚧 Content coming soon!")


# ── MAIN ROUTER ─────────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon="🩰", layout="centered")

if "page" not in st.session_state:
    st.session_state.page = "landing"

match st.session_state.page:
    case "landing":
        landing_page()
    case "grade1":
        run_quiz("Grade 1")
    case "grade2":
        run_quiz("Grade 2")
    case "flash":
        placeholder_page("Additional Information – Flash Cards")
    case _:
        st.session_state.page = "landing"
        landing_page()
