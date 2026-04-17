import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from PIL import Image
import io

# 1. НАЛАШТУВАННЯ
# Ваш ключ у лапках — тепер без помилок NameError
API_KEY = "AQ.Ab8RN6LzzJdGJ759IPA37uhSLJUSQ-ciE6AoISavDHFFLVqLCQ"
genai.configure(api_key=API_KEY)

# Використовуємо повну назву моделі з префіксом models/ та суфіксом -latest
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

# Конфігурація сторінки
st.set_page_config(page_title="ШІ-Репетитор", page_icon="🎓", layout="centered")

st.title("🎓 Мій персональний репетитор")
st.write("Сфотографуй завдання, і ми разом його розв'яжемо!")

# Інструкція для ШІ (System Prompt) — щоб був діалог, а не просто відповіді
system_instruction = """
Ти — професійний і добрий репетитор. 
Твоя мета: допомогти учню зрозуміти матеріал самостійно.
ПРАВИЛА:
1. НІКОЛИ не давай готову відповідь відразу.
2. Використовуй метод Сократа: став навідні запитання.
3. Якщо на фото є хід розв'язку — проаналізуй його і знайди помилку.
4. Пояснюй складнощі через прості приклади (наприклад, з гри Bed Wars або техніки).
5. Спілкуйся ВИКЛЮЧНО українською мовою.
6. Хвали дитину за старанність.
"""

# 2. ІНТЕРФЕЙС (Камера та текст)
img_file = st.camera_input("📸 Зроби фото завдання")
user_text = st.text_input("💬 Що саме тобі незрозуміло?", placeholder="Наприклад: 'Як почати це рівняння?'")

# 3. ЛОГІКА РОБОТИ
if img_file:
    with st.spinner('Репетитор розглядає зошит...'):
        try:
            # Відкриваємо зображення через Pillow для стабільності
            img = Image.open(img_file)
            
            # Формуємо запит (Промпт + Текст учня + Фото)
            prompt_content = [
                system_instruction, 
                user_text if user_text else "Допоможи мені розібратися з цим завданням на фото.", 
                img
            ]
            
            # Генерація відповіді
            response = model.generate_content(prompt_content)
            answer_text = response.text
            
            # Виведення тексту
            st.markdown("### 💡 Порада репетитора:")
            st.info(answer_text)
            
            # ГЕНЕРАЦІЯ ГОЛОСУ (Живе спілкування)
            tts = gTTS(text=answer_text, lang='uk')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp, format='audio/mp3')
            
        except Exception as e:
            st.error(f"Виникла помилка: {str(e)}")
            st.warning("Спробуй ще раз або перевір інтернет-з'єднання.")

st.markdown("---")
st.caption("Підказка: Тримай камеру паралельно зошиту, щоб текст було добре видно.")
