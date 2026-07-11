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
    p, label, li, .stMarkdown, .stText {
        font-family: 'Verdana', 'Comic Sans MS', sans-serif !important;
        font-size: 19px !important;
        line-height: 1.8 !important;
        letter-spacing: 0.06em !important;
    }
    h1, h2, h3, h4 { font-family: 'Verdana', sans-serif !important; color: #1a365d !important; font-weight: bold !important; margin-bottom: 20px !important; }
    .stButton>button { 
        background-color: #e0f2fe !important; color: #0369a1 !important; border: 2px solid #0369a1 !important; 
        border-radius: 10px !important; font-size: 18px !important; font-weight: bold !important; 
        padding: 10px 24px !important; transition: all 0.2s ease; 
    }
    .stButton>button:hover { background-color: #bae6fd !important; border-color: #0284c7 !important; }
    .stProgress > div > div > div > div { background-color: #0369a1 !important; }
    .stRadio label { font-size: 20px !important; padding-bottom: 8px !important; }
    
    /* Highlight for the streak counter */
    .streak-box {
        background-color: #fffbeb; border: 2px solid #f59e0b; color: #b45309;
        padding: 8px 15px; border-radius: 8px; font-weight: bold; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FULL SYLLABUS MENU
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

# Praise phrases to keep the feedback fresh
PRAISE = ["Brilliant job!", "You're a superstar! 🌟", "Spot on!", "Fantastic work!", "You nailed it! 🔨", "Absolutely right!"]

# ==========================================
# 3. AI STRUCTURE & STATE MANAGEMENT
# ==========================================
class QuestionData(BaseModel):
    question: str = Field(description="The GL 11+ style question text. DO NOT include the options in this text.")
    option_a: str = Field(description="The text for option A")
    option_b: str = Field(description="The text for option B")
    option_c: str = Field(description="The text for option C")
    option_d: str = Field(description="The text for option D")
    option_e: str = Field(description="The text for option E")
    correct_letter: str = Field(description="The correct answer letter, exactly 'A', 'B', 'C', 'D', or 'E'")
    hint: str = Field(description="A clear, dyslexia-friendly hint to solve the problem.")
    exam_technique: str = Field(description="An exam technique or time-saving trick for this type of question.")

class QuizData(BaseModel):
    questions: list[QuestionData]

if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "user_score" not in st.session_state:
    st.session_state.user_score = 0
if "current_streak" not in st.session_state:
    st.session_state.current_streak = 0
if "highest_streak" not in st.session_state:
    st.session_state.highest_streak = 0
if "answered_current" not in st.session_state:
    st.session_state.answered_current = False
if "current_subject" not in st.session_state:
    st.session_state.current_subject = "English"

def generate_quiz(subject, selected_topics, num_questions, api_key):
    if not api_key:
        st.error("Please ensure your API key is in Streamlit Secrets.")
        return False
    if not selected_topics:
        st.error("Please select at least one topic.")
        return False

    client = genai.Client(api_key=api_key)
    
   def generate_quiz(subject, selected_topics, num_questions, api_key):
    if not api_key:
        st.error("Please ensure your API key is in Streamlit Secrets.")
        return False

    client = genai.Client(api_key=api_key)
    
    # We provide an example of a perfect puzzle to "teach" the AI
    prompt = f"""
    You are a professional GL 11+ exam question creator. Generate {num_questions} questions for {subject} covering: {', '.join(selected_topics)}.
    
    ### GOLD STANDARD EXAMPLE (Follow this logic strictly):
    Topic: Letter-Word Codes
    Question: Four words: MATE, TEAM, TAME, MEAT. Three codes: 4123, 3124, 2143. What is the code for TEAM?
    Logic Check: 
    - MATE: letters M-A-T-E map to 4-1-2-3
    - TEAM: letters T-E-A-M map to 2-3-1-4
    - TAME: letters T-A-M-E map to 2-1-4-3
    - MEAT: letters M-E-A-T map to 4-3-1-2
    (The AI must generate a coherent mapping like this before outputting the question).
    
    ### MANDATORY RULES:
    1. SOLVABILITY: Before generating, create a logic table in your 'mind'. If you cannot map the numbers to letters consistently, do not output the question.
    2. STRUCTURE: Provide exactly 5 options (A, B, C, D, E).
    3. HINTS/TECHNIQUE: Hints must explain the deduction method.
    4. VARIETY: Do not repeat the same question twice.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': QuizData,
                'temperature': 0.1, # Even tighter logic control
            }
        )
        # ... rest of your existing function code remains the same ...
        data = json.loads(response.text)
        st.session_state.quiz_questions = data["questions"]
        st.session_state.user_answers = {}
        st.session_state.current_index = 0
        st.session_state.user_score = 0
        st.session_state.quiz_active = True
        st.session_state.review_mode = False
        st.session_state.current_subject = subject
        return True
    except Exception as e:
        st.error(f"Failed to generate questions. Error: {e}")
        return False

# ==========================================
# 4. APP INTERFACE & SETUP MENU
# ==========================================
st.title("GL 11+ Practice Partner")

try:
    secret_api_key = st.secrets["GEMINI_API_KEY"]
except:
    secret_api_key = ""

with st.expander("Quiz Setup", expanded=(not st.session_state.quiz_active)):
    selected_subject = st.selectbox("Choose Subject", ["English", "Verbal Reasoning"])
    st.markdown("### Choose Topics")
    all_topics = TOPICS[selected_subject]
    
    select_all = st.checkbox("Select ALL topics in this subject", value=True)
    selected_topics = []
    
    if select_all:
        selected_topics = all_topics
    else:
        col1, col2 = st.columns(2)
        for i, topic in enumerate(all_topics):
            with (col1 if i % 2 == 0 else col2):
                if st.checkbox(topic, key=f"cb_{selected_subject}_{i}"):
                    selected_topics.append(topic)

    st.markdown("### Choose Quiz Length")
    num_questions = st.selectbox("How many questions?", [10, 20, 30, 40])
    
    if st.button("Generate Quiz"):
        with st.spinner(f"Generating {num_questions} questions..."):
            success = generate_quiz(selected_subject, selected_topics, num_questions, secret_api_key)
            if success:
                st.rerun()
st.markdown("---")

# ==========================================
# 5. ALPHABET HELPER (FOR VR ONLY)
# ==========================================
if st.session_state.quiz_active and st.session_state.current_subject == "Verbal Reasoning":
    st.markdown("""
    <div style="background-color: #ffffff; padding: 15px; border-radius: 8px; border: 2px solid #cbd5e1; text-align: center; margin-bottom: 25px;">
        <div style="font-family: 'Courier New', Courier, monospace; font-size: 22px; font-weight: bold; letter-spacing: 6px; color: #1e293b;">
            A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
        </div>
        <div style="font-family: 'Courier New', Courier, monospace; font-size: 14px; letter-spacing: 12px; color: #64748b; margin-left: 6px;">
            1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 6. ACTIVE QUIZ AREA
# ==========================================
if st.session_state.quiz_active and len(st.session_state.quiz_questions) > 0:
    
    total_q = len(st.session_state.quiz_questions)
    current_q_num = st.session_state.current_index + 1
    current_data = st.session_state.quiz_questions[st.session_state.current_index]
    
    # Header area with Score and Streak Tracker
    colA, colB, colC = st.columns([1, 1, 1.2])
    with colA:
        st.markdown(f"**Question {current_q_num} of {total_q}**")
    with colB:
        st.markdown(f"**🏅 Score: {st.session_state.user_score}**")
    with colC:
        if st.session_state.current_streak >= 2:
            st.markdown(f"<div class='streak-box'>🔥 {st.session_state.current_streak} in a row!</div>", unsafe_allow_html=True)
    
    st.progress(current_q_num / total_q)
    st.info(current_data["question"])
    
    radio_options = [
        f"A) {current_data['option_a']}", f"B) {current_data['option_b']}",
        f"C) {current_data['option_c']}", f"D) {current_data['option_d']}", f"E) {current_data['option_e']}"
    ]
    
    user_choice = st.radio("Select your answer:", radio_options, index=None, key=f"radio_{st.session_state.current_index}")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Check Answer"):
            if user_choice:
                selected_letter = user_choice[0]
                target_letter = current_data["correct_letter"]
                
                if selected_letter == target_letter:
                    if not st.session_state.answered_current:
                        # Correct Answer Logic
                        st.session_state.user_score += 1
                        st.session_state.current_streak += 1
                        st.session_state.answered_current = True
                        
                        if st.session_state.current_streak > st.session_state.highest_streak:
                            st.session_state.highest_streak = st.session_state.current_streak
                        
                        # Big celebration for every 3 in a row
                        if st.session_state.current_streak > 0 and st.session_state.current_streak % 3 == 0:
                            st.balloons()
                            st.success(f"🔥 YOU ARE ON FIRE! {st.session_state.current_streak} in a row! {random.choice(PRAISE)}")
                        else:
                            st.success(f"🎉 {random.choice(PRAISE)}")
                    else:
                        st.success("Correct!")
                else:
                    # Incorrect Answer Logic - Gentle correction
                    if not st.session_state.answered_current:
                        st.session_state.current_streak = 0
                    st.error("Not quite right! Great try though. Pop open the hint below and let's crack it.")
            else:
                st.warning("Please select an answer first.")
                
    with col2:
        if current_q_num < total_q:
            if st.button("Next Question"):
                st.session_state.current_index += 1
                st.session_state.answered_current = False
                st.rerun()
        else:
            if st.button("Finish Quiz"):
                st.session_state.quiz_active = False
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Stuck? Click here for a Hint & Exam Technique"):
        st.markdown("### Hint")
        st.warning(current_data["hint"])
        st.markdown("### Exam Technique")
        st.success(current_data["exam_technique"])
        st.markdown("---")
        st.write(f"*Parent check — Correct Answer: {current_data['correct_letter']}*")

# ==========================================
# 7. END OF QUIZ REWARD SCREEN
# ==========================================
elif not st.session_state.quiz_active and st.session_state.user_score > 0:
    total = len(st.session_state.quiz_questions)
    percentage = (st.session_state.user_score / total) * 100
    
    st.balloons()
    st.markdown("## 🏁 Quiz Complete!")
    
    # Calculate Trophy based on percentage
    if percentage == 100:
        st.markdown("### 🏆 Platinum Trophy! Absolutely flawless.")
    elif percentage >= 80:
        st.markdown("### 🥇 Gold Medal! Outstanding effort.")
    elif percentage >= 60:
        st.markdown("### 🥈 Silver Medal! Great work.")
    else:
        st.markdown("### 🥉 Bronze Medal! Excellent practice today.")
        
    st.write(f"**Final Score:** {st.session_state.user_score} out of {total} ({int(percentage)}%)")
    st.write(f"**Longest Hot Streak:** 🔥 {st.session_state.highest_streak} correct in a row")
    
    st.info("To play again, open the Quiz Setup menu at the top of the screen!")

elif not st.session_state.quiz_active:
    st.info("Open the setup menu above to generate a new quiz!")
