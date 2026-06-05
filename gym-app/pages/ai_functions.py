import os
import io
import sqlite3
import asyncio
from datetime import datetime, timedelta
from groq import Groq
import edge_tts


# ---------------- GROQ SETUP ----------------
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    raise Exception("GROQ_API_KEY missing")

client = Groq(api_key=api_key)


# ---------------- DATABASE ----------------
def init_database():
    conn = sqlite3.connect("gym_complete.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT,
        email TEXT,
        membership_type TEXT,
        join_date DATE,
        expiry_date DATE,
        status TEXT,
        fee_paid INTEGER
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS trainers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        specialty TEXT,
        schedule TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY,
        name TEXT,
        status TEXT,
        last_maintenance DATE
    )''')

    conn.commit()
    conn.close()


# ---------------- AUDIO (IMPROVED URDU VOICE) ----------------
async def generate_audio(text):
    voice = "ur-PK-AsadNeural"

    communicate = edge_tts.Communicate(text, voice)
    audio_fp = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_fp.write(chunk["data"])

    audio_fp.seek(0)
    return audio_fp


def run_audio(text):
    return asyncio.run(generate_audio(text))


def clean_text(text):
    return (
        text.replace("*", "")
        .replace("#", "")
        .replace("AI", "اے آئی")
        .replace("Gym", "جم")
        .strip()
    )


# ---------------- GYM QUERY ----------------
def process_gym_query(user_input):
    conn = sqlite3.connect("gym_complete.db")
    cursor = conn.cursor()

    user_input = user_input.lower()
    response = ""

    if "pending" in user_input or "baqi" in user_input:
        cursor.execute("SELECT name, phone FROM members WHERE status='pending'")
        rows = cursor.fetchall()

        response = f"Pending Members: {len(rows)}\n"
        for r in rows:
            response += f"- {r[0]} ({r[1]})\n"

    elif "trainer" in user_input:
        cursor.execute("SELECT name, specialty FROM trainers")
        rows = cursor.fetchall()

        response = "Trainers:\n"
        for r in rows:
            response += f"- {r[0]} - {r[1]}\n"

    elif "equipment" in user_input:
        cursor.execute("SELECT name, status FROM equipment")
        rows = cursor.fetchall()

        response = "Equipment Status:\n"
        for r in rows:
            response += f"- {r[0]}: {r[1]}\n"

    else:
        response = "Mujhe is ka koi relevant data nahi mila."

    conn.close()
    return response


# ---------------- AI RESPONSE (IMPROVED URDU PROMPT) ----------------
def get_ai_response(user_input):
    system_prompt = """
    آپ جم پرو کے اے آئی اسسٹنٹ ہیں۔

    قواعد:
    - ہمیشہ اردو میں جواب دیں۔
    - رومن اردو استعمال نہ کریں۔
    - مختصر اور واضح جواب دیں۔
    - جم، فٹنس، ممبرشپ اور سسٹم سے متعلق سوالات کا جواب دیں۔
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": 
            system_prompt},
                {"role": "user", "content": user_input}
            ]
        )

        answer = response.choices[0].message.content

        return answer, run_audio(clean_text(answer))

    except Exception as e:
        return f"Error: {str(e)}", None


# ---------------- MANAGER ----------------
class GymManager:
    def __init__(self):
        self.conn = sqlite3.connect("gym_complete.db")

    def add_member(self, name, phone, membership_type):
        cursor = self.conn.cursor()

        join_date = datetime.now().date()
        expiry_date = join_date + timedelta(days=30)

        cursor.execute('''INSERT INTO members
            (name, phone, membership_type, join_date, expiry_date, status)
            VALUES (?, ?, ?, ?, ?, 'active')''',
            (name, phone, membership_type, join_date, expiry_date))

        self.conn.commit()
        return f"Member {name} add ho gaya hai."

    def get_pending_payments(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM members WHERE status='pending'")
        return cursor.fetchone()[0]

    def generate_report(self):
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM members WHERE status='active'")
        active = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(fee_paid) FROM members WHERE status='active'")
        revenue = cursor.fetchone()[0] or 0

        return {
            "active_members": active,
            "monthly_revenue": revenue,
            "pending_payments": self.get_pending_payments()
        }


# ---------------- AUDIO SYSTEM ----------------
class GymAudioSystem:
    def __init__(self):
        self.playlist = []
        self.current_track = 0

    def load_playlist(self, folder_path="gym_music/"):
        import os
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith((".mp3", ".wav")):
                    self.playlist.append(os.path.join(folder_path, file))

    def play_motivational(self):
        import pygame
        pygame.mixer.init()

        if self.playlist:
            pygame.mixer.music.load(self.playlist[self.current_track])
            pygame.mixer.music.play()
            self.current_track = (self.current_track + 1) % len(self.playlist)

    def play_announcement(self, text):
        return run_audio(text)