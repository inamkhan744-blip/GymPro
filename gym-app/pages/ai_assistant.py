import streamlit as st
from datetime import date, datetime, timedelta
import io
import asyncio
import edge_tts
import speech_recognition as sr
import tempfile
import os
import random

# ─────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Gym Assistant", page_icon="💪", layout="wide")

# ─────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "current_gym" not in st.session_state:
    st.session_state.current_gym = "gym_001"

# ─────────────────────────────────────────────────────────
# DATABASE FUNCTIONS
# ─────────────────────────────────────────────────────────
def get_members(gym_id=None):
    members = [
        {"full_name": "Ali Khan", "status": "active", "expiry_date": (date.today() + timedelta(days=30)).isoformat(), "phone": "03001234567"},
        {"full_name": "Sara Ahmed", "status": "active", "expiry_date": (date.today() + timedelta(days=15)).isoformat(), "phone": "03007654321"},
        {"full_name": "John Doe", "status": "inactive", "expiry_date": (date.today() - timedelta(days=5)).isoformat(), "phone": "03001112222"},
        {"full_name": "Emma Watson", "status": "active", "expiry_date": (date.today() + timedelta(days=45)).isoformat(), "phone": "03003334444"},
        {"full_name": "Usman Chaudhry", "status": "expired", "expiry_date": (date.today() - timedelta(days=10)).isoformat(), "phone": "03005556666"},
        {"full_name": "Fatima Zahra", "status": "active", "expiry_date": (date.today() + timedelta(days=20)).isoformat(), "phone": "03007778888"},
    ]
    return members

def get_recent_scans(gym_id=None, limit=100, today_only=False):
    if today_only:
        return [{"time": datetime.now().isoformat()} for _ in range(random.randint(15, 40))]
    return []

def get_todays_fees(gym_id=None):
    return [random.randint(1000, 5000) for _ in range(random.randint(3, 10))]

def get_gym_data(gym_id):
    members = get_members(gym_id=gym_id)
    active = [m for m in members if m.get('status') == 'active']
    today_att = get_recent_scans(gym_id=gym_id, limit=100, today_only=True)
    today_fees = get_todays_fees(gym_id=gym_id)
    
    expired = []
    for m in members:
        if m.get('expiry_date'):
            try:
                if date.fromisoformat(m['expiry_date']) < date.today():
                    expired.append(m['full_name'])
            except:
                pass
    
    return f"""
📊 GYM DATA REPORT
━━━━━━━━━━━━━━━━━━━━━
Total Members: {len(members)}
Active Members: {len(active)}
Today's Attendance: {len(today_att)}
Today's Collection: PKR {sum(today_fees) if today_fees else 0}
Expired Members: {len(expired)}
Expired Names: {', '.join(expired[:3]) if expired else 'None'}
━━━━━━━━━━━━━━━━━━━━━
"""

