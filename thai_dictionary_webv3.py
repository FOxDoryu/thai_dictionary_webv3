import streamlit as st
import json
import os
import hashlib
import smtplib
import random
import base64
import uuid
from io import BytesIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS

# === CONFIG ===
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'
USER_FILE = 'users.json'
OTP_STORE = {}
EMAIL = "guzz9777@gmail.com"  # ใส่อีเมลของคุณ
APP_PASSWORD = "pqgo hjcx dbqm pjsk"  # ใส่รหัสผ่านแอป

# === MEMORY ===
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

# === USER ===
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# === PASSWORD ===
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# === SEND OTP ===
def send_otp(email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = email
        msg['Subject'] = "Your OTP Verification Code"
        msg.attach(MIMEText(f"Your OTP code is: {otp}", 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"ไม่สามารถส่งอีเมล OTP ได้: {e}")
        return False

# === TEXT TO SPEECH ===
def text_to_speech(text, lang='th', slow=False):
    try:
        mp3_fp = BytesIO()
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        b64 = base64.b64encode(mp3_fp.read()).decode()
        unique_id = uuid.uuid4()
        return f'<audio controls key="{unique_id}"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except:
        return None

# === INIT SESSION ===
if "page" not in st.session_state:
    st.session_state.page = "login"
if "user" not in st.session_state:
    st.session_state.user = ""
if "users" not in st.session_state:
    st.session_state.users = load_users()
if "memory" not in st.session_state:
    st.session_state.memory = load_memory()

# === UI STYLES ===
st.markdown("""
    <style>
    .stTextInput>div>div>input {
        background-color: #f0f0f0;
        color: black;
        border-radius: 8px;
        padding: 8px;
        border: 1px solid #ccc;
    }
    .stButton>button {
        background-color: #0066cc;
        color: white;
        border-radius: 6px;
        padding: 8px 16px;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# === LOGIN ===
def login_page():
    st.title("🔐 เข้าสู่ระบบ")
    username = st.text_input("ชื่อผู้ใช้")
    password = st.text_input("รหัสผ่าน", type="password")
    if st.button("เข้าสู่ระบบ"):
        if username in st.session_state.users:
            if st.session_state.users[username]["password"] == hash_password(password):
                st.session_state.user = username
                st.session_state.page = "main"
            else:
                st.error("รหัสผ่านไม่ถูกต้อง")
        else:
            st.error("ไม่มีชื่อผู้ใช้นี้")
    if st.button("สมัครสมาชิก"):
        st.session_state.page = "register"

# === REGISTER ===
def register_page():
    st.title("📝 สมัครสมาชิก")
    new_user = st.text_input("ชื่อผู้ใช้ใหม่")
    new_email = st.text_input("อีเมล (@gmail หรือ @email)")
    new_pass = st.text_input("รหัสผ่าน", type="password")
    confirm_pass = st.text_input("ยืนยันรหัสผ่าน", type="password")

    if st.button("ส่ง OTP"):
        if "@gmail" in new_email or "@email" in new_email:
            if new_pass == confirm_pass and new_user:
                otp = str(random.randint(100000, 999999))
                OTP_STORE[new_email] = {"otp": otp, "user": new_user, "pass": hash_password(new_pass)}
                if send_otp(new_email, otp):
                    st.success("ส่ง OTP แล้ว กรุณาตรวจสอบอีเมลของคุณ")
            else:
                st.error("ข้อมูลไม่ถูกต้องหรือรหัสผ่านไม่ตรงกัน")
        else:
            st.error("อีเมลต้องลงท้ายด้วย @gmail หรือ @email")

    otp_input = st.text_input("กรอกรหัส OTP")
    if st.button("ยืนยัน OTP"):
        for email, data in OTP_STORE.items():
            if data["otp"] == otp_input:
                st.session_state.users[data["user"]] = {"password": data["pass"]}
                save_users(st.session_state.users)
                st.success("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ")
                st.session_state.page = "login"
                return
        st.error("OTP ไม่ถูกต้อง")

# === LOGOUT ===
def logout():
    st.session_state.user = ""
    st.session_state.page = "login"

# === DICTIONARY ===
def dictionary_app():
    st.title("📘 พจนานุกรม AI")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        query = st.text_input("🔍 คำที่ค้นหา:").strip().lower()
    with col2:
        language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])
    with col3:
        if st.button("🚪 ออกจากระบบ"):
            logout()

    if query:
        direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
        lang_code = 'th' if direction == "th_to_en" else 'en'

        st.subheader("🔁 Google Translate")
        result = GoogleTranslator(source='th' if direction=="th_to_en" else 'en',
                                  target='en' if direction=="th_to_en" else 'th').translate(query)
        st.write(f"➡️ {result}")

        audio = text_to_speech(query, lang=lang_code)
        if audio:
            st.markdown("🔊 เสียงอ่านคำค้น:")
            st.markdown(audio, unsafe_allow_html=True)

        st.subheader("📚 Wikipedia")
        try:
            summary = wikipedia.summary(query, sentences=2)
            st.info(summary)
        except:
            st.warning("ไม่พบข้อมูลจาก Wikipedia")

        st.subheader("✍️ เพิ่มคำอธิบายของคุณ")
        new_desc = st.text_input("📝 คำอธิบาย")
        if st.button("💾 บันทึก"):
            if query not in st.session_state.memory:
                st.session_state.memory[query] = []
            st.session_state.memory[query].append({"name": st.session_state.user, "desc": new_desc})
            save_memory(st.session_state.memory)
            st.success("✅ บันทึกแล้ว")

        if query in st.session_state.memory:
            st.subheader("📋 คำอธิบายทั้งหมด")
            for i, item in enumerate(st.session_state.memory[query]):
                st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
                if item['name'] == st.session_state.user:
                    if st.button(f"🗑️ ลบ ({i+1})", key=f"del_{i}"):
                        st.session_state.memory[query].pop(i)
                        if not st.session_state.memory[query]:
                            del st.session_state.memory[query]
                        save_memory(st.session_state.memory)
                        st.warning("❌ ลบเรียบร้อยแล้ว")
                        break

    st.markdown("---")
    st.caption("👨‍💻 ผู้จัดทำ: FOxDoryu")
    st.caption("🤖 Powered by ChatGPT + Streamlit")

# === ROUTING ===
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "register":
    register_page()
elif st.session_state.page == "main":
    dictionary_app()
