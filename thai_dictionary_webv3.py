# thai_dictionary_web.py
import streamlit as st
from deep_translator import GoogleTranslator
import wikipedia
import json
import os
from gtts import gTTS
import base64

# ====== CONFIG ======
WIKI_LANG = 'th'
wikipedia.set_lang(WIKI_LANG)
MEMORY_FILE = 'thai_dict_memory.json'

# ====== INITIAL LOAD ======
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_memory(mem):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# ====== FUNCTIONS ======
def translate_word(word, direction="th_to_en"):
    try:
        if direction == "th_to_en":
            translated = GoogleTranslator(source='th', target='en').translate(word)
        else:
            translated = GoogleTranslator(source='en', target='th').translate(word)
        return translated
    except Exception:
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
        audio_html = f'<audio controls><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
        return audio_html
    except:
        return None

# ====== STREAMLIT UI ======
st.set_page_config(page_title="พจนานุกรม AI", layout="centered")

st.markdown("""
    <style>
    .main {background-color: #fefefe; color: #202020; font-family: 'Segoe UI', sans-serif;}
    .stButton button {background-color: #008CBA; color: white; border-radius: 8px;}
    /* เปลี่ยนสีช่องค้นหาเป็นเทาเข้มและข้อความสีขาว */
    .stTextInput>div>div>input {
        background-color: #4a4a4a;
        color: white;
        border-radius: 5px;
        padding: 8px;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📘  พจนานุกรม AI ")

# ---- INPUT ----
query = st.text_input("🔍 คำที่ค้นหา:", "")
language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])

if query:
    st.markdown("---")
    direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
    lang_code = 'th' if direction == "th_to_en" else 'en'

    # แปลภาษา
    with st.expander("🔁 ผลจาก Google Translate"):
        result = translate_word(query, direction=direction)
        st.write(f"**{query}** ➡️ **{result}**")

        reverse = translate_word(result, direction='en_to_th' if direction == 'th_to_en' else 'th_to_en')
        st.write(f"🔄 แปลย้อนกลับ: **{result}** ➡️ **{reverse}**")

        st.markdown("---")
        st.markdown("🔊 เสียงอ่าน (ปกติ):")
        speech_norm = text_to_speech(query, lang=lang_code)
        if speech_norm:
            st.markdown(speech_norm, unsafe_allow_html=True)

        st.markdown("🔊 เสียงอ่าน (ช้า):")
        speech_slow = text_to_speech(query, lang=lang_code, slow=True)
        if speech_slow:
            st.markdown(speech_slow, unsafe_allow_html=True)

    # ความหมายจาก Wikipedia
    with st.expander("📝 ความหมายจาก Wikipedia"):
        summary = wikipedia_summary(query)
        st.write(summary)
        if summary and summary != "(ไม่พบข้อมูลจาก Wikipedia)":
            speech_wiki = text_to_speech(summary, lang=lang_code)
            if speech_wiki:
                st.markdown("🔊 เสียงอ่านความหมาย:")
                st.markdown(speech_wiki, unsafe_allow_html=True)

    # แสดงภาพจาก Google
    with st.expander("🖼️ ภาพจาก Google"):
        img_url = google_image(query)
        st.markdown(f"[🔗 ดูภาพบน Google Images]({img_url})")

    st.markdown("---")

    # เพิ่มคำอธิบายเอง
    st.subheader("📌 เพิ่มคำอธิบายของคุณ")
    custom_note = st.text_input("ใส่คำอธิบายเพิ่มเติมของคุณ:")
    if st.button("💾 บันทึกคำอธิบาย"):
        memory[query] = custom_note
        save_memory(memory)
        st.success("✅ บันทึกคำอธิบายเรียบร้อยแล้ว!")

    # ลบคำอธิบายเดิม
    if st.button("🧼 เคลียร์ฐานข้อมูลคำนี้"):
        if query in memory:
            del memory[query]
            save_memory(memory)
            st.warning("🗑️ ลบคำอธิบายเรียบร้อยแล้ว")
        else:
            st.info("ℹ️ คำนี้ยังไม่มีคำอธิบายในฐานข้อมูล")

# แสดงคำอธิบายทั้งหมดที่เคยบันทึกไว้
if memory:
    st.markdown("---")
    st.markdown("### 🗂️ คำอธิบายที่เคยเพิ่มไว้")
    for word, note in memory.items():
        st.markdown(f"- **{word}**: {note}")
else:
    st.info("📂 ยังไม่มีคำอธิบายที่ถูกบันทึกไว้")

# ====== CREDITS ======
st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 ผู้ช่วย AI: ChatGPT โดย OpenAI")