# ─────────────────────────────────────────────────────────
# 🎬 VIDEO PLAYER (YouTube KE ILAWA - 4 Platforms)
# ─────────────────────────────────────────────────────────
def video_player():
    st.markdown("""
        <h3 style='text-align: center;'>🎬 VIDEO PLAYER - YouTube ke ilawa 4 Platforms</h3>
        <hr>
    """, unsafe_allow_html=True)
    
    st.info("💡 **Choose karo kahan se dekhna hai:**")
    
    platform = st.radio(
        "Select Platform:",
        ["🌐 Dailymotion", "🎬 Tubi Movies", "🚀 Playful (No Ads YouTube)", "🎵 Spotify Web (Audio)"],
        horizontal=True,
        key="video_platform"
    )
    
    st.markdown("---")
    
    if platform == "🌐 Dailymotion":
        st.markdown("### 📺 Dailymotion - YouTube ka best alternative")
        st.caption("Millions of videos - Music, Movies, Sports, News")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search video (song, movie, comedy, etc.):", 
                                        placeholder="Example: Atif Aslam song or comedy video",
                                        key="dm_search")
        with col2:
            search_btn = st.button("▶️ PLAY", type="primary", use_container_width=True)
        
        if search_btn and search_query:
            # Dailymotion search embed
            st.markdown(f"""
                <div style="background: black; border-radius: 12px; padding: 10px;">
                    <iframe 
                        width="100%" 
                        height="450" 
                        src="https://www.dailymotion.com/embed/video/search?search={search_query.replace(' ', '+')}"
                        frameborder="0" 
                        allowfullscreen
                        allow="autoplay; fullscreen">
                    </iframe>
                </div>
            """, unsafe_allow_html=True)
            st.success(f"✅ Searching: {search_query} on Dailymotion")
        
        elif search_btn and not search_query:
            st.warning("⚠️ Kuch search karo!")
        
        # Popular suggestions
        with st.expander("🔥 Popular searches (click to use)"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("🎵 Atif Aslam songs"):
                    st.session_state.dm_search = "Atif Aslam"
                    st.rerun()
                if st.button("🎬 Latest movie trailer"):
                    st.session_state.dm_search = "movie trailer"
                    st.rerun()
            with col_b:
                if st.button("😂 Comedy clips"):
                    st.session_state.dm_search = "comedy"
                    st.rerun()
                if st.button("🏋️ Workout videos"):
                    st.session_state.dm_search = "workout"
                    st.rerun()
            with col_c:
                if st.button("🎮 Gaming"):
                    st.session_state.dm_search = "gaming"
                    st.rerun()
                if st.button("📰 News"):
                    st.session_state.dm_search = "news"
                    st.rerun()
    
    elif platform == "🎬 Tubi Movies":
        st.markdown("### 🎬 Tubi - Free Movies & TV Shows")
        st.caption("Thousands of Hollywood movies, Bollywood, Pakistani dramas - 100% FREE")
        
        st.info("🎥 **Direct website opens in iframe - search karo jo movie chahiye**")
        
        if st.button("🚀 OPEN TUBI MOVIES", type="primary", use_container_width=True):
            st.markdown("""
                <div style="background: black; border-radius: 12px; padding: 10px;">
                    <iframe 
                        width="100%" 
                        height="550" 
                        src="https://tubitv.com/home"
                        frameborder="0" 
                        allowfullscreen>
                    </iframe>
                </div>
            """, unsafe_allow_html=True)
            st.success("✅ Tubi Movies loaded! Search karo jo movie chahiye.")
        
        st.markdown("""
        **Popular movies on Tubi (free):**
        - Bollywood classics
        - Hollywood action movies  
        - Pakistani dramas
        - Comedy shows
        """)
    
    elif platform == "🚀 Playful (No Ads YouTube)":
        st.markdown("### 🚀 Playful - YouTube WITHOUT ADS!")
        st.caption("Same YouTube videos, but NO advertisements - 100% free")
        
        st.info("🎥 **Yahan YouTube ki video daalo, bina ads ke chalegi!**")
        
        video_url = st.text_input("🔗 Paste YouTube URL or Video ID:", 
                                 placeholder="https://youtu.be/... or https://youtube.com/watch?v=...",
                                 key="playful_url")
        
        if st.button("▶️ PLAY WITHOUT ADS", type="primary", use_container_width=True):
            if video_url:
                # Extract video ID
                video_id = video_url.strip()
                if "youtu.be" in video_id:
                    video_id = video_id.split("/")[-1].split("?")[0]
                elif "watch?v=" in video_id:
                    video_id = video_id.split("watch?v=")[1].split("&")[0]
                elif len(video_id) == 11:
                    pass
                else:
                    st.error("❌ Invalid YouTube URL!")
                    return
                
                # Playful embed (no ads)
                st.markdown(f"""
                    <div style="background: black; border-radius: 12px; padding: 10px;">
                        <p style="color: #00ff88; text-align: center;">✅ NO ADS! Enjoy the video...</p>
                        <iframe 
                            width="100%" 
                            height="450" 
                            src="https://playful.vercel.app/embed/{video_id}"
                            frameborder="0" 
                            allowfullscreen
                            allow="autoplay; fullscreen">
                        </iframe>
                    </div>
                """, unsafe_allow_html=True)
                st.success(f"✅ Playing video WITHOUT ADS!")
            else:
                st.warning("⚠️ Please paste YouTube URL!")
        
        st.caption("💡 **Tip:** Koi bhi YouTube video daalo - ads nahi aayengi!")
    
    elif platform == "🎵 Spotify Web (Audio)":
        st.markdown("### 🎵 Spotify Web - Millions of Songs Free")
        st.caption("Hindi, Urdu, Punjabi, English, Pakistani songs - sab free mein suno!")
        
        st.info("🎧 **Direct Spotify Web Player - Search karo jo gaana chahiye**")
        
        if st.button("🎵 OPEN SPOTIFY WEB", type="primary", use_container_width=True):
            st.markdown("""
                <div style="background: #121212; border-radius: 12px; padding: 10px;">
                    <iframe 
                        width="100%" 
                        height="550" 
                        src="https://open.spotify.com/"
                        frameborder="0" 
                        allowfullscreen
                        allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture">
                    </iframe>
                </div>
            """, unsafe_allow_html=True)
            st.success("✅ Spotify loaded! Search karo - Atif Aslam, Ali Zafar, NFAK, or any song.")
        
        st.markdown("""
        **Popular Pakistani artists on Spotify:**
        - 🎤 Atif Aslam
        - 🎤 Ali Zafar  
        - 🎤 Nusrat Fateh Ali Khan
        - 🎤 Abida Parveen
        - 🎤 Strings
        - 🎤 Young Stunners
        """)

# ─────────────────────────────────────────────────────────
# 🎵 MUSIC PLAYER (Audio Focused)
# ─────────────────────────────────────────────────────────
def music_player():
    st.markdown("""
        <h3 style='text-align: center;'>🎵 MUSIC PLAYER - Gaane Suno Free Mein</h3>
        <hr>
    """, unsafe_allow_html=True)
    
    platform = st.radio(
        "Select Music Platform:",
        ["🎵 Spotify Web", "🎧 JioSaavn", "🌐 SoundCloud", "📻 Online Radio"],
        horizontal=True,
        key="music_platform"
    )
    
    if platform == "🎵 Spotify Web":
        st.markdown("### 🎵 Spotify - Sabse bada music library")
        if st.button("🎧 OPEN SPOTIFY", type="primary", use_container_width=True):
            st.markdown("""
                <iframe 
                    width="100%" 
                    height="500" 
                    src="https://open.spotify.com/embed"
                    frameborder="0" 
                    allow="autoplay; clipboard-write; encrypted-media; fullscreen">
                </iframe>
            """, unsafe_allow_html=True)
    
    elif platform == "🎧 JioSaavn":
        st.markdown("### 🎧 JioSaavn - Best for Hindi/Urdu/Punjabi")
        st.caption("Pakistani aur Indian gaane - bilkul free!")
        if st.button("🎵 OPEN JIOSAAVN", type="primary", use_container_width=True):
            st.markdown("""
                <iframe 
                    width="100%" 
                    height="500" 
                    src="https://www.jiosaavn.com/"
                    frameborder="0" 
                    allowfullscreen>
                </iframe>
            """, unsafe_allow_html=True)
    
    elif platform == "🌐 SoundCloud":
        st.markdown("### 🌐 SoundCloud - Independent Artists + Remixes")
        if st.button("🎶 OPEN SOUNDCLOUD", type="primary", use_container_width=True):
            st.markdown("""
                <iframe 
                    width="100%" 
                    height="500" 
                    src="https://soundcloud.com/stream"
                    frameborder="0" 
                    allow="autoplay">
                </iframe>
            """, unsafe_allow_html=True)
    
    elif platform == "📻 Online Radio":
        st.markdown("### 📻 Live Radio Stations")
        radio_station = st.selectbox("Select Radio Station:", [
            "🎵 FM 100 Pakistan",
            "🎤 FM 91 (City FM)",
            "🌍 BBC Asian Network",
            "🎶 Radio Mirchi"
        ])
        if st.button("🔊 PLAY RADIO", type="primary"):
            st.audio("https://streaming.radio.co/something.mp3", format="audio/mp3")
            st.info("Radio stations - URL update karna hoga apne hisaab se")

# ─────────────────────────────────────────────────────────
# 🎙️ MICROPHONE FUNCTIONS
# ─────────────────────────────────────────────────────────
def mic_input():
    audio = st.audio_input("🎤 Click and speak (Urdu/English)", key="mic_input")
    if audio:
        return audio.getvalue()
    return None

def transcribe_audio(audio_bytes):
    if not audio_bytes:
        return None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        r = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language="ur-PK")
        
        os.unlink(tmp_path)
        return text
    except:
        return None

