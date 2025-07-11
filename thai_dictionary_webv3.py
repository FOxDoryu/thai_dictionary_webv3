import streamlit as st
import json
import os
import hashlib
import smtplib
import random
import re
import base64
import uuid
from io import BytesIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS

# CONFIG
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'
EMAIL_ADDRESS = "your_email@gmail.com"  # ใส่อีเมลของคุณ
EMAIL_PASSWORD = "your_app_password"  # ใช้ App Password จาก Gmail

# MEMORY

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# SESSION INIT
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {"password": hashlib.sha256("1234".encode()).hexdigest()}
    }
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "new_desc" not in st.session_state:
    st.session_state.new_desc = ""
if "registering" not in st.session_state:
    st.session_state.registering = False
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "otp_code" not in st.session_state:
    st.session_state.otp_code = ""
if "register_info" not in st.session_state:
    st.session_state.register_info = {}

# UTILS

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def send_otp_email(receiver_email, otp_code):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = receiver_email
        msg["Subject"] = "OTP สำหรับสมัครสมาชิก"
        body = f"รหัส OTP ของคุณคือ: {otp_code}"
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"ไม่สามารถส่งอีเมล OTP ได้: {e}")
        return False

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

# UI STYLES
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

# LOGIN PAGE

def login_page():
    st.title("🔐 เข้าสู่ระบบ")
    username = st.text_input("ชื่อผู้ใช้")
    password = st.text_input("รหัสผ่าน", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("เข้าสู่ระบบ"):
            if username in st.session_state.users and \
               st.session_state.users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        if st.button("สมัครสมาชิก"):
            st.session_state.registering = True
            st.experimental_rerun()

# REGISTER PAGE

def register_page():
    st.title("📝 สมัครสมาชิกใหม่")
    name = st.text_input("ชื่อผู้ใช้")
    email = st.text_input("อีเมล (ลงท้าย .gmail.com หรือ .email.com)")
    password1 = st.text_input("รหัสผ่าน", type="password")
    password2 = st.text_input("ยืนยันรหัสผ่าน", type="password")

    def valid_email(e): return bool(re.match(r"[^@]+@(?:gmail\.com|email\.com)$", e.lower()))

    if st.button("ส่งรหัส OTP"):
        if not name.strip():
            st.error("กรุณากรอกชื่อผู้ใช้")
        elif not valid_email(email):
            st.error("อีเมลต้องลงท้ายด้วย gmail.com หรือ email.com")
        elif password1 != password2:
            st.error("รหัสผ่านไม่ตรงกัน")
        elif name in st.session_state.users:
            st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
        else:
            otp = f"{random.randint(100000, 999999)}"
            st.session_state.otp_code = otp
            st.session_state.register_info = {
                "name": name, "email": email, "password": hash_password(password1)
            }
            if send_otp_email(email, otp):
                st.session_state.otp_sent = True
                st.success("ส่ง OTP ไปยังอีเมลเรียบร้อย")

    if st.session_state.otp_sent:
        user_otp = st.text_input("กรอกรหัส OTP")
        if st.button("ยืนยัน OTP"):
            if user_otp == st.session_state.otp_code:
                info = st.session_state.register_info
                st.session_state.users[info["name"]] = {
                    "password": info["password"], "email": info["email"]
                }
                st.success("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ")
                st.session_state.registering = False
                st.session_state.otp_sent = False
                st.experimental_rerun()
            else:
                st.error("OTP ไม่ถูกต้อง")

    if st.button("🔙 กลับไปหน้าเข้าสู่ระบบ"):
        st.session_state.registering = False
        st.experimental_rerun()

# LOGOUT

def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.new_desc = ""
    st.experimental_rerun()

# MAIN DICTIONARY APP

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
        result = GoogleTranslator(source='th' if direction == "th_to_en" else 'en',
                                  target='en' if direction == "th_to_en" else 'th').translate(query)
        st.write(f"➡️ {result}")
        reverse = GoogleTranslator(source='en' if direction == "th_to_en" else 'th',
                                   target='th' if direction == "th_to_en" else 'en').translate(result)
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
                        break

    st.markdown("---")
    st.caption("👨‍💻 ผู้จัดทำ: FOxDoryu")
    st.caption("🤖 Powered by ChatGPT + Streamlit")

# MAIN RUN
if __name__ == "__main__":
    if st.session_state.logged_in:
        dictionary_app()
    elif st.session_state.registering:
        register_page()
    else:
        login_page()
