import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from PIL import Image
import io
import os

# 1. БЕЗПЕЧНЕ НАЛАШТУВАННЯ
try:
    API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Налаштуйте GEMINI_KEY у Secrets!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

st.set_page_config(page_title="AI Tutor 3.0", page_icon="🎓")
st.title("🎓 Мій персональний репетитор")

SYSTEM_PROMPT = "Ти — крутий репетитор. Допоможи учню зрозуміти завдання. Не давай відповідь одразу, став навідні запитання. Спілкуйся українською."

# 2. ВВІД
img_file = st.camera_input("📸 Фото завдання")
audio_question = st.audio_input("🎤 Запитай голосом")
user_text = st.text_input("💬 Твоє питання")

# 3. ЛОГІКА
if img_file or audio_question or user_text:
    with st.spinner('Думаю...'):
        try:
            content = [SYSTEM_PROMPT]
            if user_text: content.append(user_text)
            if audio_question: content.append({"mime_type": "audio/wav", "data": audio_question.getvalue()})
            if img_file: content.append(Image.open(img_file))
            
            response = model.generate_content(content)
            answer = response.text
            
            st.info(answer)
            
            # --- НОВИЙ СПОСІБ ОЗВУЧКИ (ЧЕРЕЗ ТИМЧАСОВИЙ ФАЙЛ) ---
            try:
                tts = gTTS(text=answer, lang='uk')
                # Зберігаємо у тимчасовий файл
                tts.save("response.mp3")
                
                # Читаємо файл назад для відтворення
                with open("response.mp3", "rb") as f:
                    audio_bytes = f.read()
                
                st.audio(audio_bytes, format='audio/mp3', autoplay=True)
                
                # Видаляємо файл після використання (опціонально)
                os.remove("response.mp3")
            except Exception as e_audio:
                st.warning("Помилка створення аудіо. Спробуйте оновити сторінку.")
            # ----------------------------------------------------
            
        except Exception as e:
            st.error(f"Помилка: {str(e)}")
