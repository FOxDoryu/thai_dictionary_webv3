import streamlit as st
import json
import os
import hashlib
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import base64

# ====== CONFIG ======
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

# ====== LOAD/SAVE ======
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# ====== Session Init ======
if "users" not in st.session_state:
    st.session_state["users"] = {
        "admin": {"password": hashlib.sha256("1234".encode()).hexdigest()},
    }
if "user" not in st.session_state:
    st.session_state["user"] = None
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "new_desc" not in st.session_state:
    st.session_state["new_desc"] = ""

# ====== FUNCTION ======
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def login_page():
    st.markdown(
        """
        <style>
        .login-input input {
            background-color: #f0f0f0;
            color: black;
            border-radius: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🔐 เข้าสู่ระบบ")
    username = st.text_input("👤 ชื่อผู้ใช้", key="login_user", placeholder="ชื่อผู้ใช้", label_visibility="visible")
    password = st.text_input("🔒 รหัสผ่าน", type="password", key="login_pass", placeholder="รหัสผ่าน", label_visibility="visible")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ เข้าสู่ระบบ"):
            if username in st.session_state.users and st.session_state.users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        if st.button("🆕 สมัครสมาชิก"):
            if username and password:
                if username in st.session_state.users:
                    st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
                else:
                    st.session_state.users[username] = {"password": hash_password(password)}
                    st.success("✅ สมัครสมาชิกสำเร็จแล้ว")
            else:
                st.warning("กรุณากรอกชื่อและรหัสผ่าน")

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

def logout():
    st.session_state.user = None
    st.session_state.logged_in = False
    st.rerun()

# ====== MAIN PAGE ======
if not st.session_state.logged_in:
    login_page()
    st.stop()

# ====== UI START ======
st.set_page_config(page_title="พจนานุกรม AI", layout="centered")

st.title("📘 พจนานุกรม AI")

col1, col2, col3 = st.columns([3, 2, 2])
with col1:
    query = st.text_input("🔍 คำที่ค้นหา", "").strip().lower()
with col2:
    language = st.radio("🌍 ภาษา", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"], horizontal=True)
with col3:
    if st.button("🚪 ออกจากระบบ"):
        logout()

if query:
    direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
    lang_code = 'th' if direction == "th_to_en" else 'en'

    with st.expander("🔁 ผลจาก Google Translate"):
        result = translate_word(query, direction=direction)
        st.write(f"**{query}** ➡️ **{result}**")
        reverse = translate_word(result, direction='en_to_th' if direction == 'th_to_en' else 'th_to_en')
        st.write(f"🔄 แปลย้อนกลับ: **{result}** ➡️ **{reverse}**")
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

    # บันทึกคำอธิบาย
    st.markdown("### ✍️ เพิ่มคำอธิบายของคุณ")
    st.session_state.new_desc = st.text_input("📝 คำอธิบาย", value=st.session_state.new_desc, key="new_desc_input")

    if st.button("💾 บันทึกคำอธิบาย"):
        if st.session_state.new_desc.strip():
            if query not in memory:
                memory[query] = []
            memory[query].append({"name": st.session_state.user, "desc": st.session_state.new_desc.strip()})
            save_memory(memory)
            st.success("✅ บันทึกเรียบร้อย")
            st.session_state.new_desc = ""
            st.rerun()

    # แสดงคำอธิบาย
    if query in memory:
        st.markdown("### 📋 คำอธิบายทั้งหมด")
        for i, item in enumerate(memory[query]):
            st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
            if item['name'] == st.session_state.user:
                if st.button(f"🗑️ ลบ ({i+1})", key=f"delete_{i}"):
                    memory[query].pop(i)
                    if not memory[query]:
                        del memory[query]
                    save_memory(memory)
                    st.warning("❌ ลบเรียบร้อยแล้ว")
                    st.rerun()

# แสดงคำอื่นที่มีคำค้นนี้
if query:
    st.markdown("---")
    st.subheader(f"📂 คำอื่นๆ ที่มี \"{query}\" ในคำ")
    related = {k: v for k, v in memory.items() if query in k.lower() and k.lower() != query}
    for word, notes in related.items():
        st.markdown(f"- **{word}**")
        for j, note in enumerate(notes, 1):
            st.markdown(f"  {j}. {note['name']}: {note['desc']}")

# ผู้จัดทำ
st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 AI โดย ChatGPT (OpenAI)")
