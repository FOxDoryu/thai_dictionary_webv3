import streamlit as st
import json
import os
import hashlib
import smtplib
import random
import wikipedia
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator
from gtts import gTTS
import base64
import uuid
from io import BytesIO

# === CONFIG ===
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

# === EMAIL CONFIG ===
EMAIL_ADDRESS = "guzz9777@gmail.com"       # กรอก Gmail ของคุณที่ตั้งค่า App Password ไว้แล้ว
EMAIL_PASSWORD = "pqgo hjcx dbqm pjsk"         # รหัสผ่านแบบ App Password จาก Gmail

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

# === SEND OTP EMAIL ===
def send_otp_email(to_email, otp_code):
    subject = "รหัส OTP สำหรับยืนยันการสมัครสมาชิก"
    body = f"รหัส OTP ของคุณคือ: {otp_code}\nกรุณาอย่าเปิดเผยรหัสนี้กับผู้อื่น"
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"ไม่สามารถส่งอีเมล OTP ได้: {e}")
        return False

# === INIT SESSION ===
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
if "page" not in st.session_state:
    st.session_state.page = "login"
if "otp_code" not in st.session_state:
    st.session_state.otp_code = ""
if "register_data" not in st.session_state:
    st.session_state.register_data = {}

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
                st.session_state.page = "dictionary"
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        if st.button("สมัครสมาชิก"):
            st.session_state.page = "register"
            st.experimental_rerun()

def register_page():
    st.title("📝 สมัครสมาชิก")

    if "step" not in st.session_state:
        st.session_state.step = 1

    if st.session_state.step == 1:
        username = st.text_input("ชื่อผู้ใช้", key="reg_username")
        email = st.text_input("อีเมล (ต้องลงท้าย .gmail หรือ .email)", key="reg_email")
        password = st.text_input("รหัสผ่าน", type="password", key="reg_password")
        password_confirm = st.text_input("ยืนยันรหัสผ่าน", type="password", key="reg_password_confirm")

        if st.button("ส่งรหัส OTP"):
            if not username or not email or not password or not password_confirm:
                st.error("กรุณากรอกข้อมูลให้ครบทุกช่อง")
            elif not (email.endswith("@gmail.com") or email.endswith("@email.com")):
                st.error("อีเมลต้องลงท้ายด้วย @gmail.com หรือ @email.com เท่านั้น")
            elif password != password_confirm:
                st.error("รหัสผ่านไม่ตรงกัน")
            elif username in st.session_state.users:
                st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
            else:
                otp = str(random.randint(100000, 999999))
                st.session_state.otp_code = otp
                st.session_state.register_data = {
                    "username": username,
                    "email": email,
                    "password": hash_password(password)
                }
                sent = send_otp_email(email, otp)
                if sent:
                    st.success("ส่งรหัส OTP ไปยังอีเมลของคุณแล้ว กรุณากรอกรหัสด้านล่าง")
                    st.session_state.step = 2
                    st.experimental_rerun()

    elif st.session_state.step == 2:
        otp_input = st.text_input("กรอกรหัส OTP ที่ได้รับทางอีเมล", key="otp_input")
        if st.button("ยืนยัน OTP"):
            if otp_input == st.session_state.otp_code:
                # บันทึกผู้ใช้ใหม่
                data = st.session_state.register_data
                st.session_state.users[data["username"]] = {"password": data["password"], "email": data["email"]}
                st.success("สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ")
                # รีเซ็ตสถานะ
                st.session_state.step = 1
                st.session_state.page = "login"
                st.experimental_rerun()
            else:
                st.error("รหัส OTP ไม่ถูกต้อง")

def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.new_desc = ""
    st.session_state.page = "login"
    st.experimental_rerun()

def dictionary_app():
    st.title("📘 พจนานุกรม AI")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        query = st.text_input("🔍 คำที่ค้นหา:", key="query_input")
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
                st.experimental_rerun()

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

# === RUN APP ===
if st.session_state.logged_in and st.session_state.page == "dictionary":
    dictionary_app()
elif st.session_state.page == "register":
    register_page()
else:
    login_page()
