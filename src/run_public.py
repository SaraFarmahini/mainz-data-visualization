import streamlit as st
from pyngrok import ngrok
import subprocess
import time
import os

# Start Streamlit in a subprocess
streamlit_process = subprocess.Popen(['streamlit', 'run', 'streamlit_app.py'])

# Wait for Streamlit to start
time.sleep(5)

# Create a public URL with ngrok
public_url = ngrok.connect(8501)
print(f"\nYour Streamlit app is now available at: {public_url}\n")
print("Share this URL with anyone to give them access to your app.")
print("Note: This URL will change each time you restart the script.")
print("\nPress Ctrl+C to stop the server.")

try:
    # Keep the script running
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    # Clean up
    ngrok.kill()
    streamlit_process.terminate()
    print("\nServer stopped.") 