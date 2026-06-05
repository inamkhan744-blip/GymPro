import streamlit as st
import asyncio
import edge_tts
import io
import base64
import yt_dlp
import os
import os
from pages.ai_functions import get_ai_response
# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Gym AI Assistant", layout="wide")


# ---------------- HEADER ----------------
def set_bg():
    st.markdown("""
    <div style="
        background: linear-gradient(90deg,#0f172a,#1e293b);
        padding:20px;
        border-radius:15px;
        color:white;
        text-align:center;">
        <h2>🏋️ Gym AI Assistant</h2>
        <p>Smart Urdu AI + Music + Voice System</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------- BACKGROUND MUSIC ----------------
def get_music(song):
    query = f"ytsearch1:{song}"

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)

        video = info["entries"][0]

        title = video["title"]
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        audio_url = video["url"]

        return title, video_url, audio_url

# ---------------- MUSIC SEARCH ----------------
def play_bg_music():
    try:
        music_file = "gym_music.mp3"

        if not os.path.exists(music_file):
            return

        with open(music_file, "rb") as f:
            data = f.read()

        b64 = base64.b64encode(data).decode()

        st.markdown(
            f"""
            <audio autoplay loop controls>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.error(f"Background Music Error: {e}")

# ---------------- MUSIC PLAYER ----------------
def music_player():
    st.markdown("## 🎧 Gym Music Player")

    song = st.text_input(
        "🔎 Song search karo",
        key="music_search_input"
    )

    col1, col2 = st.columns(2)

    if col1.button("🎥 Play Video", key="play_video_btn"):

        if not song:
            st.warning("Pehle song likho")
            return

        try:
            title, video_url, audio_url = get_music(song)

            st.success(f"🎥 Video: {title}")

            st.video(video_url)

        except Exception as e:
            st.error(f"Video error: {e}")

    if col2.button("🎵 Play Audio", key="play_audio_btn"):

        if not song:
            st.warning("Pehle song likho")
            return

        try:
            title, video_url, audio_url = get_music(song)

            st.success(f"🎧 Audio: {title}")

            st.audio(audio_url)

        except Exception as e:
            st.error(f"Audio error: {e}")

# ---------------- AI VOICE ----------------
async def generate_audio(text):
    communicate = edge_tts.Communicate(str(text), "ur-PK-AsadNeural")

    audio_fp = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_fp.write(chunk["data"])

    audio_fp.seek(0)
    return audio_fp

def run_audio(text):
    try:
        return asyncio.run(generate_audio(str(text)))
    except Exception as e:
        print("Audio error:", e)
        return None

# ---------------- MAIN UI 
def render(gym_id=None, role="staff"):

    set_bg()
    music_player()

    st.divider()
    st.subheader("🤖 Gym AI Chat")

    # INIT chat
    if "chat" not in st.session_state:
        st.session_state.chat = []

    # SHOW CHAT
    for role_, msg in st.session_state.chat:
        with st.chat_message(role_):
            st.write(msg)

    # INPUT
    user_input = st.chat_input("💬 Gym AI se poochain...")

    if user_input:

        result = get_ai_response(user_input)

        if isinstance(result, tuple):
            answer = str(result[0])
        else:
            answer = str(result)

        st.session_state.chat.append(("user", user_input))
        st.session_state.chat.append(("assistant", answer))

        audio = run_audio(answer)
        if audio:
            st.audio(audio, format="audio/mp3")

    # ❌ NO rerun here (IMPORTANT FIX)

# ---------------- RUN ----------------
if __name__ == "__main__":
    render()