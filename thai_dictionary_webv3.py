import streamlit as st
from deep_translator import GoogleTranslator
import wikipedia
import json
import os
from gtts import gTTS
import base64

# ====== CONFIG ======
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

# ====== LOAD/SAVE ======
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# ====== FUNCTIONS ======
def translate_word(word, direction="th_to_en"):
    try:
        return GoogleTranslator(
            source='th' if direction == 'th_to_en' else 'en',
            target='en' if direction == 'th_to_en' else 'th'
        ).translate(word)
    except:
        return "(ไม่สามารถแปลได้)"

def wikipedia_summary(word):
    try:
        return wikipedia.summary(word, sentences=2)
    except:
        return "(ไม่พบข้อมูลจาก Wikipedia)"

def google_image(word):
    return f"https://www.google.com/search?tbm=isch&q={word}"

def text_to_speech(text, lang='th', slow=False):
    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.save("temp.mp3")
        with open("temp.mp3", "rb") as f:
            audio_bytes = f.read()
        b64 = base64.b64encode(audio_bytes).decode()
        return f'<audio controls><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except:
        return None

# ====== UI START ======
st.set_page_config(page_title="พจนานุกรม AI", layout="centered")

# เช็ค query params เพื่อ refresh
query_params = st.experimental_get_query_params()
if query_params.get("refresh") == ["true"]:
    st.experimental_set_query_params(refresh="false")
    st.experimental_rerun()

st.markdown("""
    <style>
    .stTextInput>div>div>input {
        background-color: #4a4a4a;
        color: white;
        border-radius: 5px;
        padding: 8px;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📘  พจนานุกรม AI ")

query = st.text_input("🔍 คำที่ค้นหา:", "").strip().lower()
language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])
user_name = st.text_input("👤 ชื่อของคุณ:", key="user_name").strip()

def save_description():
    if query and user_name and st.session_state.new_desc:
        if query not in memory:
            memory[query] = []
        memory[query].append({"name": user_name, "desc": st.session_state.new_desc})
        save_memory(memory)
        st.success("✅ บันทึกเรียบร้อย")
        st.session_state.new_desc = ""  # ล้างช่องคำอธิบาย
        st.experimental_set_query_params(refresh="true")
        st.experimental_rerun()

new_desc = st.text_input("📝 คำอธิบาย:", key="new_desc")

if st.button("💾 บันทึก"):
    save_description()

# ... (ส่วนอื่นของโค้ดยังคงเหมือนเดิม)

# CREDIT
st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 AI โดย ChatGPT (OpenAI)")
