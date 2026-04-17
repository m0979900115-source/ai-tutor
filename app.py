import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# 1. НАЛАШТУВАННЯ (Ваш ключ тепер у лапках, помилки NameError не буде)
API_KEY = "AQ.Ab8RN6LzzJdGJ759IPA37uhSLJUSQ-ciE6AoISavDHFFLVqLCQ"
genai.configure(api_key=API_KEY)

# Налаштування моделі
generation_config = {
  "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 2048,
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)

# 2. ІНТЕРФЕЙС ДОДАТКА
st.set_page_config(page_title="AI Репетитор", page_icon="🎓")
st.title("🎓 Мій персональний репетитор")
st.write("Сфотографуй завдання, і я допоможу розібратися!")

# Інструкція для ШІ (System Prompt)
system_instruction = """
Ти — професійний і терплячий репетитор. 
Твоя мета: допомогти учню зрозуміти матеріал самостійно.
ПРАВИЛА:
1. Ніколи не давай готову відповідь відразу.
2. Якщо на фото задача, перевір хід думок учня.
3. Став навідні запитання (метод Сократа).
4. Використовуй просту мову, зрозумілу дитині.
5. Хвали за старання!
6. СПІЛКУЙСЯ ВИКЛЮЧНО УКРАЇНСЬКОЮ МОВОЮ.
"""

# 3. ФУНКЦІОНАЛ (Камера та текст)
img_file = st.camera_input("Зроби фото завдання")
user_text = st.text_input("Що саме викликає труднощі?", placeholder="Наприклад: 'Не розумію, як це додати'")

if img_file:
    with st.spinner('Репетитор уважно розглядає зошит...'):
        # Підготовка картинки
        img_data = img_file.getvalue()
        image_parts = [{"mime_type": "image/jpeg", "data": img_data}]
        
        # Запит до Gemini
        prompt_parts = [system_instruction, user_text if user_text else "Допоможи розібратися з цим завданням", image_parts[0]]
        response = model.generate_content(prompt_parts)
        
        # Виведення результату
        st.info("💡 Порада вчителя:")
        st.write(response.text)
        
        # ГЕНЕРАЦІЯ ГОЛОСУ
        try:
            tts = gTTS(text=response.text, lang='uk')
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            st.audio(audio_buffer, format='audio/mp3')
        except Exception as e:
            st.error("Тимчасова помилка озвучки, але текст вище!")

st.markdown("---")
st.caption("Порада: щоб ШІ краще бачив текст, тримайте телефон рівно над зошитом.")
