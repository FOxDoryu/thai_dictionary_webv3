import streamlit as st
import json
import os
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
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
CACHE_FILE = "login_cache.json"
OTP_FILE = "otp_codes.json"

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

# === OTP ===
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(email, otp):
    sender_email = "guzz9777@gmail.com"  # replace
    sender_password = "pqgo hjcx dbqm pjsk"  # replace with App Password

    msg = MIMEText(f"รหัส OTP ของคุณคือ: {otp}")
    msg['Subject'] = 'OTP สำหรับการสมัครสมาชิก'
    msg['From'] = sender_email
    msg['To'] = email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"ไม่สามารถส่งอีเมล OTP ได้: {e}")
        return False

# === LOGIN CACHE ===
def load_login_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

def save_login_cache(username):
    with open(CACHE_FILE, "w") as f:
        json.dump({"user": username}, f)

def clear_login_cache():
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)

# === INIT SESSION ===
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {"password": hash_password("1234"), "email": "admin@email.com"}
    }
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "new_desc" not in st.session_state:
    st.session_state.new_desc = ""
if "awaiting_otp" not in st.session_state:
    st.session_state.awaiting_otp = False
if "otp_email" not in st.session_state:
    st.session_state.otp_email = ""
if "otp_code" not in st.session_state:
    st.session_state.otp_code = ""

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

# === LOGIN PAGE ===
def login_page():
    cached = load_login_cache()
    if cached and cached.get("user") in st.session_state.users:
        st.session_state.logged_in = True
        st.session_state.user = cached["user"]
        return

    st.title("🔐 เข้าสู่ระบบ")
    username = st.text_input("ชื่อผู้ใช้")
    password = st.text_input("รหัสผ่าน", type="password")
    remember = st.checkbox("📌 จดจำฉันไว้")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("เข้าสู่ระบบ"):
            if username in st.session_state.users and \
               st.session_state.users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
                if remember:
                    save_login_cache(username)
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with col2:
        if st.button("สมัครสมาชิก"):
            st.session_state.awaiting_otp = True

    if st.session_state.awaiting_otp:
        st.subheader("📨 สมัครสมาชิกพร้อมยืนยันอีเมล")
        new_user = st.text_input("ชื่อผู้ใช้ใหม่")
        email = st.text_input("อีเมล (ต้องลงท้ายด้วย @email หรือ @gmail)")
        new_pass = st.text_input("รหัสผ่านใหม่", type="password")
        confirm = st.text_input("ยืนยันรหัสผ่าน", type="password")

        if st.button("ขอ OTP"):
            if new_user and new_pass and confirm and email.endswith(("@email", "@gmail")):
                if new_pass != confirm:
                    st.error("รหัสผ่านไม่ตรงกัน")
                elif new_user in st.session_state.users:
                    st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
                else:
                    otp = generate_otp()
                    if send_otp(email, otp):
                        st.session_state.otp_code = otp
                        st.session_state.otp_email = email
                        st.session_state.pending_user = new_user
                        st.session_state.pending_pass = new_pass
                        st.success("📩 ส่งรหัส OTP ไปยังอีเมลแล้ว")
        otp_input = st.text_input("กรอกรหัส OTP")
        if st.button("ยืนยัน OTP"):
            if otp_input == st.session_state.otp_code:
                st.session_state.users[st.session_state.pending_user] = {
                    "password": hash_password(st.session_state.pending_pass),
                    "email": st.session_state.otp_email
                }
                st.success("✅ สมัครสำเร็จ กรุณาเข้าสู่ระบบ")
                st.session_state.awaiting_otp = False
            else:
                st.error("❌ OTP ไม่ถูกต้อง")

# === LOGOUT ===
def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.new_desc = ""
    clear_login_cache()

# === MAIN APP ===
def dictionary_app():
    st.title("📘 พจนานุกรม AI")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        query = st.text_input("🔍 คำที่ค้นหา: ").strip().lower()
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

# === RUN APP ===
if st.session_state.logged_in:
    dictionary_app()
else:
    login_page()