# ─────────────────────────────────────────────────────────
# 🔊 TEXT TO SPEECH
# ─────────────────────────────────────────────────────────
async def text_to_speech(text):
    try:
        voice = "ur-PK-AsadNeural"
        communicate = edge_tts.Communicate(text[:400], voice)
        audio_fp = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_fp.write(chunk["data"])
        audio_fp.seek(0)
        return audio_fp.read()
    except:
        return None

def tts_sync(text):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(text_to_speech(text))
        loop.close()
        return result
    except:
        return None

# ─────────────────────────────────────────────────────────
# 🤖 AI RESPONSE - HAR SAWAAL KA ALAG JAWAB
# ─────────────────────────────────────────────────────────
def get_ai_response(question, gym_data):
    q = question.lower().strip()
    
    if q in ["salam", "assalam", "hello", "hi", "hey"]:
        return "👋 **Assalam-u-Alaikum!** Main AI Gym Assistant hoon. Gym statistics, diet plan, workout routine, aur media player mein madad kar sakta hoon. Kya poochna chahenge?"
    
    elif "total member" in q or "kitne member" in q:
        for line in gym_data.split('\n'):
            if "Total Members:" in line:
                return f"📊 **{line.strip()}**"
    
    elif "active member" in q or "active kitne" in q:
        for line in gym_data.split('\n'):
            if "Active Members:" in line:
                return f"💪 **{line.strip()}**"
    
    elif "attendance" in q or "aaj kitne aaye" in q:
        for line in gym_data.split('\n'):
            if "Today's Attendance:" in line:
                return f"📋 **{line.strip()}**"
    
    elif "collection" in q or "paisa" in q or "fee" in q:
        for line in gym_data.split('\n'):
            if "Today's Collection:" in line:
                return f"💰 **{line.strip()}**"
    
    elif "diet" in q or "khana" in q or "protein" in q:
        return "🥗 **DIET PLAN:** Morning: eggs + oats, Lunch: chicken + rice, Dinner: light meal. Avoid junk food, drink 8-10 glasses water."
    
    elif "workout" in q or "exercise" in q or "kasrat" in q:
        return "🏋️ **WORKOUT:** Monday Chest, Tuesday Back, Wednesday Legs, Thursday Cardio, Friday Full Body, Saturday Abs, Sunday Rest."
    
    elif "time" in q or "timing" in q:
        return "⏰ **GYM TIMINGS:** Morning 6am-12pm, Evening 3pm-10pm. Open 7 days!"
    
    else:
        return f"🤔 **Main ne ye sawaal samjha:** '{question}'\n\n❓ Aap pooch sakte hain: 'Kitne active members?' ya 'Diet plan kya hai?' ya 'Workout batao'"

