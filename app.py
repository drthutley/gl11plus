import streamlit as st
import random
import json
from google import genai
from pydantic import BaseModel, Field

# ==========================================
# 1. PAGE CONFIG & DYSLEXIA-FRIENDLY CSS
# ==========================================
st.set_page_config(
    page_title="GL 11+ Practice Partner",
    page_icon="✏️",
    layout="centered"
)

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
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #fef2f2 !important; color: #991b1b !important; border: 2px solid #f87171 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover { background-color: #fee2e2 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FULL SYLLABUS MENU (From Your Images)
# ==========================================
SYLLABUS_MENU = {
    "English": {
        "Section One — Grammar": ["Parts of Speech", "Verbs", "Mixed Grammar Questions"],
        "Section Two — Punctuation": ["Starting and Ending Sentences", "Commas and Brackets", "Dashes and Apostrophes", "Inverted Commas and Colons", "Mixed Punctuation Questions"],
        "Section Three — Spelling": ["Plurals", "Homophones", "Prefixes and Suffixes", "Awkward Spellings", "Mixed Spelling Questions"],
        "Section Four — Writers' Techniques": ["Alliteration and Onomatopoeia", "Imagery", "Abbreviations", "Synonyms and Antonyms", "Spotting and Understanding Devices"],
        "Section Five — Writing": ["Writing Fiction", "Writing Non-Fiction"]
    },
    "Verbal Reasoning": {
        "Section One — The Alphabet": ["Alphabet Positions", "Identify a Letter from a Clue", "Alphabetical Order"],
        "Section Two — Making Words": ["Missing Letters", "Move a Letter", "Hidden Word", "Find the Missing Word", "Use a Rule to Make a Word", "Compound Words", "Forming New Words", "Complete a Word Pair", "Anagram in a Sentence", "Word Ladders"],
        "Section Three — Word Meanings": ["Closest Meaning", "Opposite Meaning", "Multiple Meanings", "Odd Ones Out", "Word Connections", "Reorder Words to Make a Sentence"],
        "Section Four — Maths and Sequences": ["Complete the Sum", "Letter Sequences", "Number Sequences", "Related Numbers", "Letter-Coded Sums"],
        "Section Five — Logic and Coding": ["Letter Connections", "Letter-Word Codes", "Number-Word Codes", "Explore the Facts", "Solve the Riddle", "Word Grids"]
    }
}

# ==========================================
# 3. AI STRUCTURE & STATE MANAGEMENT
# ==========================================
# This forces the AI to return exactly what our app needs
class QuestionData(BaseModel):
    question: str = Field(description="The GL 11+ style question text. Include multiple choice options in the text if applicable.")
    answer: str = Field(description="The exact target answer word or number.")
    hint: str = Field(description="A clear, dyslexia-friendly tip breaking down the rule.")

if "current_q" not in st.session_state:
    st.session_state.current_q = None
if "hint_clicked" not in st.session_state:
    st.session_state.hint_clicked = False
if "user_score" not in st.session_state:
    st.session_state.user_score = 0
if "answered" not in st.session_state:
    st.session_state.answered = False

def generate_ai_question(subject, section, topic, api_key):
    if not api_key:
        st.sidebar.error("⚠️ Please enter your Gemini API Key first.")
        return

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert tutor for the UK GL 11+ exams. Generate a single, unique practice question for:
    Subject: {subject} | Section: {section} | Topic: {topic}
    
    Requirements:
    1. Strictly align with the GL 11+ standard for this specific topic.
    2. If the topic requires multiple choice, format the options clearly within the question text.
    3. The answer must be a single word, short phrase, or number.
    4. The hint MUST be dyslexia-friendly: clear, simple vocabulary, relaxed phrasing, and directly explain the rule without giving away the exact answer.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': QuestionData,
                'temperature': 0.7, # Adds a bit of creative variance so questions don't repeat
            }
        )
        data = json.loads(response.text)
        st.session_state.current_q = data
        st.session_state.hint_clicked = False
        st.session_state.answered = False
    except Exception as e:
        st.error(f"Failed to generate question. Please check your API key or try again. Error: {e}")

