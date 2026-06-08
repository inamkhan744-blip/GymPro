import sys
import os
import io
import asyncio
import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from pages.ai_functions import get_ai_response
import edge_tts


# ─────────────────────────────────────────────────────────
# 🔊 Pakistani Urdu Voice Generation (Edge-TTS)
# ─────────────────────────────────────────────────────────
async def generate_audio(text):
    """Edge-TTS se saaf Pakistani Urdu voice generate karta hai"""
    try:
        voice = "ur-PK-AsadNeural"  # Pakistani male voice
        communicate = edge_tts.Communicate(text, voice)
        audio_fp = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_fp.write(chunk["data"])
        audio_fp.seek(0)
        return audio_fp.read()  # bytes return karein (session-safe)
    except Exception as e:
        st.error(f"Voice generate nahi ho saki: {e}")
        return None


def run_async(coro):
    """Streamlit-safe async runner"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(coro)
        loop.close()
        return result
    except Exception as e:
        st.error(f"Audio error: {e}")
        return None


# ─────────────────────────────────────────────────────────
# 🎙️ Voice → Text (Speech Recognition)
# ─────────────────────────────────────────────────────────
def transcribe_audio(audio_bytes):
    """Mic se ayi awaaz ko Urdu text mein convert karta hai"""
    if audio_bytes is None or 'bytes' not in audio_bytes:
        return None
    try:
        r = sr.Recognizer()
        audio_data = sr.AudioData(
            audio_bytes['bytes'], 
            sample_rate=48000, 
            sample_width=2
        )
        # ✅ FIX: return aur function call ek hi line par
        text = r.recognize_google(audio_data, language="ur-PK")
        return text
    except sr.UnknownValueError:
        st.warning("⚠️ Aapki awaaz samajh nahi aayi. Dobara koshish karein.")
        return None
    except sr.RequestError:
        st.error("🌐 Internet connection check karein.")
        return None
    except Exception as e:
        st.error(f"Voice recognition error: {e}")
        return None


# ─────────────────────────────────────────────────────────
# 🤖 Main Render Function
# ─────────────────────────────────────────────────────────
def render(gym_id, role):
    # ── Page Header ──
    st.title("🤖 AI Gym Assistant")
    st.caption("Apna sawal Urdu mein likhein ya bol kar poochein — main aapki madad karunga! 💪")

    # ── Session State Initialize ──
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []
    if "voice_enabled" not in st.session_state:
        st.session_state.voice_enabled = True
    if "last_processed_input" not in st.session_state:
        st.session_state.last_processed_input = ""

    # ── Sidebar Controls ──
    with st.sidebar:
        st.markdown("### ⚙️ AI Assistant Settings")
        
        # Voice toggle
        st.session_state.voice_enabled = st.toggle(
            "🔊 Voice Response", 
            value=st.session_state.voice_enabled,
            help="Band karne se sirf text response milega (tezi aur data bachat)"
        )
        
        # Message counter
        msg_count = len(st.session_state.ai_messages)
        st.metric("💬 Total Messages", msg_count)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.ai_messages = []
            st.session_state.last_processed_input = ""
            st.success("Chat clear ho gaya!")
            st.rerun()
        
        st.divider()
        
        # Tips
        st.markdown("### 💡 Tips")
        st.info(
            "• 🎙️ Mic button daba ke Urdu mein bolein\n\n"
            "• ⌨️ Ya neeche box mein likhein\n\n"
            "• 🏋️ Workout, diet, ya gym ke baare mein poochein\n\n"
            "• 🔊 Voice off karke data bacha sakte hain"
        )

    # ── Welcome Message (First Time) ──
    if not st.session_state.ai_messages:
        with st.chat_message("assistant"):
            st.markdown(
                "👋 **Assalam-o-Alaikum!**\n\n"
                "Main aapka AI Gym Assistant hoon. Aap mujhse ye sab poochh sakte hain:\n\n"
                "- 🏋️ Workout plans aur exercises\n"
                "- 🥗 Diet aur nutrition advice\n"
                "- 💪 Muscle building tips\n"
                "- 🔥 Weight loss strategies\n"
                "- ❓ Gym ke baare mein koi bhi sawal\n\n"
                "**Bolein ya likhein — main hazir hoon!** 😊"
            )

    # ── Chat History Display ──
    for msg in st.session_state.ai_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")

    # ── Input Section ──
    st.divider()
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("**🎙️ Voice:**")
        audio = mic_recorder(
            start_prompt="🎙️ Bolein", 
            stop_prompt="⏹️ Stop", 
            key='ai_mic_page'
        )
    
    with col2:
        st.markdown("**⌨️ Type:**")
        prompt = st.chat_input("Apna sawal yahan likhein...")

    # ── Input Processing ──
    user_input = None
    
    if audio:
        with st.spinner("🎧 Aapki awaaz sun raha hoon..."):
            user_input = transcribe_audio(audio)
            if user_input:
                st.toast(f"✅ Suna: {user_input[:50]}...", icon="🎙️")
    elif prompt:
        user_input = prompt.strip()

    # ── Empty Input Validation ──
    if user_input == "":
        st.warning("⚠️ Kuch likhein ya bolein!")
        user_input = None

    # ── Response Generation ──
    if user_input and user_input != st.session_state.last_processed_input:
        # Save last processed to avoid duplicate
        st.session_state.last_processed_input = user_input
        
        # Add user message
        st.session_state.ai_messages.append({
            "role": "user", 
            "content": user_input
        })

        # Generate AI response
        with st.spinner("🤔 Soch raha hoon..."):
            try:
                ai_response = get_ai_response(user_input)
                
                # Handle tuple or single response
                if isinstance(ai_response, tuple):
                    ai_text = ai_response[0]
                else:
                    ai_text = ai_response
                
                if not ai_text:
                    ai_text = "Maazrat, main abhi jawab nahi de pa raha. Dobara koshish karein."
            
            except Exception as e:
                ai_text = f"⚠️ Error: AI response generate nahi ho saka. ({str(e)[:100]})"

        # Generate audio (only if voice enabled)
        ai_audio = None
        if st.session_state.voice_enabled and ai_text and not ai_text.startswith("⚠️"):
            with st.spinner("🔊 Awaaz tayyar kar raha hoon..."):
                ai_audio = run_async(generate_audio(ai_text))

        # Save assistant message
        st.session_state.ai_messages.append({
            "role": "assistant",
            "content": ai_text,
            "audio": ai_audio
        })
        
        st.rerun()