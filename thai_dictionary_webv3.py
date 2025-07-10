import streamlit as st
import json
import os
import hashlib
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import base64

# ========== CONFIG ==========
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# ========== USER SESSION ==========
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {"password": hashlib.sha256("1234".encode()).hexdigest()}
    }
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def login_page():
    st.title("🔐 เข้าสู่ระบบ")
    st.markdown("""
        <style>
        input {
            background-color: #f0f0f0;
            color: black;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    username = st.text_input("👤 ชื่อผู้ใช้")
    password = st.text_input("🔑 รหัสผ่าน", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("เข้าสู่ระบบ"):
            if username in st.session_state.users and st.session_state.users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        if st.button("สมัครสมาชิก"):
            if username and password:
                if username in st.session_state.users:
                    st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
                else:
                    st.session_state.users[username] = {"password": hash_password(password)}
                    st.success("✅ สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ")
            else:
                st.warning("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ========== MAIN APP ==========
st.set_page_config(page_title="พจนานุกรม AI", layout="centered")
user_name = st.session_state.user

st.title("📘 พจนานุกรม AI")
col1, col2, col3 = st.columns([3, 2, 1])

with col1:
    query = st.text_input("🔍 คำที่ค้นหา:", "").strip().lower()
with col2:
    language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])
with col3:
    if st.button("🚪 ออกจากระบบ"):
        st.session_state.logged_in = False
        st.session_state.user = ""
        st.experimental_rerun()

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

def save_description(query, user, desc):
    if query not in memory:
        memory[query] = []
    memory[query].append({"name": user, "desc": desc})
    save_memory(memory)
    st.success("✅ บันทึกเรียบร้อย")

if query:
    direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
    lang_code = 'th' if direction == "th_to_en" else 'en'

    st.subheader("🔁 ผลจาก Google Translate")
    result = translate_word(query, direction=direction)
    st.write(f"**{query}** ➡️ **{result}**")
    reverse = translate_word(result, direction='en_to_th' if direction == 'th_to_en' else 'th_to_en')
    st.write(f"🔄 แปลย้อนกลับ: **{result}** ➡️ **{reverse}**")
    st.markdown("🔊 เสียงอ่าน:")
    audio = text_to_speech(query, lang=lang_code)
    if audio:
        st.markdown(audio, unsafe_allow_html=True)

    st.subheader("📚 ความหมายจาก Wikipedia")
    summary = wikipedia_summary(query)
    st.write(summary)
    audio_summary = text_to_speech(summary, lang=lang_code)
    if audio_summary:
        st.markdown("🔊 เสียงอ่านความหมาย:")
        st.markdown(audio_summary, unsafe_allow_html=True)

    st.subheader("🖼️ ภาพจาก Google")
    st.markdown(f"[🔗 ดูภาพ]({google_image(query)})")

    st.markdown("---")
    st.subheader("✍️ เพิ่มคำอธิบายของคุณ")
    new_desc = st.text_input("📝 คำอธิบาย:", "", key="desc_input")
    if st.button("💾 เพิ่มคำอธิบาย"):
        if query and user_name and new_desc.strip():
            save_description(query, user_name, new_desc.strip())

    if query in memory:
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
                    st.experimental_rerun()

# Footer
st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 AI โดย ChatGPT (OpenAI)")
