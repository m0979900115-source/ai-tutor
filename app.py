import streamlit as st
from groq import Groq
import edge_tts
import asyncio
import base64
from PIL import Image
import io

# --- Ініціалізація клієнта ---
client = Groq(api_key=st.secrets["GROQ_KEY"])

# --- Функція перетворення голосу в текст (Whisper) ---
def transcribe_audio(audio_bytes):
    try:
        # Створюємо віртуальний файл для Whisper
        audio_file = ("speech.wav", audio_bytes)
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo", # Найшвидша модель для мови
            response_format="text",
            language="uk"
        )
        return transcription
    except Exception as e:
        return f"Помилка розпізнавання: {e}"

# --- Функція аналізу фото ---
def analyze_image(image_bytes):
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Розпізнай текст та завдання на цьому фото. Відповідай українською."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Помилка зору: {e}"

# --- Озвучка відповідей ---
async def _tts(text):
    communicate = edge_tts.Communicate(text, "uk-UA-PolinaNeural")
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

def speak(text):
    audio_bytes = asyncio.run(_tts(text))
    b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)

# --- Основний інтерфейс ---
st.title("🎓 Розумний репетитор 2.0")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Відображення історії
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

st.divider()

with st.container():
    col1, col2 = st.columns(2)
    with col1: img_file = st.camera_input("📸 Фото завдання")
    with col2: audio_file = st.audio_input("🎤 Запитай голосом")
    u_text = st.chat_input("Або напиши тут...")

# --- Обробка запиту ---
if img_file or audio_file or u_text:
    user_final_text = ""
    
    if img_file:
        with st.spinner("Зчитую фото..."):
            img_desc = analyze_image(img_file.getvalue())
            user_final_text += f"\n[ЗАВДАННЯ З ФОТО]: {img_desc}\n"

    if audio_file:
        with st.spinner("Перетворюю голос у текст..."):
            voice_text = transcribe_audio(audio_file.getvalue())
            # ЦЕ ДУБЛЮВАННЯ: ми додаємо розпізнаний текст у запит
            user_final_text += f"\n[ГОЛОСОВЕ ПИТАННЯ]: {voice_text}"
            st.info(f"🎤 Розпізнано: {voice_text}") # Виводимо на екран для контролю

    if u_text:
        user_final_text += f"\n[ПИТАННЯ]: {u_text}"

    if user_final_text:
        st.session_state.messages.append({"role": "user", "content": user_final_text})
        
        with st.chat_message("assistant"):
            with st.spinner("Вчитель готує відповідь..."):
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Ти вчитель. Пояснюй задачі крок за кроком українською."},
                        *st.session_state.messages
                    ]
                )
                ans = resp.choices[0].message.content
                st.write(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                speak(ans)
