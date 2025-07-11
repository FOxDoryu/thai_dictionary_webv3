import streamlit as st
import json
import os
import hashlib
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
        margin-top: 5px;
        margin-bottom: 5px;
    }
    .stRadio > div {
        flex-direction: row;
        gap: 15px;
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

# === LOGIN SYSTEM ===
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
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    with col2:
        if st.button("สมัครสมาชิก"):
            if username and password:
                if username in st.session_state.users:
                    st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
                else:
                    st.session_state.users[username] = {"password": hash_password(password)}
                    st.success("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบใหม่")
            else:
                st.warning("กรุณากรอกชื่อและรหัสผ่าน")

# === LOGOUT ===
def logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.new_desc = ""
    st.experimental_rerun()

# === LIKE, RATE, REPLY FUNCTIONS ===
def like_description(query, index):
    memory[query][index]['likes'] = memory[query][index].get('likes', 0) + 1
    save_memory(memory)

def rate_description(query, index, rating):
    memory[query][index]['rating_sum'] = memory[query][index].get('rating_sum', 0) + rating
    memory[query][index]['rating_count'] = memory[query][index].get('rating_count', 0) + 1
    save_memory(memory)

def add_reply(query, index, reply_name, reply_text):
    if 'replies' not in memory[query][index]:
        memory[query][index]['replies'] = []
    memory[query][index]['replies'].append({'name': reply_name, 'text': reply_text})
    save_memory(memory)

# === MAIN APP ===
def dictionary_app():
    st.title("📘 พจนานุกรม AI")

    col1, col2, col3 = st.columns([3, 3, 1])
    with col1:
        query = st.text_input("🔍 คำที่ค้นหา:", key="search_query").strip().lower()
    with col2:
        language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"], key="search_language")
    with col3:
        if st.button("🚪 ออกจากระบบ"):
            logout()

    if query:
        direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
        lang_code = 'th' if direction == "th_to_en" else 'en'

        st.subheader("🔁 ผลจาก Google Translate")
        try:
            result = GoogleTranslator(source='th' if direction=="th_to_en" else 'en',
                                    target='en' if direction=="th_to_en" else 'th').translate(query)
        except:
            result = "(ไม่สามารถแปลได้)"
        st.write(f"➡️ {result}")
        try:
            reverse = GoogleTranslator(source='en' if direction=="th_to_en" else 'th',
                                    target='th' if direction=="th_to_en" else 'en').translate(result)
        except:
            reverse = "(ไม่สามารถแปลย้อนกลับได้)"
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
                    "desc": st.session_state.new_desc.strip(),
                    "likes": 0,
                    "rating_sum": 0,
                    "rating_count": 0,
                    "replies": []
                })
                save_memory(memory)
                st.session_state.new_desc = ""
                st.success("✅ บันทึกแล้ว")
                st.experimental_rerun()

        if query in memory:
            st.subheader("📋 คำอธิบายทั้งหมด")
            for i, item in enumerate(memory[query]):
                st.markdown(f"**{i+1}. {item['name']}**: {item['desc']}")
                
                # ไลค์
                st.write(f"👍 {item.get('likes', 0)} ไลค์")
                if st.button(f"กดไลค์ ({i+1})", key=f"like_{i}"):
                    like_description(query, i)
                    st.experimental_rerun()

                # คะแนนเฉลี่ย
                rating_sum = item.get('rating_sum', 0)
                rating_count = item.get('rating_count', 0)
                avg_rating = rating_sum / rating_count if rating_count > 0 else 0
                st.write(f"⭐ คะแนนเฉลี่ย: {avg_rating:.1f} จาก {rating_count} คน")

                rating = st.radio("ให้คะแนน:", [1, 2, 3, 4, 5], key=f"rate_{i}")
                if st.button(f"ส่งคะแนน ({i+1})", key=f"submit_rate_{i}"):
                    rate_description(query, i, rating)
                    st.success("ขอบคุณสำหรับคะแนน!")
                    st.experimental_rerun()

                # ตอบกลับ
                st.markdown("💬 ตอบกลับ:")
                replies = item.get('replies', [])
                for r in replies:
                    st.markdown(f"- **{r['name']}**: {r['text']}")

                reply_text = st.text_input(f"ตอบกลับ ({i+1})", key=f"reply_input_{i}")
                if st.button(f"ส่งตอบกลับ ({i+1})", key=f"submit_reply_{i}"):
                    if reply_text.strip():
                        add_reply(query, i, st.session_state.user, reply_text.strip())
                        st.success("ส่งคำตอบกลับแล้ว!")
                        st.experimental_rerun()

                # ลบคำอธิบายของตัวเอง
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

# === RUN ===
if st.session_state.logged_in:
    dictionary_app()
else:
    login_page()
