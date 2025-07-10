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

# ====== LOAD/SAVE ======
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

# ====== UI START ======
st.set_page_config(page_title="พจนานุกรม AI", layout="centered")

# 🔁 ตรวจสอบ query param สำหรับ refresh
params = st.experimental_get_query_params()
if params.get("refresh") == ["true"]:
    st.experimental_set_query_params()  # ล้าง
    st.experimental_rerun()

# ====== UI STYLE ======
st.markdown("""
    <style>
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

# ====== INPUT ======
query = st.text_input("🔍 คำที่ค้นหา:", "").strip().lower()
language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])
user_name = st.text_input("👤 ชื่อของคุณ:", key="user_name").strip()

new_desc = st.text_input("📝 คำอธิบาย:", key="new_desc_input")

# ====== SAVE FUNCTION ======
def save_description():
    if query and user_name and new_desc:
        if query not in memory:
            memory[query] = []
        memory[query].append({"name": user_name, "desc": new_desc})
        save_memory(memory)
        st.success("✅ บันทึกเรียบร้อย")
        st.experimental_set_query_params(refresh="true")

# ====== ACTION ======
if st.button("💾 บันทึก"):
    save_description()

# ====== DICTIONARY SECTION ======
if query:
    direction = "th_to_en" if language == "ไทย → อังกฤษ" else "en_to_th"
    lang_code = 'th' if direction == "th_to_en" else 'en'

    with st.expander("🔁 แปลโดย Google Translate"):
        result = translate_word(query, direction)
        st.write(f"**{query}** ➡️ **{result}**")
        reverse = translate_word(result, "en_to_th" if direction == "th_to_en" else "th_to_en")
        st.write(f"🔄 ย้อนกลับ: **{result}** ➡️ **{reverse}**")
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
        st.markdown(f"[🔗 ดูภาพทั้งหมด]({google_image(query)})")

    # ====== SHOW DESCRIPTIONS ======
    if query in memory:
        st.markdown("---")
        st.subheader("📋 คำอธิบายทั้งหมด")
        for i, item in enumerate(memory[query]):
            st.markdown(f"{i+1}. **{item['name']}**: {item['desc']}")
            if item['name'].strip().lower() == user_name.lower():
                if st.button(f"🗑️ ลบอันที่ {i+1}", key=f"delete_{i}"):
                    memory[query].pop(i)
                    if not memory[query]:
                        del memory[query]
                    save_memory(memory)
                    st.warning("❌ ลบเรียบร้อยแล้ว")
                    st.experimental_set_query_params(refresh="true")

    # ====== คำที่คล้ายกัน ======
    st.markdown("---")
    st.subheader(f"📂 คำอื่นที่มีคำว่า “{query}”")
    related = {k: v for k, v in memory.items() if query in k and k != query}
    for k, v in related.items():
        st.markdown(f"- **{k}**")
        for i, item in enumerate(v, 1):
            st.markdown(f"  {i}. {item['name']}: {item['desc']}")

# ====== CREDIT ======
st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 AI โดย ChatGPT (OpenAI)")
