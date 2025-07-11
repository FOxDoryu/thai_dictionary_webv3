import streamlit as st
import json
import os
import hashlib
import smtplib
import random
from email.mime.text import MIMEText
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import base64
import uuid
from io import BytesIO

# === CONFIG ===
WIKI_LANG = 'th'
EMAIL_ADDRESS = "guzz9777@gmail.com"
EMAIL_PASSWORD = "pqgo hjcx dbqm pjsk"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

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

# === PASSWORD ===
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# === SEND OTP ===
def send_otp(email, otp):
    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "Your Thai Dictionary OTP"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"ไม่สามารถส่งอีเมล OTP ได้: {e}")
        return False

# === INIT SESSION ===
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {"password": hash_password("1234"), "email": "admin@email.com"},
    }
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "new_desc" not in st.session_state:
    st.session_state.new_desc = ""
if "otp" not in st.session_state:
    st.session_state.otp = ""
if "temp_user" not in st.session_state:
    st.session_state.temp_user = ""
if "temp_email" not in st.session_state:
    st.session_state.temp_email = ""
if "temp_pwd" not in st.session_state:
    st.session_state.temp_pwd = ""

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

# === LOGIN & REGISTER ===
def login_page():
    st.title("🔐 เข้าสู่ระบบ / สมัครสมาชิก")
    mode = st.radio("เลือกโหมด", ["เข้าสู่ระบบ", "สมัครสมาชิก"])

    if mode == "เข้าสู่ระบบ":
        username = st.text_input("ชื่อผู้ใช้")
        password = st.text_input("รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            if username in st.session_state.users and st.session_state.users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    elif mode == "สมัครสมาชิก":
        username = st.text_input("ชื่อผู้ใช้ใหม่")
        email = st.text_input("อีเมล (@gmail หรือ @email เท่านั้น)")
        password = st.text_input("รหัสผ่าน", type="password")
        confirm = st.text_input("ยืนยันรหัสผ่าน", type="password")
        if st.button("ส่ง OTP ไปยังอีเมล"):
            if not username or not email or not password:
                st.warning("กรุณากรอกข้อมูลให้ครบ")
            elif email.endswith("@gmail.com") or email.endswith("@email.com"):
                if username in st.session_state.users:
                    st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
                elif password != confirm:
                    st.error("รหัสผ่านไม่ตรงกัน")
                else:
                    otp = str(random.randint(100000, 999999))
                    if send_otp(email, otp):
                        st.session_state.otp = otp
                        st.session_state.temp_user = username
                        st.session_state.temp_email = email
                        st.session_state.temp_pwd = hash_password(password)
                        st.success("📨 ส่ง OTP ไปยังอีเมลเรียบร้อยแล้ว")
        if st.session_state.otp:
            code = st.text_input("🔑 ป้อนรหัส OTP")
            if st.button("ยืนยัน OTP"):
                if code == st.session_state.otp:
                    st.session_state.users[st.session_state.temp_user] = {
                        "password": st.session_state.temp_pwd,
                        "email": st.session_state.temp_email
                    }
                    st.success("✅ สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ")
                    st.session_state.otp = ""
                else:
                    st.error("❌ รหัส OTP ไม่ถูกต้อง")

# === LOGOUT ===
def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.new_desc = ""

# === MAIN APP ===
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
                        break

    st.markdown("---")
    st.caption("👨‍💻 ผู้จัดทำ: FOxDoryu")
    st.caption("🤖 Powered by ChatGPT + Streamlit")

# === RUN ===
if st.session_state.logged_in:
    dictionary_app()
else:
    login_page()
