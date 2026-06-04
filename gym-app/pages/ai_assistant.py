import sys
import os
import io
import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from pages.ai_functions import get_ai_response
import edge_tts
import asyncio

async def generate_audio(text):
    voice = "ur-PK-AsadNeural" 
    communicate = edge_tts.Communicate(text, voice)
    audio_fp = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_fp.write(chunk["data"])
    audio_fp.seek(0)
    return audio_fp

def transcribe_audio(audio_bytes):
    if audio_bytes is None or 'bytes' not in audio_bytes:
        return None
    try:
        r = sr.Recognizer()
        audio_data = sr.AudioData(audio_bytes['bytes'], sample_rate=48000, sample_width=2)
        # FIX: return aur function call ko ek hi line par likha hai
        return 
        r.recognize_google(audio_data, language="ur-PK")
    except Exception:
        return None

def render(gym_id, role):
    st.title("🤖 AI Gym Assistant")
    
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []

    # Chat history dikhayein
    for msg in st.session_state.ai_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "audio" in msg and msg["audio"]:
                st.audio(msg["audio"], format="audio/mp3")

    # Inputs
    audio = mic_recorder(start_prompt="🎙️ Bol kar poochein", stop_prompt="Stop", key='ai_mic_page')
    prompt = st.chat_input("Apna sawal likhein...")

    user_input = None
    if audio:
        with st.spinner("Sun raha hoon..."):
            user_input = transcribe_audio(audio)
    elif prompt:
        user_input = prompt

    # Response logic
    if user_input:
        if not st.session_state.ai_messages or st.session_state.ai_messages[-1]["content"] != user_input:
            st.session_state.ai_messages.append({"role": "user", "content": user_input})
            
            with st.spinner("Soch raha hoon..."):
                ai_text, _ =   get_ai_response(user_input)
                # Edge-TTS se saaf Pakistani Urdu generate karein
                ai_audio = asyncio.run(generate_audio(ai_text))
            
            st.session_state.ai_messages.append({
                "role": "assistant", 
                "content": ai_text,
                "audio": ai_audio
            })
            st.rerun()
