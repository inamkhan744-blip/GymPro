import streamlit as st
import os

# Streamlit ke Secrets se key uthayen
# Agar local testing kar rahe hain aur secret nahi mil raha, 
# toh fallback ke liye .env ya code ka option rakhen, 
# lekin Streamlit Cloud par ye best hai:

api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("GROQ_API_KEY nahi mili! Streamlit Settings mein Secrets add karein.")
    st.stop()

client = Groq(api_key=api_key)
