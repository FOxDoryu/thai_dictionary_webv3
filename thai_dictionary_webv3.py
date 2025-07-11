import streamlit as st
import json
import os
import hashlib
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import base64
import uuid
from io import BytesIO
import random
import smtplib
from email.mime.text import MIMEText

# === CONFIG ===
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

# Email credentials for sending OTP (แก้เป็นของคุณ)
EMAIL_ADDRESS = "guzz9777@gmail.com"
EMAIL_PASSWORD = "pqgo hjcx dbqm pjsk"  # ใช้ App Password เท่านั้น

# === MEMORY ===
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# === PASSWORD & HASH ===
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# === SEND OTP EMAIL ===
def send_otp_email(receiver_email, otp_code):
    try:
        msg = MIMEText(f"รหัส OTP ของคุณคือ: {otp_code}")
        msg['Subject'] = "รหัส OTP สำหรับยืนยันการสมัครสมาชิก"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = receiver_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"ไม่สามารถส่งอีเมล OTP ได้: {e}")
        return False

# === INIT SESSION STATE ===
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {"password": hash_password("1234"), "email": "admin@example.com"},
    }
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "otp_code" not in st.session_state:
    st.session_state.otp_code = ""
if "reg_info" not in st.session_state:
    st.session_state.reg_info = {}  # เก็บ username, email, password ชั่วคราว
if "new_desc" not in st.session_state:
    st.session_state.new_desc = ""

# === UI CSS ===
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

# === PAGES ===
def login_page():
    st.title("🔐 เข้าสู่ระบบ")
    username = st.text_input("ชื่อผู้ใช้", key="login_username")
    password = st.text_input("รหัสผ่าน", type="password", key="login_password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("เข้าสู่ระบบ"):
            if username in st.session_state.users and \
               st.session_state.users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.session_state.new_desc = ""
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        if st.button("สมัครสมาชิก"):
            st.session_state.page = "register"

def register_page():
    st.title("📝 สมัครสมาชิก")

    if not st.session_state.otp_sent:
        username = st.text_input("ชื่อผู้ใช้", key="reg_username")
        email = st.text_input("อีเมล", key="reg_email")
        password1 = st.text_input("รหัสผ่าน", type="password", key="reg_password1")
        password2 = st.text_input("ยืนยันรหัสผ่าน", type="password", key="reg_password2")

        if st.button("ส่ง OTP เพื่อยืนยันอีเมล"):
            # Validate inputs
            if not username or not email or not password1 or not password2:
                st.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")
                return
            if username in st.session_state.users:
                st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
                return
            if not (email.endswith(".gmail") or email.endswith(".email") or email.endswith("@gmail.com") or email.endswith("@email.com")):
                st.error("อีเมลต้องลงท้ายด้วย .gmail หรือ .email เท่านั้น")
                return
            if password1 != password2:
                st.error("รหัสผ่านไม่ตรงกัน")
                return
            # Save registration info temporarily
            st.session_state.reg_info = {
                "username": username,
                "email": email,
                "password": hash_password(password1),
            }
            # Generate OTP
            otp_code = str(random.randint(100000, 999999))
            st.session_state.otp_code = otp_code
            # ส่ง OTP email
            if send_otp_email(email, otp_code):
                st.success("ส่ง OTP ไปยังอีเมลของคุณแล้ว กรุณากรอกรหัสด้านล่าง")
                st.session_state.otp_sent = True

    else:
        otp_input = st.text_input("กรอกรหัส OTP", key="otp_input")
        if st.button("ยืนยัน OTP"):
            if otp_input == st.session_state.otp_code:
                # บันทึก user ใหม่
                info = st.session_state.reg_info
                st.session_state.users[info["username"]] = {
                    "password": info["password"],
                    "email": info["email"]
                }
                st.success("สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ")
                # รีเซ็ตสถานะ
                st.session_state.otp_sent = False
                st.session_state.otp_code = ""
                st.session_state.reg_info = {}
                st.session_state.page = "login"
            else:
                st.error("รหัส OTP ไม่ถูกต้อง")

        if st.button("ส่ง OTP ใหม่"):
            otp_code = str(random.randint(100000, 999999))
            st.session_state.otp_code = otp_code
            send_otp_email(st.session_state.reg_info["email"], otp_code)
            st.success("ส่ง OTP ใหม่แล้ว")

def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.new_desc = ""
    st.experimental_rerun()

def dictionary_app():
    st.title(f"📘 พจนานุกรม AI (ผู้ใช้: {st.session_state.user})")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        query = st.text_input("🔍 คำที่ค้นหา:", key="dict_query").strip().lower()
    with col2:
        language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"], key="dict_language")
    with col3:
        if st.button("🚪 ออกจากระบบ"):
            logout()

    if query:
        direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
        lang_code = 'th' if direction == "th_to_en" else 'en'

        st.subheader("🔁 ผลจาก Google Translate")
        try:
            result = GoogleTranslator(source='th' if direction=="th_to_en" else 'en',
                                      target='en' if direction=="th_to_en" else 'th').translate(query)
            st.write(f"➡️ {result}")
            reverse = GoogleTranslator(source='en' if direction=="th_to_en" else 'th',
                                       target='th' if direction=="th_to_en" else 'en').translate(result)
            st.write(f"🔄 แปลย้อนกลับ: {reverse}")
        except:
            st.warning("ไม่สามารถแปลได้")

        audio = text_to_speech(query, lang=lang_code)
        if audio:
            st.markdown("🔊 เสียงอ่านคำค้น:")
            st.markdown(audio, unsafe_allow_html=True)

        st.subheader("📚 ความหมายจาก Wikipedia")
        try:
            summary = wikipedia.summary(query, sentences=2)
            st.info(summary)
            audio_summary = text_to_speech(summary, lang=lang_code)
            if audio_summary:
                st.markdown("🔊 เสียงอ่านความหมาย:")
                st.markdown(audio_summary, unsafe_allow_html=True)
        except:
            st.warning("ไม่พบข้อมูลจาก Wikipedia")

        st.subheader("✍️ เพิ่มคำอธิบายของคุณ")
        st.session_state.new_desc = st.text_input("📝 คำอธิบาย", value=st.session_state.new_desc, key="new_desc_input")

        if st.button("💾 บันทึก"):
            if st.session_state.new_desc.strip():
                if query not in memory:
                    memory[query] = []
                memory[query].append({
                    "name": st.session_state.user,
                    "desc": st.session_state.new_desc.strip()
                })
                save_memory(memory)
                st.session_state.new_desc = ""
                st.success("✅ บันทึกแล้ว")

        if query in memory:
            st.subheader("📋 คำอธิบายทั้งหมด")
            for i, item in enumerate(memory[query]):
                st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
                if item["name"] == st.session_state.user:
                    if st.button(f"🗑️ ลบ ({i+1})", key=f"delete_{i}"):
                        memory[query].pop(i)
                        if not memory[query]:
                            del memory[query]
                        save_memory(memory)
                        st.warning("❌ ลบเรียบร้อยแล้ว")
                        st.experimental_rerun()

# === MAIN ===
if "page" not in st.session_state:
    st.session_state.page = "login"

if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "register":
    register_page()
else:
    if st.session_state.logged_in:
        dictionary_app()
    else:
        st.session_state.page = "login"
        login_page()
