import streamlit as st
import json
import os
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import base64
import re

# ------- Config --------
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

# Gmail SMTP config (เปลี่ยนให้เป็นของคุณ)
EMAIL_ADDRESS = "guzz9777@gmail.com"
EMAIL_PASSWORD = "pqgo hjcx dbqm pjsk"

# ------- โหลด / บันทึกความทรงจำ --------
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# ------- ฟังก์ชันแฮชรหัสผ่าน --------
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ------- ส่ง OTP อีเมล --------
def send_otp_email(receiver_email, otp_code):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = receiver_email
        msg['Subject'] = 'รหัสยืนยัน OTP สำหรับพจนานุกรม AI'

        body = f"รหัส OTP ของคุณคือ: {otp_code}\nโปรดอย่าเปิดเผยรหัสนี้กับใคร"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"ไม่สามารถส่งอีเมล OTP ได้: {e}")
        return False

# ------- ระบบผู้ใช้ใน session --------
if "users" not in st.session_state:
    # ตัวอย่างผู้ใช้ admin
    st.session_state.users = {
        "admin": {"password": hash_password("1234"), "email": "admin@email.com"}
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "registering" not in st.session_state:
    st.session_state.registering = False
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "otp_code" not in st.session_state:
    st.session_state.otp_code = ""
if "register_info" not in st.session_state:
    st.session_state.register_info = {}

# ------- ฟังก์ชันแสดงหน้า login --------
def login_page():
    st.title("🔐 เข้าสู่ระบบ")
    username = st.text_input("ชื่อผู้ใช้", key="login_user", placeholder="ใส่ชื่อผู้ใช้", label_visibility="collapsed")
    password = st.text_input("รหัสผ่าน", type="password", key="login_pass", placeholder="ใส่รหัสผ่าน", label_visibility="collapsed")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("เข้าสู่ระบบ"):
            if username in st.session_state.users and st.session_state.users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.session_state.registering = False
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        if st.button("สมัครสมาชิกใหม่"):
            st.session_state.registering = True
            st.experimental_rerun()

# ------- ฟังก์ชันแสดงหน้า register --------
def register_page():
    st.title("📝 สมัครสมาชิกใหม่")

    name = st.text_input("ชื่อผู้ใช้", key="reg_name", placeholder="ชื่อผู้ใช้")
    email = st.text_input("อีเมล (ต้องลงท้าย .gmail.com หรือ .email.com)", key="reg_email", placeholder="example@gmail.com")
    password1 = st.text_input("รหัสผ่าน", type="password", key="reg_pass1", placeholder="รหัสผ่าน")
    password2 = st.text_input("ยืนยันรหัสผ่าน", type="password", key="reg_pass2", placeholder="ยืนยันรหัสผ่าน")

    # ตรวจสอบรูปแบบอีเมลง่ายๆ
    def valid_email(e):
        return bool(re.match(r"[^@]+@(?:gmail\.com|email\.com)$", e.lower()))

    if st.button("ส่งรหัส OTP ยืนยันอีเมล"):
        if not name.strip():
            st.error("กรุณากรอกชื่อผู้ใช้")
        elif not valid_email(email.strip()):
            st.error("กรุณากรอกอีเมลที่ลงท้ายด้วย gmail.com หรือ email.com เท่านั้น")
        elif password1 != password2:
            st.error("รหัสผ่านทั้งสองช่องไม่ตรงกัน")
        elif len(password1) < 4:
            st.error("รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร")
        elif name in st.session_state.users:
            st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว")
        else:
            otp_code = f"{random.randint(100000, 999999)}"
            st.session_state.otp_code = otp_code
            st.session_state.register_info = {"name": name, "email": email, "password": hash_password(password1)}
            success = send_otp_email(email, otp_code)
            if success:
                st.session_state.otp_sent = True
                st.success(f"ส่งรหัส OTP ไปยัง {email} เรียบร้อย กรุณาตรวจสอบและกรอกรหัส OTP ด้านล่าง")

    if st.session_state.otp_sent:
        otp_input = st.text_input("กรอกรหัส OTP ที่ได้รับทางอีเมล", key="otp_input")
        if st.button("ยืนยัน OTP"):
            if otp_input == st.session_state.otp_code:
                # เพิ่มผู้ใช้ใหม่
                info = st.session_state.register_info
                st.session_state.users[info["name"]] = {"password": info["password"], "email": info["email"]}
                st.success("สมัครสมาชิกสำเร็จ! โปรดเข้าสู่ระบบ")
                # รีเซ็ตสถานะ
                st.session_state.otp_sent = False
                st.session_state.registering = False
                st.experimental_rerun()
            else:
                st.error("รหัส OTP ไม่ถูกต้อง")

    if st.button("ย้อนกลับไปหน้าเข้าสู่ระบบ"):
        st.session_state.registering = False
        st.experimental_rerun()

# ------- ฟังก์ชัน logout --------
def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.experimental_rerun()

# ------- ฟังก์ชันแปลคำ, Wikipedia, เสียง --------
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

# ------- ฟังก์ชันบันทึกคำอธิบาย --------
def save_description(query, user, desc):
    if query not in memory:
        memory[query] = []
    memory[query].append({"name": user, "desc": desc})
    save_memory(memory)
    st.success("✅ บันทึกเรียบร้อย")

# ------- หน้าแรกหลัง login --------
def main_app():
    st.title("📘 พจนานุกรม AI")

    st.write(f"👤 ผู้ใช้: **{st.session_state.user}**")
    if st.button("ออกจากระบบ"):
        logout()

    query = st.text_input("🔍 คำที่ค้นหา:", "").strip().lower()
    language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])

    if query:
        direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
        lang_code = 'th' if direction == "th_to_en" else 'en'

        with st.expander("🔁 ผลจาก Google Translate"):
            result = translate_word(query, direction=direction)
            st.write(f"**{query}** ➡️ **{result}**")
            reverse = translate_word(result, direction='en_to_th' if direction == 'th_to_en' else 'th_to_en')
            st.write(f"🔄 แปลย้อนกลับ: **{result}** ➡️ **{reverse}**")
            st.markdown("---")
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

        st.markdown("---")
        st.subheader("✍️ เพิ่มคำอธิบายของคุณ")
        new_desc = st.text_input("📝 คำอธิบาย:", key="new_desc")

        if st.button("💾 บันทึกคำอธิบาย"):
            if query and st.session_state.user and new_desc.strip():
                save_description(query, st.session_state.user, new_desc.strip())
                st.session_state.new_desc = ""  # ล้างช่องคำอธิบาย
                st.experimental_rerun()

        if query in memory:
            st.markdown("---")
            st.subheader("📋 คำอธิบายทั้งหมดของคำนี้")
            for i, item in enumerate(memory[query]):
                st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
                if item['name'] == st.session_state.user:
                    if st.button(f"🗑️ ลบ ({i+1})", key=f"delete_{i}"):
                        memory[query].pop(i)
                        if not memory[query]:
                            del memory[query]
                        save_memory(memory)
                        st.warning("❌ ลบเรียบร้อยแล้ว")
                        st.experimental_rerun()

    if query:
        st.markdown("---")
        st.subheader(f"📂 คำอื่นๆ ที่มี \"{query}\" ในคำ")
        related = {k: v for k, v in memory.items() if query in k.lower() and k.lower() != query}
        for word, notes in related.items():
            st.markdown(f"- **{word}**")
            for j, note in enumerate(notes, 1):
                st.markdown(f"  {j}. {note['name']}: {note['desc']}")

    st.markdown("---")
    st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
    st.caption("🤖 AI โดย ChatGPT (OpenAI)")

# ------- เริ่มต้นแอป --------
def main():
    if st.session_state.logged_in:
        main_app()
    else:
        if st.session_state.registering:
            register_page()
        else:
            login_page()

if __name__ == "__main__":
    main()
