import streamlit as st
import json
import os
import hashlib
import random
import smtplib
import wikipedia
from deep_translator import GoogleTranslator
from gtts import gTTS
import base64
import uuid
from io import BytesIO
from email.message import EmailMessage

# ===== CONFIG =====
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

# === Email Settings ===
EMAIL_ADDRESS = "guzz9777@gmail.com"       
EMAIL_PASSWORD = "pqgo hjcx dbqm pjsk"          

# ===== MEMORY =====
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# ===== PASSWORD =====
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ===== EMAIL OTP SEND =====
def send_otp_email(to_email, otp):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'รหัส OTP สำหรับยืนยันการสมัครสมาชิก'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg.set_content(f"รหัส OTP ของคุณคือ: {otp}\n\nอย่าเปิดเผยรหัสนี้กับผู้อื่น")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"ไม่สามารถส่งอีเมล OTP ได้: {e}")
        return False

# ===== INIT SESSION STATE =====
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

# Session vars for registration flow
if "reg_stage" not in st.session_state:
    st.session_state.reg_stage = 0    # 0=normal login, 1=register form, 2=otp verification
if "reg_username" not in st.session_state:
    st.session_state.reg_username = ""
if "reg_email" not in st.session_state:
    st.session_state.reg_email = ""
if "reg_password1" not in st.session_state:
    st.session_state.reg_password1 = ""
if "reg_password2" not in st.session_state:
    st.session_state.reg_password2 = ""
if "otp" not in st.session_state:
    st.session_state.otp = ""
if "otp_input" not in st.session_state:
    st.session_state.otp_input = ""

# ===== UI STYLES =====
st.markdown("""
    <style>
    .stTextInput>div>div>input {
        background-color: #f0f0f0;
        color: #111;
        border-radius: 8px;
        padding: 8px;
        border: 1px solid #ccc;
    }
    .stButton>button {
        background-color: #007bff;
        color: white;
        border-radius: 6px;
        padding: 8px 16px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        cursor: pointer;
    }
    .error {
        color: red;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ===== TEXT TO SPEECH =====
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

# ===== REGISTER FORM =====
def register_form():
    st.title("📝 สมัครสมาชิก")
    username = st.text_input("ชื่อผู้ใช้", key="reg_username_input")
    email = st.text_input("อีเมล (ต้องลงท้าย .gmail หรือ .email)", key="reg_email_input")
    password1 = st.text_input("รหัสผ่าน", type="password", key="reg_password1_input")
    password2 = st.text_input("ยืนยันรหัสผ่าน", type="password", key="reg_password2_input")

    if st.button("ส่งรหัส OTP"):
        # Validation
        if not username.strip() or not email.strip() or not password1 or not password2:
            st.error("กรุณากรอกข้อมูลให้ครบทุกช่อง")
            return
        if not (email.endswith(".gmail") or email.endswith(".email") or email.endswith("@gmail.com") or email.endswith("@email.com")):
            st.error("อีเมลต้องลงท้ายด้วย .gmail หรือ .email หรือ @gmail.com หรือ @email.com เท่านั้น")
            return
        if password1 != password2:
            st.error("รหัสผ่านไม่ตรงกัน")
            return
        if username in st.session_state.users:
            st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
            return
        # Save reg data
        st.session_state.reg_username = username.strip()
        st.session_state.reg_email = email.strip()
        st.session_state.reg_password1 = password1
        # Generate OTP
        otp_code = str(random.randint(100000, 999999))
        st.session_state.otp = otp_code
        sent = send_otp_email(st.session_state.reg_email, otp_code)
        if sent:
            st.success(f"ส่งรหัส OTP ไปยังอีเมล {st.session_state.reg_email} แล้ว")
            st.session_state.reg_stage = 2  # ไปหน้า OTP verify

# ===== OTP VERIFY =====
def otp_verify():
    st.title("🔑 ยืนยันรหัส OTP")
    otp_input = st.text_input("กรุณากรอกรหัส OTP ที่ส่งไปยังอีเมลของคุณ", key="otp_input")
    if st.button("ยืนยัน OTP"):
        if otp_input == st.session_state.otp:
            # สร้างบัญชีผู้ใช้
            st.session_state.users[st.session_state.reg_username] = {
                "password": hash_password(st.session_state.reg_password1),
                "email": st.session_state.reg_email
            }
            st.success("สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ")
            # รีเซ็ต stage
            st.session_state.reg_stage = 0
            st.session_state.otp = ""
            st.session_state.reg_username = ""
            st.session_state.reg_email = ""
            st.session_state.reg_password1 = ""
            st.experimental_rerun()
        else:
            st.error("รหัส OTP ไม่ถูกต้อง กรุณาลองใหม่")

    if st.button("ส่งรหัส OTP ใหม่"):
        otp_code = str(random.randint(100000, 999999))
        st.session_state.otp = otp_code
        sent = send_otp_email(st.session_state.reg_email, otp_code)
        if sent:
            st.success(f"ส่งรหัส OTP ไปยังอีเมล {st.session_state.reg_email} อีกครั้ง")

# ===== LOGIN PAGE =====
def login_page():
    st.title("🔐 เข้าสู่ระบบ")
    username = st.text_input("ชื่อผู้ใช้", key="login_username")
    password = st.text_input("รหัสผ่าน", type="password", key="login_password")

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("เข้าสู่ระบบ"):
            if username in st.session_state.users and \
               st.session_state.users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.experimental_set_query_params(logged_in="true")
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        if st.button("สมัครสมาชิก"):
            st.session_state.reg_stage = 1
            st.experimental_rerun()
    with col3:
        st.write("")

# ===== LOGOUT =====
def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.new_desc = ""
    st.experimental_set_query_params(logged_in="false")
    st.experimental_rerun()

# ===== MAIN APP =====
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
                        st.experimental_rerun()

    st.markdown("---")
    st.caption("👨‍💻 ผู้จัดทำ: FOxDoryu")
    st.caption("🤖 Powered by ChatGPT + Streamlit")

# ===== RUN =====
if st.session_state.reg_stage == 1:
    register_form()
elif st.session_state.reg_stage == 2:
    otp_verify()
else:
    if st.session_state.logged_in:
        dictionary_app()
    else:
        login_page()
