import streamlit as st
import json
import os
import hashlib
import random
import smtplib
from email.message import EmailMessage
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import base64
import uuid
from io import BytesIO

# === CONFIG ===
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

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

# === PASSWORD HASH ===
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# === SEND EMAIL OTP ===
def send_email_otp(receiver_email, otp_code):
    try:
        sender_email = "guzz9777@gmail.com"  # เปลี่ยนเป็นอีเมลคุณ
        app_password = "pqgo hjcx dbqm pjsk"    # เปลี่ยนเป็นรหัสผ่านแอปของ Gmail (App Password)
        
        msg = EmailMessage()
        msg.set_content(f"รหัส OTP ของคุณคือ: {otp_code}")
        msg['Subject'] = 'รหัส OTP สำหรับยืนยันตัวตน'
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"ส่งอีเมล OTP ไม่สำเร็จ: {e}")
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

# === INIT SESSION STATE ===
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {"password": hash_password("1234")},
    }
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "new_desc" not in st.session_state:
    st.session_state.new_desc = ""

# สำหรับระบบ OTP
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "otp_code" not in st.session_state:
    st.session_state.otp_code = ""
if "otp_verified" not in st.session_state:
    st.session_state.otp_verified = False
if "reg_username" not in st.session_state:
    st.session_state.reg_username = ""
if "reg_password" not in st.session_state:
    st.session_state.reg_password = ""
if "reg_email" not in st.session_state:
    st.session_state.reg_email = ""

# === STYLE ===
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
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #004a99;
    }
    </style>
""", unsafe_allow_html=True)

# === LOGIN PAGE ===
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
                st.success(f"ยินดีต้อนรับ, {username}!")
                # เคลียร์ค่าสมัครสมาชิกหากมีค้าง
                st.session_state.otp_sent = False
                st.session_state.otp_verified = False
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with col2:
        if st.button("สมัครสมาชิก"):
            st.session_state.page = "register"
            st.experimental_rerun()

# === REGISTER PAGE ===
def register_page():
    st.title("📝 สมัครสมาชิก")
    username = st.text_input("ชื่อผู้ใช้", key="reg_username")
    email = st.text_input("อีเมล (ต้องลงท้าย .email หรือ .gmail)", key="reg_email")
    password = st.text_input("รหัสผ่าน", type="password", key="reg_password")
    password2 = st.text_input("ยืนยันรหัสผ่าน", type="password", key="reg_password2")

    # ตรวจสอบ email
    email_valid = email.endswith('.email') or email.endswith('.gmail')

    if not email_valid and email != "":
        st.warning("อีเมลต้องลงท้ายด้วย .email หรือ .gmail เท่านั้น")

    if st.session_state.otp_sent is False:
        if st.button("ส่ง OTP"):
            if not username or not email or not password or not password2:
                st.error("กรุณากรอกข้อมูลให้ครบทุกช่อง")
                return
            if not email_valid:
                st.error("รูปแบบอีเมลไม่ถูกต้อง")
                return
            if username in st.session_state.users:
                st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
                return
            if password != password2:
                st.error("รหัสผ่านทั้งสองช่องไม่ตรงกัน")
                return
            # สร้าง OTP
            otp_code = str(random.randint(100000, 999999))
            st.session_state.otp_code = otp_code
            st.session_state.reg_username = username
            st.session_state.reg_password = password
            st.session_state.reg_email = email
            # ส่ง OTP
            sent = send_email_otp(email, otp_code)
            if sent:
                st.session_state.otp_sent = True
                st.info(f"ส่ง OTP ไปยังอีเมล {email} แล้ว กรุณาตรวจสอบ")
    else:
        otp_input = st.text_input("กรอก OTP ที่ได้รับทางอีเมล")
        if st.button("ยืนยัน OTP"):
            if otp_input == st.session_state.otp_code:
                st.success("ยืนยัน OTP สำเร็จ! สมัครสมาชิกเรียบร้อย")
                # บันทึกผู้ใช้ใหม่
                st.session_state.users[st.session_state.reg_username] = {
                    "password": hash_password(st.session_state.reg_password),
                    "email": st.session_state.reg_email
                }
                # รีเซ็ตตัวแปร
                st.session_state.otp_sent = False
                st.session_state.otp_code = ""
                st.session_state.otp_verified = True
                st.session_state.reg_username = ""
                st.session_state.reg_password = ""
                st.session_state.reg_email = ""
                # ไปหน้า login
                st.session_state.page = "login"
                st.experimental_rerun()
            else:
                st.error("OTP ไม่ถูกต้อง กรุณาลองใหม่")

    if st.button("ย้อนกลับไปหน้าเข้าสู่ระบบ"):
        st.session_state.page = "login"
        st.experimental_rerun()

# === LOGOUT ===
def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.new_desc = ""
    st.experimental_rerun()

# === DICTIONARY APP ===
def dictionary_app():
    st.title("📘 พจนานุกรม AI")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        query = st.text_input("🔍 คำที่ค้นหา:", key="query_input").strip().lower()
    with col2:
        language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"], key="lang_radio")
    with col3:
        if st.button("🚪 ออกจากระบบ"):
            logout()

    if query:
        direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
        lang_code = 'th' if direction == "th_to_en" else 'en'

        st.subheader("🔁 ผลจาก Google Translate")
        result = GoogleTranslator(source='th' if direction=="th_to_en" else 'en',
                                  target='en' if direction=="th_to_en" else 'th').translate(query)
        st.write(f"➡️ {result}")
        reverse = GoogleTranslator(source='en' if direction=="th_to_en" else 'th',
                                   target='th' if direction=="th_to_en" else 'en').translate(result)
        st.write(f"🔄 แปลย้อนกลับ: {reverse}")

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
        st.session_state.new_desc = st.text_input("📝 คำอธิบาย", value=st.session_state.new_desc)

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

    st.markdown("---")
    st.caption("👨‍💻 ผู้จัดทำ: FOxDoryu")
    st.caption("🤖 Powered by ChatGPT + Streamlit")

# === MAIN ===
if "page" not in st.session_state:
    st.session_state.page = "login"

if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "register":
    register_page()
elif st.session_state.logged_in:
    dictionary_app()
else:
    login_page()
