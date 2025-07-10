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
USERS_FILE = 'users.json'

# ====== LOAD/SAVE ======
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

memory = load_memory()
users = load_users()

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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None

    if not st.session_state.logged_in:
        st.title("🔐 Login")
        username = st.text_input("ชื่อผู้ใช้")
        password = st.text_input("รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            if username in users and users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success(f"ยินดีต้อนรับ {username}!")
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

        st.markdown("---")
        st.subheader("สมัครสมาชิก")
        new_username = st.text_input("ชื่อผู้ใช้ใหม่")
        new_password = st.text_input("รหัสผ่านใหม่", type="password")
        if st.button("สมัครสมาชิก"):
            if new_username in users:
                st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว")
            elif new_username.strip() == "" or new_password.strip() == "":
                st.error("กรุณากรอกข้อมูลให้ครบ")
            else:
                users[new_username] = {"password": hash_password(new_password)}
                save_users(users)
                st.success("สมัครสมาชิกเรียบร้อย! กรุณาเข้าสู่ระบบ")
                st.experimental_rerun()
        return False
    else:
        st.sidebar.write(f"👤 ผู้ใช้งาน: **{st.session_state.user}**")
        if st.sidebar.button("ออกจากระบบ"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.experimental_rerun()
        return True

def save_description(query, user_name, desc):
    if query not in memory:
        memory[query] = []
    memory[query].append({"name": user_name, "desc": desc})
    save_memory(memory)
    st.success("✅ บันทึกเรียบร้อย")

def delete_description(query, idx):
    if query in memory and 0 <= idx < len(memory[query]):
        memory[query].pop(idx)
        if not memory[query]:
            del memory[query]
        save_memory(memory)
        st.warning("❌ ลบเรียบร้อยแล้ว")

# ====== UI START ======
st.set_page_config(page_title="พจนานุกรม AI", layout="centered")

# --- เช็ค Login ---
if not login():
    st.stop()  # หยุดโปรแกรมถ้ายังไม่ล็อกอิน

# --- ส่วนหลักของโปรแกรม ---

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

st.title("📘  พจนานุกรม AI")

query = st.text_input("🔍 คำที่ค้นหา:", "").strip().lower()
language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])
user_name = st.session_state.user  # ใช้ user ที่ล็อกอินแทน

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
        if query and new_desc:
            save_description(query, user_name, new_desc)
            st.session_state.new_desc = ""  # ล้างช่องคำอธิบาย

    if query in memory:
        st.markdown("---")
        st.subheader("📋 คำอธิบายทั้งหมดของคำนี้")
        for i, item in enumerate(memory[query]):
            st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
            if item['name'] == user_name:
                if st.button(f"🗑️ ลบรายการที่ {i+1}", key=f"del_{i}"):
                    delete_description(query, i)
                    st.experimental_rerun()

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