# ─────────────────────────────────────────────────────────
# 💬 AI CHAT
# ─────────────────────────────────────────────────────────
def ai_chat():
    st.markdown("""
        <h3 style='text-align: center;'>💬 AI CHAT - Gym Assistant</h3>
        <hr>
    """, unsafe_allow_html=True)
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        audio_bytes = mic_input()
    
    with col2:
        text_input = st.chat_input("Apna sawal likhein...")
    
    user_question = None
    
    if audio_bytes:
        with st.spinner("🎧 Sun raha hoon..."):
            user_question = transcribe_audio(audio_bytes)
            if user_question:
                st.success(f"🎤 Aapne kaha: **{user_question}**")
    
    if text_input:
        user_question = text_input
    
    if user_question and user_question != st.session_state.last_question:
        st.session_state.last_question = user_question
        
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        
        with st.spinner("🤔 Soch raha hoon..."):
            gym_data = get_gym_data(st.session_state.current_gym)
            ai_response = get_ai_response(user_question, gym_data)
        
        with st.spinner("🔊 Awaaz bana raha hoon..."):
            ai_audio = tts_sync(ai_response[:350])
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": ai_response,
            "audio": ai_audio
        })
        
        st.rerun()
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.last_question = ""
        st.rerun()

# ─────────────────────────────────────────────────────────
# 🏠 SIDEBAR
# ─────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/gym.png", width=80)
        st.markdown("# 💪 AI Gym Assistant")
        st.markdown("---")
        
        st.markdown("### 🏢 Select Gym")
        gyms = ["🏋️‍♂️ Main Gym", "🏋️‍♀️ Women's Gym", "💪 Elite Gym"]
        selected_gym = st.selectbox("Choose Location:", gyms, key="gym_selector")
        
        if "Main" in selected_gym:
            st.session_state.current_gym = "gym_001"
        elif "Women" in selected_gym:
            st.session_state.current_gym = "gym_002"
        else:
            st.session_state.current_gym = "gym_003"
        
        st.markdown("---")
        
        st.markdown("### 📊 Quick Stats")
        gym_data = get_gym_data(st.session_state.current_gym)
        for line in gym_data.split('\n')[:5]:
            if line.strip() and "━━" not in line:
                st.info(line.strip())
        
        st.markdown("---")
        
        st.markdown("### 📖 Media Platforms Available")
        st.markdown("""
        🎬 **Video:**
        - Dailymotion
        - Tubi Movies (Free Hollywood)
        - Playful (YouTube NO ADS)
        
        🎵 **Audio:**
        - Spotify Web
        - JioSaavn
        - SoundCloud
        """)
        
        st.markdown("---")
        st.caption("Made with ❤️ | YouTube ke ilawa 6 platforms!")

# ─────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────
def render(gym_id=None, role=None):
    sidebar()
    
    st.markdown("""
        <div style='text-align: center; padding: 10px;'>
            <h1>🤖 AI Gym Assistant</h1>
            <p style='font-size: 18px;'>💪 Gym Management + 🎬 Media Player (YouTube ke ilawa)</p>
            <p style='color: #00ff88;'>✅ Dailymotion | ✅ Tubi Movies | ✅ Spotify | ✅ JioSaavn | ✅ Playful (No Ads YouTube)</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["🎬 VIDEO PLAYER", "🎵 MUSIC PLAYER", "💬 AI CHAT"])
    
    with tab1:
        video_player()
    
    with tab2:
        music_player()
    
    with tab3:
        ai_chat()
    
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: gray;'>
            <p>🌟 6 Media Platforms - Sab Free, Sab Online, YouTube ke ilawa!</p>
            <p>🎬 Dailymotion | 🎬 Tubi (Free Movies) | 🚀 Playful (YouTube No Ads)</p>
            <p>🎵 Spotify | 🎧 JioSaavn | 🌐 SoundCloud</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render(None, "admin")