import streamlit as st
from deep_translator import GoogleTranslator
import wikipedia
import json
import os
from gtts import gTTS
import base64
import hashlib

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

# ====== USER DB (เก็บไว้ใน session_state หรือไฟล์จริงก็ได้) ======
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {
            "password": hashlib.sha256("1234".encode()).hexdigest()
        },
    }

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

# ====== LOGIN FUNCTION ======
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = ""

    if not st.session_state.logged_in:
        st.title("🔐 กรุณาเข้าสู่ระบบ")

        username = st.text_input("ชื่อผู้ใช้", key="login_username")
        password = st.text_input("รหัสผ่าน", type="password", key="login_password")
        login_clicked = st.button("เข้าสู่ระบบ")

        if login_clicked:
            users = st.session_state.users
            if username in users and users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success(f"ยินดีต้อนรับ {username}!")
                return True, True  # logged in, rerun needed
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
                return False, False

        signup_clicked = st.button("สมัครสมาชิก")
        if signup_clicked:
            if username and password:
                if username in st.session_state.users:
                    st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว")
                else:
                    st.session_state.users[username] = {"password": hash_password(password)}
                    st.success("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบใหม่")
            else:
                st.warning("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
        return False, False
    else:
        return True, False

# ====== MAIN APP START ======
st.set_page_config(page_title="พจนานุกรม AI", layout="centered")

if "new_desc" not in st.session_state:
    st.session_state["new_desc"] = ""

# **ตรงนี้เปลี่ยนจาก experimental_get_query_params เป็น st.query_params**
query_params = st.query_params
if query_params.get("refresh") == ["true"]:
    st.set_query_params(refresh="false")
    st.experimental_rerun()

logged_in, rerun_needed = login()
if rerun_needed:
    st.experimental_rerun()
if not logged_in:
    st.stop()

user_name = st.session_state.user

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

def save_description(query, user, desc):
    if query not in memory:
        memory[query] = []
    memory[query].append({"name": user, "desc": desc})
    save_memory(memory)
    st.success("✅ บันทึกเรียบร้อย")

if query:
    direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
    lang_code = 'th' if direction == "th_to_en" else 'en'

    with st.expander("🔁 ผลจาก Google Translate"):
        result = translate_word(query, direction=direction)
        st.write(f"**{query}** ➡️ **{result}**")
        reverse = translate_word(result, direction='en_to_th' if direction == 'th_to_en' else 'th_to_en')
        st.write(f"🔄 แปลย้อนกลับ: **{result}** ➡️ **{reverse}**")
        st.markdown("---")
        st.markdown("🔊 เสียงอ่าน:")
        audio = text_to_speech(query, lang=lang_code)
        if audio:
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

    st.markdown("---")
    st.subheader("✍️ เพิ่มคำอธิบายของคุณ")

    new_desc = st.text_input("📝 คำอธิบาย:", key="new_desc")

    if st.button("💾 บันทึก"):
        if query and user_name and new_desc.strip():
            save_description(query, user_name, new_desc.strip())
            st.session_state["new_desc"] = ""  # ล้างช่องคำอธิบาย
            # เปลี่ยนจาก experimental_set_query_params เป็น set_query_params
            st.set_query_params(refresh="true")

    if query in memory:
        st.markdown("---")
        st.subheader("📋 คำอธิบายทั้งหมดของคำนี้")
        for i, item in enumerate(memory[query]):
            st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
            if item['name'] == user_name:
                if st.button(f"🗑️ ลบ ({i+1})", key=f"delete_{i}"):
                    memory[query].pop(i)
                    if not memory[query]:
                        del memory[query]
                    save_memory(memory)
                    st.warning("❌ ลบเรียบร้อยแล้ว")
                    st.set_query_params(refresh="true")

# แสดงคำอื่นที่มีคำค้นนี้อยู่ในคำ
if query:
    st.markdown("---")
    st.subheader(f"📂 คำอื่นๆ ที่มี \"{query}\" ในคำ")
    related = {k: v for k, v in memory.items() if query in k.lower() and k.lower() != query}
    for word, notes in related.items():
        st.markdown(f"- **{word}**")
        for j, note in enumerate(notes, 1):
            st.markdown(f"  {j}. {note['name']}: {note['desc']}")

# CREDIT
st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 AI โดย ChatGPT (OpenAI)")
