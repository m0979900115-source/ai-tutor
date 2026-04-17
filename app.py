import streamlit as st
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from PIL import Image
import io
import base64

# --- НАЛАШТУВАННЯ ---
try:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    # Створюємо клієнт ElevenLabs
    el_client = ElevenLabs(api_key=st.secrets["ELEVENLABS_KEY"])
except Exception as e:
    st.error("Помилка конфігурації секретів!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

st.title("🎓 Твій реалістичний репетитор")

# --- ІНТЕРФЕЙС ---
img_file = st.camera_input("📸 Фото завдання")
audio_question = st.audio_input("🎤 Запитай голосом")
user_text = st.text_input("💬 Твоє питання")

if img_file or audio_question or user_text:
    with st.spinner('Репетитор думає...'):
        try:
            content = ["Ти репетитор, відповідай українською, допомагай зрозуміти."]
            if user_text: content.append(user_text)
            if audio_question: content.append({"mime_type": "audio/wav", "data": audio_question.getvalue()})
            if img_file: content.append(Image.open(img_file))
            
            response = model.generate_content(content)
            answer = response.text
            st.info(answer)
            
            # --- ОЗВУЧКА ---
            try:
                # Використовуємо універсальний голос 'Aria' або 'Adam' (вони зазвичай є у всіх)
                # Якщо хочете саме Олександра, він має бути доданий у ваш Voice Lab
                audio_gen = el_client.generate(
                    text=answer,
                    voice="Aria", 
                    model="eleven_multilingual_v2"
                )
                
                audio_bytes = b"".join(list(audio_gen))
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
                audio_html = f"""
                    <audio autoplay="true" controls style="width: 100%;">
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
                
            except Exception as e_audio:
                # Цей рядок покаже нам справжню помилку ElevenLabs
                st.warning(f"Деталі помилки голосу: {str(e_audio)}")
            
        except Exception as e:
            st.error(f"Помилка Gemini: {str(e)}")
