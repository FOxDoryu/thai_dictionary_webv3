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

# ====== USER DB in session ======
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {"password": hashlib.sha256("1234".encode()).hexdigest()},
    }

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ====== CSS for Login page with BG ======
login_css = """
<style>
body {
    margin: 0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: 
        linear-gradient(135deg, rgba(30,60,114,0.8), rgba(42,82,152,0.8)),
        url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1470&q=80') no-repeat center center fixed;
    background-size: cover;
    height: 100vh;
}
div[data-testid="stAppViewContainer"] > div:first-child {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 90vh;
}
.login-box {
    background: rgba(13,27,42,0.85);
    padding: 40px 50px;
    border-radius: 15px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    width: 360px;
    color: #fff;
    backdrop-filter: blur(8px);
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

# ====== Login Function ======
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = ""

    if not st.session_state.logged_in:
        st.markdown(login_css, unsafe_allow_html=True)
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h1>🔐 กรุณาเข้าสู่ระบบ</h1>", unsafe_allow_html=True)

        username = st.text_input("ชื่อผู้ใช้", key="login_user")
        password = st.text_input("รหัสผ่าน", type="password", key="login_pass")

        col1, col2 = st.columns([1,1])
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
                        st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว")
                    else:
                        st.session_state.users[username] = {"password": hash_password(password)}
                        st.success("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบใหม่")
                else:
                    st.warning("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")

        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

# ====== Logout Function ======
def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.experimental_rerun()

# ====== Main App ======
login()  # เรียก login

user_name = st.session_state.user

# Query params for refresh
query_params = st.query_params
if query_params.get("refresh") == ["true"]:
    st.set_query_params(refresh="false")
    st.experimental_rerun()

# Show logout button
st.sidebar.markdown(f"👤 ผู้ใช้: **{user_name}**")
if st.sidebar.button("🚪 ออกจากระบบ"):
    logout()

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

    new_desc = st.text_input("📝 คำอธิบาย:", key="new_desc")

    if st.button("💾 บันทึก"):
        if query and user_name and new_desc.strip():
            save_description(query, user_name, new_desc.strip())
            if "new_desc" in st.session_state:
                st.session_state.new_desc = ""  # ล้างช่องคำอธิบาย
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