# ==========================================
# 4. APP INTERFACE & SIDEBAR
# ==========================================
st.title("✏️ GL 11+ Practice Partner")

# Sidebar Configuration
st.sidebar.header("🔑 AI Setup")
api_key_input = st.sidebar.text_input("Enter Gemini API Key", type="password")
st.sidebar.markdown("[Get a free API key here](https://aistudio.google.com/app/apikey)")
st.sidebar.markdown("---")

st.sidebar.header("📋 Subject Selection")
selected_subject = st.sidebar.selectbox("Choose Subject", list(SYLLABUS_MENU.keys()))
selected_section = st.sidebar.selectbox("Choose Section", list(SYLLABUS_MENU[selected_subject].keys()))
selected_topic = st.sidebar.selectbox("Choose Topic Type", SYLLABUS_MENU[selected_subject][selected_section])

if st.sidebar.button("✨ Generate New Question"):
    with st.spinner("🧠 Generating a unique 11+ challenge..."):
        generate_ai_question(selected_subject, selected_section, selected_topic, api_key_input)

st.sidebar.markdown(f"### 🏆 Current Score: `{st.session_state.user_score}`")
st.markdown("---")

# ==========================================
# 5. JAVASCRIPT TIMER
# ==========================================
timer_html = """
<div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
    <div id="countdown-box" style="font-size: 22px; font-weight: bold; color: #0c4a6e; background-color: #e0f2fe; padding: 10px 20px; border-radius: 8px; border: 2px solid #0284c7;">
        ⏱️ Time Left: <span id="timer">02:00</span>
    </div>
</div>
<script>
    var targetTime = 120; 
    var timerDisplay = document.getElementById("timer");
    var countdown = setInterval(function() {
        var minutes = Math.floor(targetTime / 60);
        var seconds = targetTime % 60;
        if (seconds < 10) { seconds = "0" + seconds; }
        timerDisplay.textContent = minutes + ":" + seconds;
        if (targetTime <= 0) {
            clearInterval(countdown);
            document.getElementById("countdown-box").style.backgroundColor = "#fee2e2";
            document.getElementById("countdown-box").style.borderColor = "#ef4444";
            document.getElementById("countdown-box").style.color = "#991b1b";
            timerDisplay.textContent = "Time's Up!";
        }
        targetTime--;
    }, 1000);
</script>
"""
st.components.v1.html(timer_html, height=65)

# ==========================================
# 6. ACTIVE PRACTICE AREA
# ==========================================
if st.session_state.current_q:
    st.markdown("### ❓ Question Challenge:")
    st.info(st.session_state.current_q["question"])
    
    user_input = st.text_input("Type your answer below:", value="", key="user_answer_field")
    
    col1, col2, col3 = st.columns([1.2, 1.5, 1])
    
    with col1:
        if st.button("✔️ Check Answer"):
            # Simple check: if the target answer is inside the user's text or vice versa
            target = str(st.session_state.current_q["answer"]).strip().lower()
            user_ans = user_input.strip().lower()
            
            if target == user_ans or target in user_ans:
                if not st.session_state.answered:
                    st.success("🎉 Correct! Spot on.")
                    st.session_state.user_score += 1
                    st.session_state.answered = True
            else:
                st.error("❌ Not quite right yet. Try using a hint or double-check your spelling!")
                
    with col2:
        if st.button("💡 Stuck? Show Hint"):
            st.session_state.hint_clicked = True
            
    with col3:
        if st.button("➡️ Next Question"):
            with st.spinner("🧠 Generating next challenge..."):
                generate_ai_question(selected_subject, selected_section, selected_topic, api_key_input)
            st.rerun()

    if st.session_state.hint_clicked:
        st.markdown("#### 🔍 Clue Panel:")
        st.warning(st.session_state.current_q["hint"])
        # Optionally show the hidden answer for parent assistance
        with st.expander("Show Answer (Parent view)"):
            st.write(f"**Target Answer:** {st.session_state.current_q['answer']}")
else:
    st.info("👈 Enter your API Key in the sidebar and click **Generate New Question** to begin!")
