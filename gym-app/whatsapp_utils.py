# pywhatkit hata dein
import webbrowser

def send_whatsapp_reminder(phone_number, name):
    # Yeh code server par crash nahi hoga
    message = f"Salam {name}, Inam Khan yahan! Aapki gym fee pending hai."
    # Direct WhatsApp link generate karein
    url = f"https://wa.me/92{phone_number}?text={message.replace(' ', '%20')}"
    
    # Replit mein aap yahan print(url) kar sakte hain
    # Ya agar aap local PC par hain to webbrowser.open(url) use karein
    return f"Link generate ho gaya: {url}"
