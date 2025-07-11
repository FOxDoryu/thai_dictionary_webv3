import streamlit as st
import json
import os
import hashlib
import random
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

# === PASSWORD HASHING ===
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# === EMAIL VALIDATION ===
def valid_email(email):
    # แค่ตรวจว่า email ลงท้าย .gmail หรือ .email (ปรับได้ตามต้องการ)
    pattern = r'^[\w\.-]+@([\w\-]+\.)+(gmail|email)$'
    return re.match(pattern, email)

# === OTP GENERATION ===
def generate_otp():
    return str(random.randint(100000, 999999))

# === SEND OTP EMAIL ===
def send_otp_email(receiver_email, otp_code):
    # กรอกข้อมูลอีเมลผู้ส่งและรหัสผ่าน Gmail ที่ใช้ส่ง (แนะนำใช้ App Password)
    sender_email = "your_email@gmail.com"
    sender_password = "your_app_password"

    try:
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "OTP ยืนยันตัวตนสำหรับพจนานุกรม AI"

        body = f"รหัส OTP ของคุณคือ: {otp_code}\n\nกรุณาอย่าเปิดเผยรหัสนี้กับใคร"
        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        st.error(f"ไม่สามารถส่งอีเมล OTP ได้: {e}")
        return False

# === UI STYLE ===
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
        font-weight: bold;
    }
    .stRadio>div {
        flex-direction: row;
        gap: 10px;
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

# === INIT SESSION STATE ===
if "users" not in st.session_state:
    # user structure: { "password": hashed_pwd, "email": email }
    st.session_state.users = {
        "admin": {"password": hash_password("1234"), "email": "admin@gmail.com"},
    }
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "new_desc" not in st.session_state:
    st.session_state.new_desc = ""
if "otp" not in st.session_state:
    st.session_state.otp = ""
if "otp_verified" not in st.session_state:
    st.session_state.otp_verified = False
if "register_info" not in st.session_state:
    st.session_state.register_info = {}

# === PAGES ===

def login_page():
    st.title("🔐 เข้าสู่ระบบ")

    username = st.text_input("ชื่อผู้ใช้", key="login_username")
    password = st.text_input("รหัสผ่าน", type="password", key="login_password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("เข้าสู่ระบบ"):
            if username in st.session_state.users:
                stored_pwd = st.session_state.users[username]["password"]
                if stored_pwd == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.user = username
                    st.session_state.otp_verified = False
                    st.experimental_set_query_params(logged_in="true")
                    st.experimental_rerun()
                else:
                    st.error("รหัสผ่านไม่ถูกต้อง")
            else:
                st.error("ไม่พบชื่อผู้ใช้")

    with col2:
        if st.button("สมัครสมาชิก"):
            st.session_state.register_info = {}  # เคลียร์ข้อมูลเก่า
            st.session_state.otp_verified = False
            st.experimental_set_query_params(page="register")
            st.experimental_rerun()

def register_page():
    st.title("📝 สมัครสมาชิก")

    # กรอกข้อมูลพื้นฐาน
    username = st.text_input("ชื่อผู้ใช้", value=st.session_state.register_info.get("username", ""), key="reg_username")
    email = st.text_input("อีเมล (ต้องลงท้าย .gmail หรือ .email)", value=st.session_state.register_info.get("email", ""), key="reg_email")
    password = st.text_input("รหัสผ่าน", type="password", key="reg_password")
    password_confirm = st.text_input("ยืนยันรหัสผ่าน", type="password", key="reg_password_confirm")

    # เก็บข้อมูลชั่วคราว
    st.session_state.register_info["username"] = username
    st.session_state.register_info["email"] = email
    st.session_state.register_info["password"] = password
    st.session_state.register_info["password_confirm"] = password_confirm

    # ปุ่มส่ง OTP
    if st.button("ส่งรหัส OTP เพื่อยืนยันอีเมล"):
        if not username or not email or not password or not password_confirm:
            st.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")
        elif username in st.session_state.users:
            st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
        elif not valid_email(email):
            st.error("รูปแบบอีเมลไม่ถูกต้อง")
        elif password != password_confirm:
            st.error("รหัสผ่านและยืนยันรหัสผ่านไม่ตรงกัน")
        else:
            otp = generate_otp()
            st.session_state.otp = otp
            if send_otp_email(email, otp):
                st.success(f"ส่ง OTP ไปยัง {email} แล้ว กรุณาตรวจสอบอีเมล")
            else:
                st.error("ไม่สามารถส่ง OTP ได้ โปรดลองอีกครั้ง")

    # กรอก OTP
    input_otp = st.text_input("กรุณาใส่รหัส OTP ที่ได้รับทางอีเมล", key="input_otp")

    if st.button("ยืนยัน OTP"):
        if input_otp == st.session_state.otp and input_otp != "":
            st.success("ยืนยัน OTP สำเร็จ! สมัครสมาชิกเรียบร้อย")
            # บันทึกข้อมูลผู้ใช้
            st.session_state.users[username] = {
                "password": hash_password(password),
                "email": email
            }
            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.otp_verified = True
            st.experimental_set_query_params(logged_in="true")
            st.experimental_set_query_params(page=None)
            st.experimental_rerun()
        else:
            st.error("รหัส OTP ไม่ถูกต้อง")

    if st.button("ย้อนกลับไปหน้าเข้าสู่ระบบ"):
        st.experimental_set_query_params(page=None)
        st.experimental_rerun()

def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.new_desc = ""
    st.session_state.otp = ""
    st.session_state.otp_verified = False
    st.experimental_set_query_params(logged_in="false")
    st.experimental_set_query_params(page=None)
    st.experimental_rerun()

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
                        break  # หยุด loop เพื่อป้องกัน index error

    st.markdown("---")
    st.caption("👨‍💻 ผู้จัดทำ: FOxDoryu")
    st.caption("🤖 Powered by ChatGPT + Streamlit")

# === MAIN ===
def main():
    params = st.experimental_get_query_params()
    page = params.get("page", [None])[0]
    logged_in = st.session_state.logged_in

    if logged_in:
        dictionary_app()
    else:
        if page == "register":
            register_page()
        else:
            login_page()

if __name__ == "__main__":
    main()
