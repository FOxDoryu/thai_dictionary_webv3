import streamlit as st
import json, os, hashlib, smtplib, random, re
from email.mime.text import MIMEText

# ---------------- CONFIG ----------------
MEMORY_FILE = 'thai_dict_memory.json'
EMAIL_SENDER = 'your_email@gmail.com'  # เปลี่ยนเป็นอีเมลของคุณ
EMAIL_PASSWORD = 'your_app_password'   # เปลี่ยนเป็นรหัสผ่านสำหรับแอป

# ---------------- ฟังก์ชัน ----------------
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def send_otp_email(to_email, otp):
    msg = MIMEText(f'รหัสยืนยันของคุณคือ: {otp}')
    msg['Subject'] = 'รหัสยืนยัน OTP สำหรับสมัครสมาชิก'
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

# ---------------- Session ----------------
if "users" not in st.session_state:
    st.session_state.users = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = ""

if "otp_stage" not in st.session_state:
    st.session_state.otp_stage = False

if "otp_code" not in st.session_state:
    st.session_state.otp_code = ""

if "reg_email" not in st.session_state:
    st.session_state.reg_email = ""

if "reg_name" not in st.session_state:
    st.session_state.reg_name = ""

if "reg_password" not in st.session_state:
    st.session_state.reg_password = ""

# ---------------- Register ----------------
def register_page():
    st.title("📧 สมัครสมาชิก (ยืนยันผ่านอีเมล)")

    if not st.session_state.otp_stage:
        name = st.text_input("ชื่อผู้ใช้")
        email = st.text_input("อีเมล (ต้องลงท้ายด้วย @gmail.com หรือ @email.com)")
        pwd = st.text_input("รหัสผ่าน", type="password")
        confirm = st.text_input("ยืนยันรหัสผ่าน", type="password")

        if st.button("ส่งรหัสยืนยัน"):
            if not name or not email or not pwd or not confirm:
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบ")
            elif not re.match(r".+@(gmail|email)\.com$", email):
                st.warning("⚠️ อีเมลไม่ถูกต้อง")
            elif pwd != confirm:
                st.warning("⚠️ รหัสผ่านไม่ตรงกัน")
            elif name in st.session_state.users:
                st.error("ชื่อผู้ใช้นี้ถูกใช้แล้ว")
            else:
                otp = str(random.randint(100000, 999999))
                try:
                    send_otp_email(email, otp)
                    st.session_state.otp_stage = True
                    st.session_state.otp_code = otp
                    st.session_state.reg_email = email
                    st.session_state.reg_name = name
                    st.session_state.reg_password = hash_password(pwd)
                    st.success("✅ ส่งรหัสยืนยันไปยังอีเมลเรียบร้อยแล้ว")
                except Exception as e:
                    st.error("❌ ไม่สามารถส่งอีเมลได้: " + str(e))
        st.stop()

    else:
        st.info(f"📨 รหัส OTP ถูกส่งไปยัง {st.session_state.reg_email}")
        user_otp = st.text_input("กรุณากรอกรหัส OTP ที่ได้รับ")
        if st.button("ยืนยัน OTP"):
            if user_otp == st.session_state.otp_code:
                st.session_state.users[st.session_state.reg_name] = {
                    "email": st.session_state.reg_email,
                    "password": st.session_state.reg_password
                }
                st.session_state.logged_in = True
                st.session_state.user = st.session_state.reg_name
                st.success("✅ ยืนยันตัวตนสำเร็จ! ล็อกอินแล้ว")
                st.rerun()
            else:
                st.error("❌ รหัส OTP ไม่ถูกต้อง")
        st.stop()

# ---------------- Login ----------------
if not st.session_state.logged_in:
    st.title("🔐 เข้าสู่ระบบ")
    col1, col2 = st.columns(2)

    with col1:
        username = st.text_input("ชื่อผู้ใช้")
        password = st.text_input("รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            hashed = hash_password(password)
            if username in st.session_state.users and st.session_state.users[username]["password"] == hashed:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success("✅ ล็อกอินสำเร็จ")
                st.rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with col2:
        st.write("ยังไม่มีบัญชี?")
        if st.button("สมัครสมาชิก"):
            register_page()

    st.stop()

# ---------------- MAIN APP ----------------
st.title("📘 พจนานุกรม AI")
st.write(f"👋 สวัสดี, **{st.session_state.user}**")

if st.button("🚪 ออกจากระบบ"):
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.experimental_rerun()

# ... (ที่เหลือคือระบบค้นหา/แปล/คำอธิบาย ใช้ของเดิมคุณได้เลย)
