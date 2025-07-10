import streamlit as st
import json
import os
import hashlib
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import base64

# --- Config ---
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

# --- Functions ---

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

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

# --- Initialization ---

if 'users' not in st.session_state:
    # เริ่มต้น user เดิม
    st.session_state.users = {
        "admin": {"password": hash_password("1234")}
    }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'user' not in st.session_state:
    st.session_state.user = ""

if 'memory' not in st.session_state:
    st.session_state.memory = load_memory()

# --- Login Page ---

def login_page():
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 80px auto;
        padding: 30px;
        background: #273c75;
        border-radius: 15px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .login-container h2 {
        text-align: center;
        margin-bottom: 25px;
        color: #00a8ff;
        text-shadow: 0 0 8px #00a8ff;
    }
    .login-container input, .login-container button {
        width: 100%;
        padding: 12px;
        margin: 8px 0;
        border-radius: 10px;
        border: none;
        font-size: 1rem;
    }
    .login-container input {
        background: #192a56;
        color: white;
    }
    .login-container button {
        background: #00a8ff;
        color: #192a56;
        font-weight: 700;
        cursor: pointer;
        transition: background 0.3s ease;
    }
    .login-container button:hover {
        background: #0097e6;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("<h2>เข้าสู่ระบบ พจนานุกรม AI</h2>", unsafe_allow_html=True)

    username = st.text_input("ชื่อผู้ใช้", key="login_user")
    password = st.text_input("รหัสผ่าน", type="password", key="login_pass")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("เข้าสู่ระบบ"):
            if username in st.session_state.users and st.session_state.users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        if st.button("สมัครสมาชิก"):
            if username and password:
                if username in st.session_state.users:
                    st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
                else:
                    st.session_state.users[username] = {"password": hash_password(password)}
                    st.success("สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ")
            else:
                st.warning("กรุณากรอกชื่อและรหัสผ่าน")

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- Logout Function ---

def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.experimental_rerun()

# --- Main App ---

if not st.session_state.logged_in:
    login_page()

st.sidebar.markdown(f"👤 ผู้ใช้: **{st.session_state.user}**")
if st.sidebar.button("🚪 ออกจากระบบ"):
    logout()

st.title("📘 พจนานุกรม AI")

query = st.text_input("🔍 คำที่ค้นหา:", key="query").strip().lower()
language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])
new_desc = st.text_input("📝 เพิ่มคำอธิบายของคุณ:", key="new_desc")

def save_description():
    q = st.session_state.query
    desc = st.session_state.new_desc.strip()
    user = st.session_state.user
    if not q:
        st.warning("กรุณากรอกคำที่ต้องการค้นหา")
        return
    if not desc:
        st.warning("กรุณากรอกคำอธิบาย")
        return
    if q not in st.session_state.memory:
        st.session_state.memory[q] = []
    st.session_state.memory[q].append({"name": user, "desc": desc})
    save_memory(st.session_state.memory)
    st.success("✅ บันทึกเรียบร้อย")
    st.session_state.new_desc = ""

if st.button("💾 บันทึก", on_click=save_description):
    pass

if query:
    direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
    lang_code = "th" if direction == "th_to_en" else "en"

    with st.expander("🔁 ผลจาก Google Translate", expanded=True):
        translated = translate_word(query, direction)
        st.write(f"**{query}** ➡️ **{translated}**")
        back_translated = translate_word(translated, "en_to_th" if direction == "th_to_en" else "th_to_en")
        st.write(f"🔄 แปลย้อนกลับ: **{translated}** ➡️ **{back_translated}**")
        audio = text_to_speech(query, lang=lang_code)
        if audio:
            st.markdown("🔊 เสียงอ่าน:")
            st.markdown(audio, unsafe_allow_html=True)

    with st.expander("📚 ความหมายจาก Wikipedia"):
        summary = wikipedia_summary(query)
        st.write(summary)
        audio_summary = text_to_speech(summary, lang=lang_code)
        if audio_summary:
            st.markdown("🔊 เสียงอ่านความหมาย:")
            st.markdown(audio_summary, unsafe_allow_html=True)

    with st.expander("🖼️ ภาพจาก Google"):
        st.markdown(f"[🔗 ดูภาพ]({google_image(query)})")

    # แสดงคำอธิบาย
    if query in st.session_state.memory:
        st.markdown("---")
        st.subheader("📋 คำอธิบายทั้งหมดของคำนี้")
        for i, item in enumerate(st.session_state.memory[query]):
            st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
            if item['name'] == st.session_state.user:
                btn_key = f"del_{query}_{i}"
                if st.button(f"🗑️ ลบ ({i+1})", key=btn_key):
                    st.session_state.memory[query].pop(i)
                    if not st.session_state.memory[query]:
                        del st.session_state.memory[query]
                    save_memory(st.session_state.memory)
                    st.experimental_rerun()

st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 AI โดย ChatGPT (OpenAI)")
