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

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# ====== USER & LOGIN ======
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {"password": hashlib.sha256("1234".encode()).hexdigest()},
    }

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# CSS สำหรับหน้า Login สวย ๆ
login_css = """
<style>
body {
    background: linear-gradient(135deg, #1e3c72, #2a5298);
    height: 100vh;
    margin: 0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
div[data-testid="stAppViewContainer"] > div:first-child {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 90vh;
}
.login-box {
    background: #0d1b2a;
    padding: 40px 50px;
    border-radius: 15px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
    width: 360px;
    color: #fff;
}
.login-box h1 {
    text-align: center;
    margin-bottom: 25px;
    font-weight: 700;
    font-size: 2.2rem;
    color: #00d8ff;
    text-shadow: 0 0 8px #00d8ff;
}
.login-box input[type="text"],
.login-box input[type="password"] {
    width: 100%;
    padding: 14px 20px;
    margin: 10px 0 20px 0;
    border: none;
    border-radius: 8px;
    background-color: #142850;
    color: #fff;
    font-size: 1rem;
    box-shadow: inset 0 0 8px #073763;
    transition: background-color 0.3s ease;
}
.login-box input[type="text"]:focus,
.login-box input[type="password"]:focus {
    background-color: #274c87;
    outline: none;
}
.login-box button {
    width: 48%;
    background: #00d8ff;
    border: none;
    padding: 14px 0;
    border-radius: 10px;
    color: #0d1b2a;
    font-weight: 700;
    font-size: 1.1rem;
    cursor: pointer;
    box-shadow: 0 5px 15px rgba(0,216,255,0.6);
    transition: background 0.3s ease;
    margin: 0 2% 10px 2%;
}
.login-box button:hover {
    background: #00b4cc;
    color: #fff;
}
.login-box .full-width {
    width: 100%;
    margin: 10px 0 0 0;
}
</style>
"""

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = ""

    if not st.session_state.logged_in:
        st.markdown(login_css, unsafe_allow_html=True)
        st.markdown("""
            <div class="login-box">
                <h1>🔐 เข้าสู่ระบบพจนานุกรม AI</h1>
            </div>
        """, unsafe_allow_html=True)

        username = st.text_input("", placeholder="👤 ชื่อผู้ใช้", key="login_user", label_visibility="collapsed")
        password = st.text_input("", placeholder="🔒 รหัสผ่าน", type="password", key="login_pass", label_visibility="collapsed")

        col1, col2 = st.columns([1,1], gap="small")
        with col1:
            if st.button("🚪 เข้าสู่ระบบ"):
                users = st.session_state.users
                if username in users and users[username]["password"] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.user = username
                    st.experimental_rerun()
                else:
                    st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        with col2:
            if st.button("📝 สมัครสมาชิก"):
                if username and password:
                    if username in st.session_state.users:
                        st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว")
                    else:
                        st.session_state.users[username] = {"password": hash_password(password)}
                        st.success("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบใหม่")
                else:
                    st.warning("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
        st.stop()

login()

user_name = st.session_state.user

# ====== MAIN DICTIONARY UI ======
query_params = st.query_params
if query_params.get("refresh") == ["true"]:
    st.set_query_params(refresh="false")
    st.experimental_rerun()

st.title("📘  พจนานุกรม AI ")

query = st.text_input("🔍 คำที่ค้นหา:", "").strip().lower()
language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])

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

    if "new_desc" not in st.session_state:
        st.session_state["new_desc"] = ""

    new_desc = st.text_input("📝 คำอธิบาย:", key="new_desc")

    if st.button("💾 บันทึก"):
        if query and user_name and new_desc.strip():
            save_description(query, user_name, new_desc.strip())
            # ล้างช่องคำอธิบายโดยใช้ form-reset trick:
            st.session_state["new_desc"] = ""
            st.experimental_set_query_params(refresh="true")
            st.experimental_rerun()

    if query in memory:
        st.markdown("---")
        st.subheader("📋 คำอธิบายทั้งหมดของคำนี้")
        # แสดงคำอธิบายที่เจ้าของเดียวกันกับ user เท่านั้นที่สามารถลบได้
        for i, item in enumerate(memory[query]):
            st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
            if item['name'] == user_name:
                if st.button(f"🗑️ ลบ ({i+1})", key=f"delete_{i}"):
                    memory[query].pop(i)
                    if not memory[query]:
                        del memory[query]
                    save_memory(memory)
                    st.warning("❌ ลบเรียบร้อยแล้ว")
                    st.experimental_set_query_params(refresh="true")
                    st.experimental_rerun()

if query:
    st.markdown("---")
    st.subheader(f"📂 คำอื่นๆ ที่มี \"{query}\" ในคำ")
    related = {k: v for k, v in memory.items() if query in k.lower() and k.lower() != query}
    for word, notes in related.items():
        st.markdown(f"- **{word}**")
        for j, note in enumerate(notes, 1):
            st.markdown(f"  {j}. {note['name']}: {note['desc']}")

st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 AI โดย ChatGPT (OpenAI)")

# ปุ่มออกจากระบบ มุมล่าง
if st.session_state.logged_in:
    if st.button("🚪 ออกจากระบบ"):
        st.session_state.logged_in = False
        st.session_state.user = ""
        st.experimental_rerun()
