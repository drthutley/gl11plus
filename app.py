import streamlit as st
import random
import json
from google import genai
from pydantic import BaseModel, Field

# ==========================================
# 1. PAGE CONFIG & DYSLEXIA-FRIENDLY CSS
# ==========================================
st.set_page_config(page_title="GL 11+ Practice Partner", page_icon="✏️", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #fdfbf7 !important; color: #2b2b2b !important; }
    p, label, li, .stMarkdown, .stText { font-family: 'Verdana', sans-serif !important; font-size: 19px !important; line-height: 1.8 !important; }
    .stButton>button { background-color: #e0f2fe !important; color: #0369a1 !important; border: 2px solid #0369a1 !important; border-radius: 10px !important; font-weight: bold !important; }
    .correct-box { background-color: #dcfce7; padding: 15px; border-radius: 8px; border: 2px solid #22c55e; margin-bottom: 10px; }
    .incorrect-box { background-color: #fee2e2; padding: 15px; border-radius: 8px; border: 2px solid #ef4444; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# [... Keep the same TOPICS dictionary as before ...]
# [... Keep the same QuestionData/QuizData classes as before ...]

# ==========================================
# 2. STATE MANAGEMENT
# ==========================================
if "quiz_active" not in st.session_state: st.session_state.quiz_active = False
if "review_mode" not in st.session_state: st.session_state.review_mode = False
if "user_answers" not in st.session_state: st.session_state.user_answers = {} # Stores {index: choice}
if "quiz_questions" not in st.session_state: st.session_state.quiz_questions = []

# ==========================================
# 3. QUIZ INTERFACE
# ==========================================
st.title("GL 11+ Practice Partner")

# [... Keep your "Quiz Setup" expander logic here ...]

if st.session_state.quiz_active and not st.session_state.review_mode:
    total_q = len(st.session_state.quiz_questions)
    idx = st.session_state.current_index
    q = st.session_state.quiz_questions[idx]
    
    st.progress((idx + 1) / total_q)
    st.info(f"**Question {idx + 1}**: {q['question']}")
    
    options = [f"A) {q['option_a']}", f"B) {q['option_b']}", f"C) {q['option_c']}", f"D) {q['option_d']}", f"E) {q['option_e']}"]
    
    # Pre-select answer if he navigates back
    choice = st.radio("Select answer:", options, index=None, key=f"r_{idx}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous") and idx > 0:
            st.session_state.current_index -= 1
            st.rerun()
    with col2:
        if idx < total_q - 1:
            if st.button("Next"):
                st.session_state.user_answers[idx] = choice
                st.session_state.current_index += 1
                st.rerun()
        else:
            if st.button("Finish & See Results"):
                st.session_state.user_answers[idx] = choice
                st.session_state.quiz_active = False
                st.session_state.review_mode = True
                st.rerun()

# ==========================================
# 4. REVIEW DASHBOARD
# ==========================================
if st.session_state.review_mode:
    st.header("Results Dashboard")
    score = 0
    for i, q in enumerate(st.session_state.quiz_questions):
        user_ans = st.session_state.user_answers.get(i)
        is_correct = user_ans and user_ans[0] == q['correct_letter']
        if is_correct: score += 1
        
        box_class = "correct-box" if is_correct else "incorrect-box"
        with st.expander(f"Question {i+1}: {'✅ Correct' if is_correct else '❌ Review Needed'}"):
            st.markdown(f"<div class='{box_class}'>", unsafe_allow_html=True)
            st.write(q['question'])
            st.write(f"Your answer: {user_ans}")
            st.write(f"Correct answer: {q['correct_letter']}")
            st.markdown("</div>", unsafe_allow_html=True)
            if not is_correct:
                st.warning(f"**Hint:** {q['hint']}")
                st.success(f"**Technique:** {q['exam_technique']}")
    
    st.metric("Final Score", f"{score} / {len(st.session_state.quiz_questions)}")
    if st.button("Start New Quiz"):
        st.session_state.review_mode = False
        st.rerun()
