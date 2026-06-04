import os
import io
from groq import Groq
import edge_tts
import asyncio
import sqlite3
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
#111111111
from whatsapp_utils import send_whatsapp_reminder
#1111111
#222222222
from database import get_member_phone
from whatsapp_utils import send_whatsapp_reminder

def process_gym_action(user_input, name):
    if "reminder" in user_input.lower():
        phone = get_member_phone(name)
        if phone:
            link = send_whatsapp_reminder(phone, name)
            return f"Action Complete! Aap is link par click kar ke message bhej sakte hain: {link}"
        else:
            return "Mujhe database mein is member ka phone number nahi mila."

    # Baqi normal AI response
    return get_ai_response_with_db(user_input)
#222222222
async def generate_audio(text):
    # Pakistani Urdu Neural Voice
    voice = "ur-PK-AsadNeural" 
    communicate = edge_tts.Communicate(text, voice)
    audio_fp = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_fp.write(chunk["data"])
    audio_fp.seek(0)
    return audio_fp

def get_ai_response(user_input):
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional and friendly Gym Assistant. Provide detailed, helpful, and comprehensive answers in Urdu. Explain things clearly and step-by-step."},
                {"role": "user", "content": user_input}
            ],
            model="llama-3.3-70b-versatile",
        )
        answer = response.choices[0].message.content
        # Audio generation (sync wrap for asyncio)
        audio_fp = asyncio.run(generate_audio(answer))
        return answer, audio_fp
    except Exception as e:
        return f"Error: {e}", None




# ... baqi imports wahi rahengi

def get_gym_summary():
    try:
        # Apni database file ka path dein
        conn = sqlite3.connect('gym_pro.db') 
        cursor = conn.cursor()
        
        # Misal ke tor par pending payments count
        cursor.execute("SELECT COUNT(*) FROM members WHERE status = 'pending'")
        pending_count = cursor.fetchone()[0]
        
        conn.close()
        return f"Pending Fee Members: {pending_count}. Be professional and remind me if I need to send notices."
    except Exception:
        return "Gym status currently unavailable."

def get_ai_response(user_input):
    try:
        # 1. Database se current status uthayein
        gym_status = get_gym_summary()
        
        # 2. System prompt mein context inject karein
        system_content = f"You are a professional Gym Assistant. Current Status: {gym_status}. Explain in Urdu."
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_input}
            ],
            model="llama-3.3-70b-versatile",
        )
        answer = response.choices[0].message.content
        audio_fp = asyncio.run(generate_audio(answer))
        return answer, audio_fp
    except Exception as e:
        return f"Error: {e}", None



def process_voice_command(user_input):
    # Simple check for command
    if "send reminder" in user_input.lower():
        # Yahan aap logic laga sakte hain ke kis ko bhejna hai
        # Misal ke tor par: "send reminder to Ali"
        return "Adil Shah ko reminder bhejna shuru kar raha hoon..."
    
    # Normal response
    return get_ai_response_with_db(user_input)
