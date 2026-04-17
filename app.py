import streamlit as st
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from PIL import Image
import io
import base64

# 1. КОНФІГУРАЦІЯ
try:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    # Створюємо клієнт ElevenLabs
    el_client = ElevenLabs(api_key=st.secrets["ELEVENLABS_KEY"])
except Exception as e:
    st.error("Помилка секретів! Перевірте GEMINI_KEY та ELEVENLABS_KEY у налаштуваннях Streamlit.")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

st.set_page_config(page_title="AI Tutor Pro", page_icon="🎓")
st.title("🎓 Твій реалістичний репетитор")

SYSTEM_PROMPT = """Ти — професійний і дружній репетитор. 
Твоя мета: допомогти учню розібратися в темі через запитання, а не просто дати відповідь.
Спілкуйся виключно українською мовою. Будь емоційним, хвали дитину!"""

# 2. ВХІДНІ ДАНІ
img_file = st.camera_input("📸 Фото завдання")
audio_question = st.audio_input("🎤 Запитай голосом")
user_text = st.text_input("💬 Твоє питання")

# 3. ЛОГІКА
if img_file or audio_question or user_text:
    with st.spinner('Репетитор обмірковує відповідь...'):
        try:
            content = [SYSTEM_PROMPT]
            if user_text: content.append(f"Питання учня: {user_text}")
            if audio_question:
                content.append({
                    "mime_type": "audio/wav",
                    "data": audio_question.getvalue()
                })
            if img_file:
                content.append(Image.open(img_file))
            
            # Отримуємо текст від Gemini
            response = model.generate_content(content)
            answer = response.text
            
            st.info(answer)
            
            # --- ВИПРАВЛЕНА ОЗВУЧКА ELEVENLABS ---
            try:
                # ВАЖЛИВО: Використовуємо el_client.generate (правильний синтаксис)
                audio_stream = el_client.text_to_speech.convert(
                    text=answer,
                    voice_id="pNInz6obpg8n9YZZ9NpS", # Це ID голосу 'Adam', він добре працює
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
                
                # Перетворюємо генератор в байти
                audio_bytes = b"".join(audio_stream)
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
                audio_html = f"""
                    <audio autoplay="true" controls style="width: 100%;">
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
                
            except Exception as e_audio:
                st.warning(f"Деталі помилки голосу: {str(e_audio)}")
                st.info("Підказка: Перевірте, чи не закінчився ліміт символів на ElevenLabs.")
            
        except Exception as e:
            st.error(f"Помилка Gemini: {str(e)}")
