import streamlit as st
import json
import os
import hashlib
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import base64

# CONFIG
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'
USER_DB_FILE = 'user_db.json'

# ====== UTILITIES =======
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

memory = load_json(MEMORY_FILE)
user_db = load_json(USER_DB_FILE)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = ""
if 'page' not in st.session_state:
    st.session_state.page = "login"

# ====== AUTH PAGES =======
def login_page():
    st.title("🔐 เข้าสู่ระบบ")
    username = st.text_input("ชื่อผู้ใช้")
    password = st.text_input("รหัสผ่าน", type="password")

    if st.button("เข้าสู่ระบบ"):
        if username in user_db and user_db[username]['password'] == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.page = "main"
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    if st.button("สมัครสมาชิก"):
        st.session_state.page = "signup"

def signup_page():
    st.title("📝 สมัครสมาชิก")
    new_user = st.text_input("ชื่อผู้ใช้ใหม่")
    email = st.text_input("อีเมล")
    pwd1 = st.text_input("รหัสผ่าน", type="password")
    pwd2 = st.text_input("ยืนยันรหัสผ่าน", type="password")

    if st.button("สร้างบัญชี"):
        if not new_user or not email or not pwd1 or not pwd2:
            st.warning("กรุณากรอกข้อมูลให้ครบ")
        elif new_user in user_db:
            st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
        elif pwd1 != pwd2:
            st.error("รหัสผ่านไม่ตรงกัน")
        else:
            user_db[new_user] = {"email": email, "password": hash_password(pwd1)}
            save_json(USER_DB_FILE, user_db)
            st.success("✅ สมัครสมาชิกเรียบร้อย กรุณาเข้าสู่ระบบ")
            st.session_state.page = "login"

    if st.button("ย้อนกลับ"):
        st.session_state.page = "login"

# ====== MAIN DICTIONARY APP ======
def main_page():
    st.title("📘  พจนานุกรม AI")

    if st.button("🚪 ออกจากระบบ"):
        st.session_state.logged_in = False
        st.session_state.user = ""
        st.session_state.page = "login"
        return

    query = st.text_input("🔍 คำที่ค้นหา:", "").strip().lower()
    language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])
    user_name = st.session_state.user

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

    if query:
        direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
        lang_code = 'th' if direction == "th_to_en" else 'en'

        with st.expander("🔁 ผลจาก Google Translate"):
            result = translate_word(query, direction=direction)
            st.write(f"**{query}** ➡️ **{result}**")
            reverse = translate_word(result, direction='en_to_th' if direction == 'th_to_en' else 'th_to_en')
            st.write(f"🔄 แปลย้อนกลับ: **{result}** ➡️ **{reverse}**")
            audio = text_to_speech(query, lang=lang_code)
            if audio:
                st.markdown(audio, unsafe_allow_html=True)

        with st.expander("📚 ความหมายจาก Wikipedia"):
            summary = wikipedia_summary(query)
            st.write(summary)
            audio_summary = text_to_speech(summary, lang=lang_code)
            if audio_summary:
                st.markdown(audio_summary, unsafe_allow_html=True)

        with st.expander("🖼️ ภาพจาก Google"):
            st.markdown(f"[🔗 ดูภาพ]({google_image(query)})")

        st.markdown("---")
        st.subheader("✍️ เพิ่มคำอธิบายของคุณ")
        new_desc = st.text_input("📝 คำอธิบาย:", key="new_desc")

        if st.button("💾 บันทึก"):
            if query not in memory:
                memory[query] = []
            memory[query].append({"name": user_name, "desc": new_desc})
            save_json(MEMORY_FILE, memory)
            st.success("✅ บันทึกเรียบร้อย")

        if query in memory:
            st.markdown("---")
            st.subheader("📋 คำอธิบายทั้งหมดของคำนี้")
            for i, item in enumerate(memory[query]):
                st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
                if item['name'] == user_name:
                    if st.button(f"🗑️ ลบ ({i+1})", key=f"delete_{i}"):
                        memory[query].pop(i)
                        if not memory[query]:
                            del memory[query]
                        save_json(MEMORY_FILE, memory)
                        st.warning("❌ ลบเรียบร้อยแล้ว")
                        st.experimental_rerun()

    st.markdown("---")
    st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
    st.caption("🤖 AI โดย ChatGPT (OpenAI)")

# ====== ROUTING ======
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "signup":
    signup_page()
elif st.session_state.page == "main":
    main_page()
