import streamlit as st
import json, os, hashlib, smtplib, random, re, base64
import wikipedia
from gtts import gTTS
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator

# ---------------- CONFIG ----------------
MEMORY_FILE = 'thai_dict_memory.json'
EMAIL_SENDER = ' guzz9777@gmail.com'  # เปลี่ยนเป็นอีเมลของคุณ
EMAIL_PASSWORD = 'pqgo hjcx dbqm pjsk'   # ใช้ App Password จาก Gmail
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)

# ---------------- FUNCTION ----------------
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def send_otp_email(to_email, otp):
    msg = MIMEText(f'รหัสยืนยันของคุณคือ: {otp}')
    msg['Subject'] = 'ยืนยันการสมัครสมาชิก - OTP'
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

def translate_word(word, direction="th_to_en"):
    try:
        return GoogleTranslator(
            source='th' if direction == 'th_to_en' else 'en',
            target='en' if direction == 'th_to_en' else 'th'
        ).translate(word)
    except:
        return "(ไม่สามารถแปลได้)"

def wikipedia_summary(word):
    try:
        return wikipedia.summary(word, sentences=2)
    except:
        return "(ไม่พบข้อมูลจาก Wikipedia)"

def google_image(word):
    return f"https://www.google.com/search?tbm=isch&q={word}"

def text_to_speech(text, lang='th', slow=False):
    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.save("temp.mp3")
        with open("temp.mp3", "rb") as f:
            audio_bytes = f.read()
        b64 = base64.b64encode(audio_bytes).decode()
        return f'<audio controls><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except:
        return None

def save_description(query, user, desc):
    if query not in memory:
        memory[query] = []
    memory[query].append({"name": user, "desc": desc})
    save_memory(memory)

# ---------------- SESSION ----------------
memory = load_memory()

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

# ---------------- REGISTER PAGE ----------------
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
            elif not re.match(r".+@(gmail|email)\\.com$", email):
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

# ---------------- LOGIN PAGE ----------------
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
                st.rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        st.write("ยังไม่มีบัญชี?")
        if st.button("สมัครสมาชิก"):
            register_page()
    st.stop()

# ---------------- MAIN APP ----------------
user_name = st.session_state.user
st.title("📘 พจนานุกรม AI")
st.write(f"👋 สวัสดี, **{user_name}**")

if st.button("🚪 ออกจากระบบ"):
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.rerun()

query = st.text_input("🔍 คำที่ค้นหา:", "").strip().lower()
language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])

if query:
    direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
    lang_code = 'th' if direction == "th_to_en" else 'en'

    with st.expander("🔁 แปลจาก Google Translate"):
        result = translate_word(query, direction=direction)
        st.write(f"**{query}** ➡️ **{result}**")
        reverse = translate_word(result, direction='en_to_th' if direction == 'th_to_en' else 'th_to_en')
        st.write(f"🔄 แปลย้อนกลับ: **{result}** ➡️ **{reverse}**")
        st.markdown("🔊 เสียงอ่าน:")
        audio = text_to_speech(query, lang=lang_code)
        if audio:
            st.markdown(audio, unsafe_allow_html=True)

    with st.expander("📚 ความหมายจาก Wikipedia"):
        summary = wikipedia_summary(query)
        st.write(summary)
        audio_summary = text_to_speech(summary, lang=lang_code)
        if audio_summary:
            st.markdown("🔊 เสียงอ่านความหมาย:")
            st.markdown(audio_summary, unsafe_allow_html=True)

    with st.expander("🖼️ ภาพจาก Google"):
        st.markdown(f"[🔗 ดูภาพ]({google_image(query)})")

    st.subheader("✍️ เพิ่มคำอธิบายของคุณ")
    new_desc = st.text_input("📝 คำอธิบาย", key="new_desc")
    if st.button("💾 บันทึก"):
        if query and user_name and new_desc.strip():
            save_description(query, user_name, new_desc.strip())
            st.rerun()

    if query in memory:
        st.subheader("📋 คำอธิบายทั้งหมดของคำนี้")
        for i, item in enumerate(memory[query]):
            st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
            if item['name'] == user_name:
                if st.button(f"🗑️ ลบ ({i+1})", key=f"del_{i}"):
                    memory[query].pop(i)
                    if not memory[query]:
                        del memory[query]
                    save_memory(memory)
                    st.warning("❌ ลบเรียบร้อยแล้ว")
                    st.rerun()

st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 AI โดย ChatGPT (OpenAI)")
