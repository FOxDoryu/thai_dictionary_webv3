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
            return GoogleTranslator(source='th', target='en').translate(word)
        else:
            return GoogleTranslator(source='en', target='th').translate(word)
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

# ====== STREAMLIT UI ======
st.set_page_config(page_title="พจนานุกรม AI", layout="centered")

st.markdown("""
    <style>
    .main {background-color: #fefefe; color: #202020; font-family: 'Segoe UI', sans-serif;}
    .stButton button {background-color: #008CBA; color: white; border-radius: 8px;}
    .stTextInput>div>div>input {
        background-color: #4a4a4a;
        color: white;
        border-radius: 5px;
        padding: 8px;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📘 พจนานุกรม AI ")

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

    # Wikipedia
    with st.expander("📝 ความหมายจาก Wikipedia"):
        summary = wikipedia_summary(query)
        st.write(summary)
        if summary and summary != "(ไม่พบข้อมูลจาก Wikipedia)":
            speech_wiki = text_to_speech(summary, lang=lang_code)
            if speech_wiki:
                st.markdown("🔊 เสียงอ่านความหมาย:")
                st.markdown(speech_wiki, unsafe_allow_html=True)

    # รูปภาพ
    with st.expander("🖼️ ภาพจาก Google"):
        img_url = google_image(query)
        st.markdown(f"[🔗 ดูภาพบน Google Images]({img_url})")

    st.markdown("---")

    # เพิ่มคำอธิบายแบบใส่ชื่อ
    st.subheader("✍️ เพิ่มคำอธิบายของคุณ")
    user_name = st.text_input("👤 ชื่อของคุณ:")
    custom_note = st.text_input("📝 อธิบายเพิ่มเติม:")
    if st.button("💾 บันทึกคำอธิบาย"):
        if query not in memory:
            memory[query] = []
        if user_name.strip() and custom_note.strip():
            memory[query].append({"name": user_name.strip(), "desc": custom_note.strip()})
            save_memory(memory)
            st.success("✅ บันทึกคำอธิบายเรียบร้อยแล้ว!")
        else:
            st.warning("⚠️ กรุณากรอกชื่อและคำอธิบายให้ครบถ้วน")

    # ลบคำนี้
    if st.button("🧼 เคลียร์คำอธิบายของคำนี้"):
        if query in memory:
            del memory[query]
            save_memory(memory)
            st.warning("🗑️ ลบคำอธิบายของคำนี้แล้ว")
        else:
            st.info("ℹ️ คำนี้ยังไม่มีคำอธิบายในระบบ")

# แสดงคำอธิบายที่เกี่ยวข้อง
if query:
    st.markdown("---")
    st.markdown(f"### 📚 คำอธิบายที่เกี่ยวข้องกับ \"{query}\"")
    related = {k: v for k, v in memory.items() if query in k}
    if related:
        for word, notes in related.items():
            st.markdown(f"- **{word}**:")
            for i, entry in enumerate(notes, 1):
                st.markdown(f"  {i}. {entry['name']}: {entry['desc']}")
    else:
        st.info("🔍 ยังไม่มีคำอธิบายที่เกี่ยวข้องกับคำนี้")

# ====== CREDITS ======
st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 ผู้ช่วย AI: ChatGPT โดย OpenAI")
