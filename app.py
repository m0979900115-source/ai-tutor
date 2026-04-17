import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# Налаштування Gemini
genai.configure(api_key="AQ.Ab8RN6LzzJdGJ759IPA37uhSLJUSQ-ciE6AoISavDHFFLVqLCQ")
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="ШІ-Репетитор", page_icon="🎓")
st.title("🎓 Мій персональний репетитор")

# Інструкція для ШІ
system_prompt = "Ти — професійний репетитор. Твоє завдання: допомогти учню знайти помилку самостійно. Якщо на фото математика — перевір розрахунки. Якщо мова — перевір граматику. НІКОЛИ не пиши готову відповідь відразу. Став навідні запитання. Використовуй емодзі та підбадьорюй дитину. Спілкуйся виключно українською.".

# Камера
img_file = st.camera_input("Сфотографуй завдання або сторінку")

# Текст
user_question = st.text_input("Що саме тут незрозуміло?", placeholder="Наприклад: як розв'язати це рівняння?")

if img_file and user_question:
    with st.spinner('Репетитор думає...'):
        img = {"mime_type": "image/jpeg", "data": img_file.getvalue()}
        response = model.generate_content([system_prompt, user_question, img])
        
        st.markdown(f"### Порада вчителя:\n{response.text}")
        
        # Генерація голосу
        tts = gTTS(text=response.text, lang='uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')
