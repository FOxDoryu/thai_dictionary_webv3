import streamlit as st
import json
import os
import hashlib
import re
import base64
import pickle
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS

# ================ CONFIG ================
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# ================ GMAIL API ================
def gmail_authenticate():
    creds = None
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text, 'plain', 'utf-8')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_email(to, subject, body):
    service = gmail_authenticate()
    sender = "youremail@gmail.com"  # เปลี่ยนเป็นอีเมลจริงของคุณ
    message = create_message(sender, to, subject, body)
    send_message = service.users().messages().send(userId="me", body=message).execute()
    print(f"📨 Email sent! ID: {send_message['id']}")

# ================ LOAD / SAVE MEMORY ================
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# ================ SESSION STATE INIT ================
if "users" not in st.session_state:
    st.session_state.users = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "page" not in st.session_state:
    st.session_state.page = "login"
if "do_rerun" not in st.session_state:
    st.session_state.do_rerun = False

# ================ REGISTER PAGE ================
def register_page():
    st.title("📧 สมัครสมาชิก")
    name = st.text_input("ชื่อผู้ใช้", key="reg_name")
    email = st.text_input("อีเมล (ต้องลงท้ายด้วย @email หรือ @gmail)", key="reg_email")
    password = st.text_input("รหัสผ่าน", type="password", key="reg_password")
    confirm = st.text_input("ยืนยันรหัสผ่าน", type="password", key="reg_confirm")

    if st.button("สมัครสมาชิก", key="register_btn"):
        if not name or not email or not password or not confirm:
            st.warning("กรุณากรอกข้อมูลให้ครบ")
        elif not re.match(r".+@(email|gmail)\.com$", email):
            st.warning("กรุณาใช้อีเมลที่ลงท้ายด้วย @email หรือ @gmail")
        elif password != confirm:
            st.error("รหัสผ่านไม่ตรงกัน")
        elif name in st.session_state.users:
            st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
        else:
            hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
            st.session_state.users[name] = {"email": email, "password": hashed_pwd}
            try:
                send_email(email, "ยืนยันการสมัครสมาชิก",
                           f"สวัสดี {name}!\nขอบคุณที่สมัครสมาชิกกับเรา!")
                st.success("✅ สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ")
            except Exception as e:
                st.warning(f"สมัครสมาชิกสำเร็จ แต่ส่งเมลล้มเหลว: {e}")
            st.session_state.page = "login"
            st.session_state.do_rerun = True

    if st.button("กลับไปหน้าล็อกอิน", key="reg_back_login"):
        st.session_state.page = "login"
        st.session_state.do_rerun = True

# ================ LOGIN PAGE ================
def login_page():
    st.title("🔐 เข้าสู่ระบบ")
    username = st.text_input("ชื่อผู้ใช้", key="login_name")
    password = st.text_input("รหัสผ่าน", type="password", key="login_password")

    if st.button("เข้าสู่ระบบ", key="login_btn"):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        if username in st.session_state.users and st.session_state.users[username]["password"] == hashed:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.page = "main"
            st.session_state.do_rerun = True
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    st.write("ยังไม่มีบัญชี? สมัครสมาชิกที่นี่:")
    if st.button("สมัครสมาชิก", key="goto_register"):
        st.session_state.page = "register"
        st.session_state.do_rerun = True

# ================ MAIN APP ================
def main_app():
    user_name = st.session_state.user
    st.title(f"📘 พจนานุกรม AI - ยินดีต้อนรับคุณ {user_name}")

    if st.button("🚪 ออกจากระบบ", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.user = ""
        st.session_state.page = "login"
        st.session_state.do_rerun = True

    query = st.text_input("🔍 คำที่ค้นหา:", key="main_query").strip().lower()
    language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"], key="main_lang")

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
        st.success("✅ บันทึกเรียบร้อย")

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
        if st.button("💾 บันทึก", key="save_desc"):
            if query and user_name and new_desc.strip():
                save_description(query, user_name, new_desc.strip())
                st.session_state.do_rerun = True

        if query in memory:
            st.subheader("📋 คำอธิบายทั้งหมดของคำนี้")
            to_remove = []
            for i, item in enumerate(memory[query]):
                st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
                if item['name'] == user_name:
                    if st.button(f"🗑️ ลบ ({i+1})", key=f"del_{i}"):
                        to_remove.append(i)
            if to_remove:
                for index in sorted(to_remove, reverse=True):
                    memory[query].pop(index)
                if not memory[query]:
                    del memory[query]
                save_memory(memory)
                st.warning("❌ ลบเรียบร้อยแล้ว")
                st.session_state.do_rerun = True

# ================ APP CONTROLLER ================
def app():
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "main":
        if not st.session_state.logged_in:
            st.session_state.page = "login"
            st.session_state.do_rerun = True
        else:
            main_app()
    else:
        st.error("หน้าที่ร้องขอไม่มีอยู่จริง")

    if st.session_state.do_rerun:
        st.session_state.do_rerun = False
        st.experimental_rerun()

if __name__ == "__main__":
    app()
