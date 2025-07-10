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
        return GoogleTranslator(source='th' if direction == 'th_to_en' else 'en',
                                target='en' if direction == 'th_to_en' else 'th').translate(word)
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

st.title("📘 พจนานุกรม AI ")

query = st.text_input("🔍 คำที่ค้นหา:", "")
language = st.radio("🌏 ภาษา:", ["ไทย → อังกฤษ", "อังกฤษ → ไทย"])

# ====== ระบบแปล และ Wiki ======
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

# ====== ระบบเพิ่มคำอธิบาย ======
    st.markdown("---")
    st.subheader("✍️ เพิ่มคำอธิบายของคุณ")
    user_name = st.text_input("👤 ชื่อของคุณ:", key="user_name")
    custom_note = st.text_input("📝 คำอธิบายของคุณ:", key="custom_note")

    if st.button("💾 บันทึกคำอธิบาย"):
        if not query or not user_name or not custom_note:
            st.warning("⚠️ กรุณากรอกคำค้นหา, ชื่อ และคำอธิบายให้ครบ")
        else:
            if query not in memory:
                memory[query] = []
            memory[query].append({"name": user_name.strip(), "desc": custom_note.strip()})
            save_memory(memory)
            st.success("✅ บันทึกคำอธิบายเรียบร้อยแล้ว!")

# ====== ระบบลบ / แก้ไขเฉพาะของตัวเอง ======
    if query and user_name and query in memory:
        own_entries = [item for item in memory[query] if item["name"] == user_name.strip()]
        if own_entries:
            st.markdown("---")
            st.subheader("🧹 จัดการคำอธิบายของคุณ")

            for idx, item in enumerate(own_entries):
                col1, col2 = st.columns([5, 4])
                with col1:
                    st.markdown(f"**{idx+1}. {item['desc']}**")
                with col2:
                    if st.button(f"✏️ แก้ไข {idx+1}", key=f"edit_{idx}"):
                        new_text = st.text_input("🔁 ป้อนคำอธิบายใหม่:", value=item["desc"], key=f"edit_text_{idx}")
                        if st.button(f"✅ ยืนยันแก้ {idx+1}", key=f"confirm_edit_{idx}"):
                            memory[query][memory[query].index(item)]["desc"] = new_text.strip()
                            save_memory(memory)
                            st.success("📝 แก้ไขสำเร็จแล้ว")
                            st.experimental_rerun()

                    if st.button(f"🗑️ ลบ {idx+1}", key=f"delete_{idx}"):
                        confirm = st.radio("⚠️ ยืนยันการลบ:", ["ไม่ลบ", "ยืนยันลบ"], key=f"confirm_delete_{idx}")
                        if confirm == "ยืนยันลบ":
                            memory[query].remove(item)
                            if not memory[query]:
                                del memory[query]
                            save_memory(memory)
                            st.warning("❌ ลบคำอธิบายเรียบร้อยแล้ว")
                            st.experimental_rerun()

# ====== แสดงคำอธิบายที่เกี่ยวข้อง ======
if query:
    st.markdown("---")
    st.subheader(f"📂 คำอธิบายที่เกี่ยวข้องกับ \"{query}\"")
    related = {k: v for k, v in memory.items() if query in k}
    if related:
        for word, notes in related.items():
            st.markdown(f"- **{word}**:")
            for i, note in enumerate(notes, 1):
                st.markdown(f"  {i}. {note['name']}: {note['desc']}")
    else:
        st.info("🔍 ยังไม่มีคำอธิบายที่เกี่ยวข้อง")

# ====== CREDIT ======
st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 AI โดย ChatGPT (OpenAI)")