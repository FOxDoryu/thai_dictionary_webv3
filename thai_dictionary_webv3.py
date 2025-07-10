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

user_name = st.text_input("👤 ชื่อของคุณ:", key="user_name").strip()

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

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = None  # index ของ item ที่แก้ไข

    if "edit_text" not in st.session_state:
        st.session_state.edit_text = ""

    if st.session_state.edit_mode is None:
        # เพิ่มคำอธิบายใหม่
        custom_note = st.text_input("📝 คำอธิบายของคุณ:", key="custom_note")
        if st.button("💾 บันทึกคำอธิบาย"):
            if not query or not user_name or not custom_note.strip():
                st.warning("⚠️ กรุณากรอกคำค้นหา, ชื่อ และคำอธิบายให้ครบ")
            else:
                if query not in memory:
                    memory[query] = []
                memory[query].append({"name": user_name, "desc": custom_note.strip()})
                save_memory(memory)
                st.success("✅ บันทึกคำอธิบายเรียบร้อยแล้ว!")
                st.experimental_rerun()
    else:
        # โหมดแก้ไข
        idx = st.session_state.edit_mode
        item = None
        if query in memory and 0 <= idx < len(memory[query]):
            item = memory[query][idx]

        if item:
            st.text_area("แก้ไขคำอธิบาย:", value=item["desc"], key="edit_text_area")
            if st.button("💾 บันทึกการแก้ไข"):
                new_text = st.session_state.edit_text_area.strip()
                if new_text:
                    memory[query][idx]["desc"] = new_text
                    save_memory(memory)
                    st.success("📝 แก้ไขคำอธิบายเรียบร้อยแล้ว")
                    st.session_state.edit_mode = None
                    st.experimental_rerun()
                else:
                    st.warning("⚠️ คำอธิบายไม่สามารถว่างเปล่าได้")
            if st.button("❌ ยกเลิกการแก้ไข"):
                st.session_state.edit_mode = None
                st.experimental_rerun()

    # แสดงคำอธิบายที่เกี่ยวข้อง (กรองคำที่มีคำค้นใน key)
    if query in memory:
        st.markdown("---")
        st.subheader("📝 คำอธิบายที่เกี่ยวข้อง")

        for i, item in enumerate(memory[query]):
            name = item["name"]
            desc = item["desc"]

            col1, col2, col3 = st.columns([8,1,1])
            with col1:
                st.markdown(f"**{i+1}. {name}:** {desc}")
            with col2:
                # ปุ่มแก้ไข ให้เฉพาะของ user ตัวเอง
                if user_name == name and st.button(f"✏️ แก้ไข {i+1}", key=f"edit_btn_{i}"):
                    st.session_state.edit_mode = i
                    st.experimental_rerun()
            with col3:
                # ปุ่มลบ ให้เฉพาะของ user ตัวเอง
                if user_name == name:
                    if f"del_confirm_{i}" not in st.session_state:
                        st.session_state[f"del_confirm_{i}"] = False

                    if not st.session_state[f"del_confirm_{i}"]:
                        if st.button(f"🗑️ ลบ {i+1}", key=f"del_btn_{i}"):
                            st.session_state[f"del_confirm_{i}"] = True
                            st.experimental_rerun()
                    else:
                        st.warning(f"ยืนยันการลบคำอธิบายที่ {i+1}?")
                        cola, colb = st.columns(2)
                        with cola:
                            if st.button(f"✅ ยืนยัน", key=f"del_yes_{i}"):
                                memory[query].pop(i)
                                if not memory[query]:
                                    del memory[query]
                                save_memory(memory)
                                st.success(f"❌ ลบคำอธิบายที่ {i+1} เรียบร้อยแล้ว")
                                # ล้างสถานะ confirm ลบทั้งหมด
                                keys_to_del = [k for k in st.session_state.keys() if k.startswith("del_confirm_")]
                                for k in keys_to_del:
                                    del st.session_state[k]
                                st.experimental_rerun()
                        with colb:
                            if st.button(f"❌ ยกเลิก", key=f"del_no_{i}"):
                                st.session_state[f"del_confirm_{i}"] = False
                                st.experimental_rerun()


# แสดงคำอธิบายที่มีคำค้นในคีย์ (ทั้งคำที่มีคำค้นเป็นส่วนหนึ่ง เช่น งาน, งานบ้าน)
if query:
    st.markdown("---")
    st.subheader(f"📂 คำอธิบายที่เกี่ยวข้องกับ \"{query}\"")
    related = {k: v for k, v in memory.items() if query in k}
    if related:
        for word, notes in related.items():
            if word == query:
                continue  # ข้ามคำที่แสดงข้างบนไปแล้ว
            st.markdown(f"- **{word}**:")
            for i, note in enumerate(notes, 1):
                st.markdown(f"  {i}. {note['name']}: {note['desc']}")
    else:
        st.info("🔍 ยังไม่มีคำอธิบายที่เกี่ยวข้อง")

# CREDIT
st.markdown("---")
st.caption("👨‍💻 ผู้จัดทำ: [FOxDoryu]")
st.caption("🤖 AI โดย ChatGPT (OpenAI)")
