import streamlit as st
from groq import Groq
import edge_tts
import asyncio
import base64
from PIL import Image
import io

# ── Конфігурація ──────────────────────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_KEY"])
except Exception:
    st.error("Додайте GROQ_KEY у Secrets!")
    st.stop()

# ── Озвучка (Edge-TTS) ────────────────────────────────────────
async def _tts(text):
    communicate = edge_tts.Communicate(text, "uk-UA-PolinaNeural")
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

def speak(text):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_bytes = loop.run_until_complete(_tts(text))
        b64 = base64.b64encode(audio_bytes).decode()
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
    except: pass

# ── Функція для аналізу зображення через Groq Vision ──────────
def analyze_image(image_bytes):
    try:
        # Кодуємо зображення в base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Опиши що на фото, особливо якщо там є навчальне завдання або текст. Відповідай українською."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Помилка зору: {e}"

# ── Стан сесії ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

st.set_page_config(page_title="Smart Tutor", page_icon="🎓")
st.title("🎓 Розумний репетитор (Vision + Voice)")

# Відображення чату
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

st.divider()

# ── Панель інструментів ──────────────────────────────────────
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        img_file = st.camera_input("📸 Сфотографуй завдання")
    with col2:
        audio_file = st.audio_input("🎤 Запитай голосом")

    u_text = st.chat_input("Або напиши повідомлення тут...")

# ── Логіка обробки ────────────────────────────────────────────
if img_file or audio_file or u_text:
    final_prompt = ""
    
    # 1. Якщо є фото — спочатку "дивлячись" на нього
    if img_file:
        with st.spinner("Дивлюсь на завдання..."):
            img_description = analyze_image(img_file.getvalue())
            final_prompt += f"\n[Користувач надіслав фото. Опис фото: {img_description}]\n"
            st.image(img_file, caption="Ваше фото", width=300)

    # 2. Якщо є голос або текст
    if u_text:
        final_prompt += u_text
    elif audio_file:
        # Для простоти на Free Tier Groq ми можемо використати текстову модель, 
        # припустивши що користувач просто хоче відповіді на фото або текст.
        final_prompt += "Поясни мені це завдання."

    if final_prompt:
        st.session_state.messages.append({"role": "user", "content": u_text or "Аналіз фото/голосу"})
        
        with st.chat_message("assistant"):
            with st.spinner("Вчитель готує відповідь..."):
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "Ти терплячий репетитор. Допомагай розв'язувати завдання, пояснюй логіку. Відповідай українською."},
                            {"role": "user", "content": final_prompt}
                        ],
                        model="llama-3.3-70b-versatile",
                    )
                    ans = chat_completion.choices[0].message.content
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    speak(ans)
                except Exception as e:
                    st.error(f"Помилка: {e}")
