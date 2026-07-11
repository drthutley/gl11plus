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
    p, span, label, li, div, input {
        font-family: 'Verdana', 'Comic Sans MS', sans-serif !important;
        font-size: 19px !important;
        line-height: 1.8 !important;
        letter-spacing: 0.06em !important;
    }
    h1, h2, h3, h4 { font-family: 'Verdana', sans-serif !important; color: #1a365d !important; font-weight: bold !important; margin-bottom: 20px !important; }
    .stTextInput>div>div>input { background-color: #ffffff !important; border: 2px solid #cbd5e1 !important; border-radius: 8px !important; padding: 12px !important; }
    .stButton>button { background-color: #e0f2fe !important; color: #0369a1 !important; border: 2px solid #0369a1 !important; border-radius: 10px !important; font-size: 18px !important; font-weight: bold !important; padding: 10px 24px !important; transition: all 0.2s ease; }
    .stButton>button:hover { background-color: #bae6fd !important; border-color: #0284c7 !important; }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div { background-color: #0369a1 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FULL SYLLABUS MENU (Flattened for easier selection)
# ==========================================
TOPICS = {
    "English": [
        "Grammar: Parts of Speech", "Grammar: Verbs", "Grammar: Mixed Questions",
        "Punctuation: Starting/Ending Sentences", "Punctuation: Commas and Brackets", 
        "Punctuation: Dashes/Apostrophes", "Punctuation: Inverted Commas/Colons", "Punctuation: Mixed",
        "Spelling: Plurals", "Spelling: Homophones", "Spelling: Prefixes/Suffixes", 
        "Spelling: Awkward Spellings", "Spelling: Mixed",
        "Writers' Techniques: Alliteration/Onomatopoeia", "Writers' Techniques: Imagery", 
        "Writers' Techniques: Abbreviations", "Writers' Techniques: Synonyms/Antonyms", 
        "Writers' Techniques: Spotting Devices",
        "Writing: Fiction", "Writing: Non-Fiction"
    ],
    "Verbal Reasoning": [
        "The Alphabet: Positions", "The Alphabet: Identify from Clue", "The Alphabet: Order",
        "Making Words: Missing Letters", "Making Words: Move a Letter", "Making Words: Hidden Word", 
        "Making Words: Find Missing Word", "Making Words: Rule to Make a Word", "Making Words: Compound Words", 
        "Making Words: Forming New Words", "Making Words: Complete Word Pair", "Making Words: Anagram in Sentence", 
        "Making Words: Word Ladders",
        "Word Meanings: Closest Meaning", "Word Meanings: Opposite Meaning", "Word Meanings: Multiple Meanings", 
        "Word Meanings: Odd Ones Out", "Word Meanings: Word Connections", "Word Meanings: Reorder Words",
        "Maths & Sequences: Complete the Sum", "Maths & Sequences: Letter Sequences", 
        "Maths & Sequences: Number Sequences", "Maths & Sequences: Related Numbers", "Maths & Sequences: Letter-Coded Sums",
        "Logic & Coding: Letter Connections", "Logic & Coding: Letter-Word Codes", "Logic & Coding: Number-Word Codes", 
        "Logic & Coding: Explore Facts", "Logic & Coding: Solve Riddle", "Logic & Coding: Word Grids"
    ]
}

# ==========================================
# 3. AI STRUCTURE & STATE MANAGEMENT
# ==========================================
# Note: Added 'exam_technique' to the required AI output
class QuestionData(BaseModel):
    question: str = Field(description="The GL 11+ style question text. Include multiple choice options in text if applicable.")
    answer: str = Field(description="The exact target answer word or number.")
    hint: str = Field(description="A clear, dyslexia-friendly hint to solve the problem.")
    exam_technique: str = Field(description="A specific exam technique or time-saving trick for this specific type of question.")

class QuizData(BaseModel):
    questions: list[QuestionData]

# Initialize all the variables needed to run a batch quiz
if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "user_score" not in st.session_state:
    st.session_state.user_score = 0
if "answered_current" not in st.session_state:
    st.session_state.answered_current = False

def generate_quiz(subject, selected_topics, num_questions, api_key):
    if not api_key:
        st.error("⚠️ Please ensure your API key is in Streamlit Secrets.")
        return False
    if not selected_topics:
        st.error("⚠️ Please select at least one topic.")
        return False

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert tutor for the UK GL 11+ exams. Generate exactly {num_questions} unique practice questions.
    Distribute the questions evenly across these topics for the subject '{subject}': {', '.join(selected_topics)}
    
    Requirements:
    1. Strictly align with the GL 11+ standard.
    2. Format options clearly within the question text if it is multiple choice.
    3. The answer must be a single word, short phrase, or number.
    4. The hint MUST be dyslexia-friendly (clear, simple phrasing).
    5. Provide an exam technique/strategy for approaching this specific type of question rapidly.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': QuizData,
                'temperature': 0.7, 
            }
        )
        data = json.loads(response.text)
        st.session_state.quiz_questions = data["questions"]
        st.session_state.current_index = 0
        st.session_state.user_score = 0
        st.session_state.quiz_active = True
        st.session_state.answered_current = False
        return True
    except Exception as e:
        st.error(f"Failed to generate questions. Error: {e}")
        return False

# ==========================================
# 4. APP INTERFACE & SETUP MENU
# ==========================================
st.title("✏️ GL 11+ Practice Partner")

try:
    secret_api_key = st.secrets["GEMINI_API_KEY"]
except:
    secret_api_key = ""
    st.error("⚠️ API Key not found in Streamlit secrets.")

# Setup menu folds up automatically when a quiz is running
with st.expander("⚙️ Quiz Setup (Click to open/close)", expanded=(not st.session_state.quiz_active)):
    
    selected_subject = st.selectbox("📚 Choose Subject", ["English", "Verbal Reasoning"])
    
    st.markdown("### 🎯 Choose Topics")
    all_topics = TOPICS[selected_subject]
    
    # Checkbox to easily select everything
    select_all = st.checkbox("☑️ Select ALL topics in this subject", value=True)
    
    if select_all:
        selected_topics = all_topics
        st.info("All topics selected! Uncheck the box above to pick specific topics.")
    else:
        selected_topics = st.multiselect("Pick specific topics to practice:", all_topics, default=all_topics[:3])

    st.markdown("### 🔢 Choose Quiz Length")
    num_questions = st.selectbox("How many questions?", [10, 20, 30, 40])
    
    if st.button("🚀 Generate Quiz"):
        with st.spinner(f"🧠 Generating {num_questions} questions... (This takes about 10-20 seconds)"):
            success = generate_quiz(selected_subject, selected_topics, num_questions, secret_api_key)
            if success:
                st.rerun()

st.markdown("---")

# ==========================================
# 5. ACTIVE QUIZ AREA
# ==========================================
if st.session_state.quiz_active and len(st.session_state.quiz_questions) > 0:
    
    total_q = len(st.session_state.quiz_questions)
    current_q_num = st.session_state.current_index + 1
    current_data = st.session_state.quiz_questions[st.session_state.current_index]
    
    # Top bar showing progress and score
    colA, colB = st.columns(2)
    with colA:
        st.markdown(f"**Question {current_q_num} of {total_q}**")
    with colB:
        st.markdown(f"**🏆 Score: {st.session_state.user_score}**", help="Points awarded for correct answers on the first try.")
    
    st.progress(current_q_num / total_q)
    
    # Display the Question
    st.info(current_data["question"])
    
    # We add the index to the key so the input box clears completely on every new question
    user_input = st.text_input("Type your answer below:", value="", key=f"ans_input_{st.session_state.current_index}")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("✔️ Check Answer"):
            target = str(current_data["answer"]).strip().lower()
            user_ans = user_input.strip().lower()
            
            if target == user_ans or target in user_ans:
                if not st.session_state.answered_current:
                    st.success("🎉 Correct! Great job.")
                    st.session_state.user_score += 1
                    st.session_state.answered_current = True
                else:
                    st.success("🎉 Correct!")
            else:
                st.error("❌ Not quite right yet. Have another look!")
                
    with col2:
        # Show "Next Question" or "Finish" depending on where we are in the list
        if current_q_num < total_q:
            if st.button("➡️ Next Question"):
                st.session_state.current_index += 1
                st.session_state.answered_current = False
                st.rerun()
        else:
            if st.button("🏁 Finish Quiz"):
                st.session_state.quiz_active = False
                st.balloons()
                st.success(f"Quiz Complete! Final Score: {st.session_state.user_score} / {total_q}")
                st.rerun()

    # The hint is now neatly tucked away at the bottom
    st.markdown("<br>", unsafe_allow_html=True) # Adds a little visual breathing room
    with st.expander("💡 Stuck? Click here for a Hint & Exam Technique"):
        st.markdown("### 🔍 Hint")
        st.warning(current_data["hint"])
        st.markdown("### ⏱️ Exam Technique")
        st.success(current_data["exam_technique"])
        
        # Optionally show the hidden answer for parent assistance
        st.markdown("---")
        st.write(f"*Parent check — Target Answer: {current_data['answer']}*")

elif not st.session_state.quiz_active:
    st.info("👈 Open the setup menu above to generate a new quiz!")
