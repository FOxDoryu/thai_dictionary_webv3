import streamlit as st
import json
import os
import hashlib
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit_authenticator as stauth
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import base64
import uuid
from io import BytesIO
from serpapi import GoogleSearch  # เพิ่มตรงนี้

# === Config ===
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'
USER_FILE = 'users.json'
SERPAPI_API_KEY = "ใส่_API_KEY_ของคุณที่นี่"  # <-- ใส่ API key ของคุณ

# Load or create user data file
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_users():
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

users = load_users()

# Password hashing
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# Email sending function (ต้องตั้งค่าตรงนี้ให้ถูกต้อง)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "your_email@gmail.com"  # ใส่อีเมลจริงที่ใช้ส่ง OTP
SMTP_PASSWORD = "your_app_password"  # ใช้ App Password ของ Gmail (2FA)

def send_otp(email, otp_code):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = email
        msg['Subject'] = "รหัส OTP สำหรับสมัครสมาชิก"

        body = f"รหัส OTP ของคุณคือ: {otp_code}\n\nกรุณาอย่าเปิดเผยรหัสนี้แก่ผู้อื่น"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_EMAIL, email, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"ส่ง OTP ไม่สำเร็จ: {e}")
        return False

# OTP storage ใน session state
if 'otp_code' not in st.session_state:
    st.session_state.otp_code = ""
if 'otp_email' not in st.session_state:
    st.session_state.otp_email = ""
if 'otp_verified' not in st.session_state:
    st.session_state.otp_verified = False
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False

# Text to speech
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

# Load dictionary memory
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# --- UI styles ---
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

# --- User Authentication (streamlit_authenticator) ---
def get_authenticator():
    user_dict = {}
    for u, info in users.items():
        user_dict[u] = {
            "name": u,
            "password": info['password']
        }
    return stauth.Authenticate(
        user_dict,
        "cookie_name",
        "signature_key",
        cookie_expiry_days=30
    )

authenticator = get_authenticator()

# ฟังก์ชันดึงรูปภาพจาก SerpAPI
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
            return results["images_results"][0]["original"]
        return None
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงรูปภาพ: {e}")
        return None

# --- Pages ---
def login_page():
    st.title("🔐 เข้าสู่ระบบ")

    name, auth_status, username = authenticator.login('เข้าสู่ระบบ', 'main')

    if auth_status:
        st.success(f"ยินดีต้อนรับ {name}")
        st.experimental_set_query_params(logged_in="true")
    elif auth_status is False:
        st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    else:
        st.info("กรุณาเข้าสู่ระบบ")

    if st.button("สมัครสมาชิก"):
        st.session_state['page'] = "register"
        st.experimental_rerun()

def register_page():
    st.title("สมัครสมาชิก")

    new_user = st.text_input("ชื่อผู้ใช้ (ภาษาอังกฤษหรือตัวเลขเท่านั้น)")
    new_email = st.text_input("อีเมล (ต้องลงท้าย .email หรือ .gmail เท่านั้น)")
    new_password = st.text_input("รหัสผ่าน", type="password")
    confirm_password = st.text_input("ยืนยันรหัสผ่าน", type="password")

    if new_email and (not new_email.endswith('.email') and not new_email.endswith('.gmail')):
        st.error("อีเมลต้องลงท้ายด้วย .email หรือ .gmail เท่านั้น")

    if st.session_state.get('otp_sent', False):
        otp_input = st.text_input("กรอกรหัส OTP ที่ได้รับทางอีเมล")
        if st.button("ยืนยัน OTP"):
            if otp_input == st.session_state.otp_code:
                st.success("ยืนยัน OTP สำเร็จ! คุณสามารถสมัครสมาชิกได้แล้ว")
                st.session_state.otp_verified = True
            else:
                st.error("OTP ไม่ถูกต้อง")
    else:
        if st.button("ส่ง OTP"):
            if not new_user or not new_email or not new_password or not confirm_password:
                st.error("กรุณากรอกข้อมูลให้ครบถ้วน")
            elif new_password != confirm_password:
                st.error("รหัสผ่านไม่ตรงกัน")
            elif new_user in users:
                st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
            elif not new_email.endswith('.email') and not new_email.endswith('.gmail'):
                st.error("อีเมลต้องลงท้ายด้วย .email หรือ .gmail เท่านั้น")
            else:
                otp_code = str(random.randint(100000, 999999))
                if send_otp(new_email, otp_code):
                    st.session_state.otp_code = otp_code
                    st.session_state.otp_email = new_email
                    st.session_state.otp_sent = True
                    st.success("ส่ง OTP ไปยังอีเมลเรียบร้อย กรุณาตรวจสอบ")

    if st.session_state.get('otp_verified', False):
        if st.button("สมัครสมาชิกสำเร็จ"):
            users[new_user] = {"password": hash_password(new_password)}
            save_users(users)
            st.success("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ")
            # รีเซ็ตสถานะ OTP
            st.session_state.otp_code = ""
            st.session_state.otp_email = ""
            st.session_state.otp_sent = False
            st.session_state.otp_verified = False
            st.session_state['page'] = "login"
            st.experimental_rerun()

    if st.button("กลับไปหน้าเข้าสู่ระบบ"):
        st.session_state['page'] = "login"
        st.experimental_rerun()

def dictionary_app(name):
    st.title("📘 พจนานุกรม AI")

    authenticator.logout('ออกจากระบบ', 'main')

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        query = st.text_input("🔍 คำที่ค้นหา:").strip().lower()
    with col2:
        language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])
    with col3:
        if st.button("🚪 ออกจากระบบ"):
            authenticator.logout('ออกจากระบบ', 'main')
            st.session_state['page'] = "login"
            st.experimental_rerun()

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

        # แสดงรูปภาพที่เกี่ยวข้อง
        image_url = get_image_url(query)
        if image_url:
            st.subheader("🖼️ รูปภาพที่เกี่ยวข้อง")
            st.image(image_url, use_column_width=True)

        st.subheader("✍️ เพิ่มคำอธิบายของคุณ")
        if 'new_desc' not in st.session_state:
            st.session_state.new_desc = ""

        st.session_state.new_desc = st.text_input("📝 คำอธิบาย", value=st.session_state.new_desc)

        if st.button("💾 บันทึก"):
            if st.session_state.new_desc.strip():
                if query not in memory:
                    memory[query] = []
                memory[query].append({
                    "name": name,
                    "desc": st.session_state.new_desc.strip()
                })
                save_memory(memory)
                st.session_state.new_desc = ""
                st.success("✅ บันทึกแล้ว")

        if query in memory:
            st.subheader("📋 คำอธิบายทั้งหมด")
            for i, item in enumerate(memory[query]):
                st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
                if item["name"] == name:
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

# === Main app flow ===
if 'page' not in st.session_state:
    st.session_state['page'] = "login"

if st.session_state['page'] == "login":
    login_page()
elif st.session_state['page'] == "register":
    register_page()
elif st.session_state['page'] == "app":
    # ต้องล็อกอินก่อนถึงเข้ามาหน้านี้ได้
    name, auth_status, username = authenticator.login('เข้าสู่ระบบ', 'main')
    if auth_status:
        dictionary_app(name)
    elif auth_status is False:
        st.error('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    else:
        st.info('กรุณาเข้าสู่ระบบ')
else:
    st.session_state['page'] = "login"
    st.experimental_rerun()
