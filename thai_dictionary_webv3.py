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
from serpapi import GoogleSearch

# === CONFIG ===
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

# SerpAPI API key ใส่ตรงนี้
SERPAPI_API_KEY = "c92fb1a39177153b474a00d3f9eb3c2eed80a55b858ba711c1b2b710f0ed84ef"

# Email Config for OTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "guzz9777@gmail.com"      # อีเมลที่ใช้ส่ง OTP
EMAIL_PASSWORD = "pqgo hjcx dbqm pjsk"      # รหัสผ่านหรือ App Password

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
def send_otp(email, otp_code):
    try:
        msg = MIMEText(f"รหัส OTP ของคุณคือ: {otp_code}")
        msg['Subject'] = 'OTP สำหรับสมัครสมาชิก พจนานุกรม AI'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
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
        "admin": {"password": hash_password("1234"), "email": "admin@example.com"},
    }
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "new_desc" not in st.session_state:
    st.session_state.new_desc = ""
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "otp_code" not in st.session_state:
    st.session_state.otp_code = ""
if "register_info" not in st.session_state:
    st.session_state.register_info = {}

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
        font-weight: bold;
    }
    .logout-button {
        background-color: #cc3300 !important;
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

# === GET IMAGE FROM SERPAPI ===
def get_image_url(query):
    try:
        params = {
            "engine": "google",
            "q": query,
            "tbm": "isch",
            "ijn": "0",
            "api_key": SERPAPI_API_KEY
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        if "images_results" in results and len(results["images_results"]) > 0:
            first_img = results["images_results"][0]
            return first_img["original"]
    except Exception as e:
        st.warning("ไม่สามารถโหลดรูปภาพได้")
    return None

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
                st.session_state.new_desc = ""
                st.success(f"ยินดีต้อนรับ {username}!")
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        if st.button("สมัครสมาชิก"):
            st.session_state.register_info = {}
            st.session_state.otp_sent = False
            st.experimental_rerun()

# === REGISTER PAGE ===
def register_page():
    st.title("📝 สมัครสมาชิก")

    if "step" not in st.session_state:
        st.session_state.step = 1

    if st.session_state.step == 1:
        st.write("กรุณากรอกข้อมูลเพื่อสมัครสมาชิก")

        username = st.text_input("ชื่อผู้ใช้", key="reg_username", value=st.session_state.register_info.get("username", ""))
        email = st.text_input("อีเมล (ต้องลงท้าย .gmail หรือ .email)", key="reg_email", value=st.session_state.register_info.get("email", ""))
        password = st.text_input("รหัสผ่าน", type="password", key="reg_password")
        password_confirm = st.text_input("ยืนยันรหัสผ่าน", type="password", key="reg_password_confirm")

        if st.button("ส่งรหัส OTP"):
            # Validate inputs
            if not username or not email or not password or not password_confirm:
                st.error("กรุณากรอกข้อมูลให้ครบทุกช่อง")
                return
            if not (email.endswith("@gmail.com") or email.endswith("@email.com")):
                st.error("อีเมลต้องลงท้ายด้วย @gmail.com หรือ @email.com เท่านั้น")
                return
            if password != password_confirm:
                st.error("รหัสผ่านไม่ตรงกัน")
                return
            if username in st.session_state.users:
                st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
                return

            # Save info temporarily
            st.session_state.register_info = {
                "username": username,
                "email": email,
                "password": hash_password(password)
            }
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            st.session_state.otp_code = otp

            # Send OTP
            if send_otp(email, otp):
                st.success(f"ส่งรหัส OTP ไปที่ {email} แล้ว")
                st.session_state.step = 2
                st.experimental_rerun()
            else:
                st.error("ส่ง OTP ไม่สำเร็จ")

    elif st.session_state.step == 2:
        st.write(f"กรุณากรอกรหัส OTP ที่ส่งไปยัง {st.session_state.register_info['email']}")

        user_otp = st.text_input("รหัส OTP", key="input_otp")
        if st.button("ยืนยัน OTP"):
            if user_otp == st.session_state.otp_code:
                # สร้างผู้ใช้ใหม่
                user = st.session_state.register_info["username"]
                st.session_state.users[user] = {
                    "password": st.session_state.register_info["password"],
                    "email": st.session_state.register_info["email"]
                }
                st.success("สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ")
                st.session_state.step = 1
                st.session_state.register_info = {}
                st.session_state.otp_code = ""
                st.experimental_rerun()
            else:
                st.error("รหัส OTP ไม่ถูกต้อง")

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
        query = st.text_input("🔍 คำที่ค้นหา:").strip().lower()
    with col2:
        language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])
    with col3:
        if st.button("🚪 ออกจากระบบ", key="logout_btn"):
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
        except Exception as e:
            st.warning("เกิดข้อผิดพลาดในการแปล")

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

        # แสดงรูปภาพ
        image_url = get_image_url(query)
        if image_url:
            st.subheader("🖼️ รูปภาพที่เกี่ยวข้อง")
            st.image(image_url, use_column_width=True)

        st.subheader("✍️ เพิ่มคำอธิบายของคุณ")
        st.session_state.new_desc = st.text_input("📝 คำอธิบาย", value=st.session_state.new_desc, key="desc_input")

        if st.button("💾 บันทึก", key="save_desc"):
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
                        break  # หยุด loop เพื่อป้องกัน index error

    st.markdown("---")
    st.caption("👨‍💻 ผู้จัดทำ: FOxDoryu")
    st.caption("🤖 Powered by ChatGPT + Streamlit")

# === MAIN RUN ===
if st.session_state.logged_in:
    dictionary_app()
elif "register_info" in st.session_state and st.session_state.register_info:
    register_page()
else:
    login_page()
