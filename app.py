import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from PIL import Image
import io

# 1. КОНФІГУРАЦІЯ
API_KEY = "AQ.Ab8RN6LzzJdGJ759IPA37uhSLJUSQ-ciE6AoISavDHFFLVqLCQ"
genai.configure(api_key=API_KEY)

# Використовуємо найновішу модель Gemini 3
model = genai.GenerativeModel('gemini-3-flash-preview')

st.set_page_config(page_title="AI Tutor 3.0", page_icon="🎓", layout="centered")

# Кастомний стиль для гарного вигляду
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #FF4B4B; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 Твій персональний репетитор 3.0")
st.write("Привіт! Я твій ШІ-вчитель. Покажи мені завдання або просто запитай.")

# Системна інструкція для "живого" вчителя
SYSTEM_PROMPT = """
Ти — емпатичний, крутий репетитор. 
Твоє завдання: допомогти учню зрозуміти логіку, а не просто дати відповідь.
- Використовуй метод Сократа: став навідні запитання.
- Можеш наводити приклади з ігор (наприклад, Bed Wars), якщо це допоможе пояснити математику чи логіку.
- Спілкуйся виключно українською мовою.
- Будь емоційним: використовуй емодзі, підбадьорюй ("Ти молодець!", "Класна спроба!").
- Якщо на фото задача — спочатку запитай, як дитина сама думає її розв'язати.
"""

# 2. ІНТЕРФЕЙС ВВОДУ
col1, col2 = st.columns(2)

with col1:
    img_file = st.camera_input("📸 Фото завдання")

with col2:
    st.write("🎤 Спілкування")
    audio_question = st.audio_input("Натисни, щоб запитати голосом")
    user_text = st.text_input("💬 Або напиши тут", placeholder="Наприклад: Що це за правило?")

# 3. ОБРОБКА ТА ВІДПОВІДЬ
if img_file or audio_question or user_text:
    with st.spinner('Репетитор думає...'):
        try:
            content_to_send = [SYSTEM_PROMPT]
            
            # Додаємо текст або аудіо-повідомлення
            if user_text:
                content_to_send.append(f"Питання учня: {user_text}")
            if audio_question:
                content_to_send.append(audio_question)
            
            # Додаємо фото, якщо воно є
            if img_file:
                img = Image.open(img_file)
                content_to_send.append(img)
            
            # Отримуємо відповідь від Gemini 3
            response = model.generate_content(content_to_send)
            answer = response.text
            
            st.markdown("---")
            st.subheader("💡 Порада вчителя:")
            st.write(answer)
            
            # ГЕНЕРАЦІЯ ГОЛОСУ (Відповідь вчителя)
            tts = gTTS(text=answer, lang='uk')
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            st.audio(audio_buffer, format='audio/mp3', autoplay=True)
            
        except Exception as e:
            st.error(f"Упс! Виникла технічна заминка: {str(e)}")
            st.info("Переконайся, що в тебе стабільний інтернет.")

st.markdown("---")
st.caption("Порада: Якщо хочеш, щоб я краще бачив текст — тримай камеру рівно.")
