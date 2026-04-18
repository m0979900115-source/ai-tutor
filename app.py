import streamlit as st
from groq import Groq
import edge_tts
import asyncio
import base64
from PIL import Image
import io

# --- Инициализация клиента Groq ---
# Убедитесь, что GROQ_KEY добавлен в Settings -> Secrets в Streamlit Cloud
try:
    client = Groq(api_key=st.secrets["GROQ_KEY"])
except Exception:
    st.error("Ошибка: GROQ_KEY не найден в Secrets!")
    st.stop()

# --- Функция преобразования голоса в текст (Whisper) ---
def transcribe_audio(audio_bytes):
    try:
        audio_file = ("speech.wav", audio_bytes)
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo", 
            response_format="text",
            language="ru"  # Распознаем русскую речь
        )
        return transcription
    except Exception as e:
        return f"Ошибка распознавания: {e}"

# --- Функция анализа фото (Vision) ---
def analyze_image(image_bytes):
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview", # Модель со "зрением"
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Распознай текст и задание на этом фото. Отвечай на русском языке."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Ошибка зрения: {e}"

# --- Озвучка ответов (Женский голос) ---
async def _tts(text):
    # Используем приятный женский голос Svetlana
    communicate = edge_tts.Communicate(text, "ru-RU-SvetlanaNeural")
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": 
            data += chunk["data"]
    return data

def speak(text):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_bytes = loop.run_until_complete(_tts(text))
        loop.close()
        
        b64 = base64.b64encode(audio_bytes).decode()
        st.markdown(
            f'<audio autoplay src="data:audio/mp3;base64,{b64}"></audio>', 
            unsafe_allow_html=True
        )
    except:
        pass

# --- Интерфейс приложения ---
st.set_page_config(page_title="Smart Tutor", page_icon="🎓")
st.title("🎓 Ваш репетитор (Groq Edition)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображение истории чата
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

st.divider()

# Панель ввода
with st.container():
    col1, col2 = st.columns(2)
    with col1: 
        img_file = st.camera_input("📸 Сфотографировать задание")
    with col2: 
        audio_file = st.audio_input("🎤 Задать вопрос голосом")
    
    u_text = st.chat_input("Или напишите сообщение здесь...")

# --- Обработка ввода ---
if img_file or audio_file or u_text:
    final_query = ""
    display_user_text = ""

    # 1. Обработка изображения
    if img_file:
        with st.spinner("Считываю информацию с фото..."):
            img_desc = analyze_image(img_file.getvalue())
            final_query += f"\n[ЗАДАНИЕ НА ФОТО]: {img_desc}\n"
            display_user_text += "📷 Отправлено фото задания. "

    # 2. Обработка голоса
    if audio_file:
        with st.spinner("Распознаю ваш голос..."):
            voice_text = transcribe_audio(audio_file.getvalue())
            final_query += f"\n[ГОЛОСОВОЙ ВОПРОС]: {voice_text}"
            display_user_text += f"🎤 Голос: {voice_text}"
            # Синий блок для мгновенного контроля распознанного текста
            st.info(f"🎤 Распознано: {voice_text}")

    # 3. Текстовый ввод
    if u_text:
        final_query += f"\n[ВОПРОС ТЕКСТОМ]: {u_text}"
        display_user_text += u_text

    if final_query:
        # Сохраняем "чистый" текст пользователя в историю
        st.session_state.messages.append({"role": "user", "content": display_user_text})
        
        with st.chat_message("assistant"):
            with st.spinner("Учитель готовит ответ..."):
                try:
                    # Основная модель для рассуждений
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "Ты терпеливый и добрый учитель. Объясняй задачи пошагово, доступным языком. Отвечай всегда на русском языке."},
                            *st.session_state.messages,
                            {"role": "user", "content": final_query}
                        ]
                    )
                    ans = resp.choices[0].message.content
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    
                    # Автоматическая озвучка ответа
                    speak(ans)
                except Exception as e:
                    st.error(f"Произошла ошибка: {e}")
