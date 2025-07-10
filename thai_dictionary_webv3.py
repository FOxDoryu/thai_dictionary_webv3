import streamlit as st
import json
import os
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import base64

# ====== CONFIG ======
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
USER_FILE = 'users.json'
MEMORY_FILE = 'thai_dict_memory.json'

# ====== LOAD/SAVE ======
def load_json_file(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_json_file(USER_FILE)
memory = load_json_file(MEMORY_FILE)

# ====== FUNCTIONS ======
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

# ====== LOGIN SYSTEM ======
def login():
    st.title("🔐 เข้าสู่ระบบ / สมัครสมาชิก")
    with st.form("login_form"):
        username = st.text_input("👤 ชื่อผู้ใช้")
        password = st.text_input("🔑 รหัสผ่าน", type="password")
        action = st.radio("เลือกดำเนินการ", ["เข้าสู่ระบบ", "สมัครสมาชิก"])
        submitted = st.form_submit_button("ดำเนินการ")

        if submitted:
            if not username or not password:
                st.error("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
                return None

            if action == "สมัครสมาชิก":
                if username in users:
                    st.error("ชื่อผู้ใช้นี้ถูกใช้ไปแล้ว")
                else:
                    users[username] = password
                    save_json_file(USER_FILE, users)
                    st.success("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบใหม่อีกครั้ง")
            elif action == "เข้าสู่ระบบ":
                if username in users and users[username] == password:
                    st.session_state.user = username
                    st.success("เข้าสู่ระบบสำเร็จ")
                    st.experimental_rerun()
                else:
                    st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    return None

# ====== MAIN APP ======
def main():
    st.set_page_config(page_title="พจนานุกรม AI", layout="centered")

    # Logout
    if "user" in st.session_state:
        col1, col2 = st.columns([3,1])
        with col2:
            if st.button("🚪 ออกจากระบบ"):
                del st.session_state.user
                st.experimental_rerun()

    st.title("📘  พจนานุกรม AI ")
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
            audio = text_to_speech(query, lang=lang_code)
            if audio:
                st.markdown("🔊 เสียงอ่าน:")
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
        new_desc = st.text_input("📝 คำอธิบาย:", key="desc")
        if st.button("💾 บันทึก"):
            if query and new_desc:
                if query not in memory:
                    memory[query] = []
                memory[query].append({"name": st.session_state.user, "desc": new_desc})
                save_json_file(MEMORY_FILE, memory)
                st.success("✅ บันทึกเรียบร้อย")
                st.experimental_rerun()

        if query in memory:
            st.markdown("---")
            st.subheader("📋 คำอธิบายทั้งหมดของคำนี้")
            for i, item in enumerate(memory[query]):
                st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
                if item['name'] == st.session_state.user:
                    if st.button(f"🗑️ ลบ {i+1}", key=f"del_{i}"):
                        memory[query].pop(i)
                        if not memory[query]:
                            del memory[query]
                        save_json_file(MEMORY_FILE, memory)
                        st.warning("❌ ลบเรียบร้อยแล้ว")
                        st.experimental_rerun()

        # แสดงคำอื่นที่เกี่ยวข้อง
        st.markdown("---")
        st.subheader(f"📂 คำอื่นๆ ที่มี \"{query}\" ในคำ")
        related = {k: v for k, v in memory.items() if query in k.lower() and k.lower() != query}
        for word, notes in related.items():
            st.markdown(f"- **{word}**")
            for j, note in enumerate(notes, 1):
                st.markdown(f"  {j}. {note['name']}: {note['desc']}")

    # CREDIT
    st.markdown("---")
    st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
    st.caption("🤖 AI โดย ChatGPT (OpenAI)")

# ====== RUN APP ======
if "user" not in st.session_state:
    login()
else:
    main()