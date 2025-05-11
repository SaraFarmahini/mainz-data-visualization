import streamlit as st
import subprocess
import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# Get local IP address
local_ip = get_local_ip()

# Start Streamlit with network access
streamlit_process = subprocess.Popen(['streamlit', 'run', 'streamlit_app.py', '--server.address', local_ip])

print(f"\nYour Streamlit app is now available at:")
print(f"Local URL: http://localhost:8501")
print(f"Network URL: http://{local_ip}:8501")
print("\nShare the Network URL with anyone on your local network.")
print("Note: This will only work for devices connected to the same network.")
print("\nPress Ctrl+C to stop the server.")

try:
    # Keep the script running
    while True:
        streamlit_process.wait()
except KeyboardInterrupt:
    # Clean up
    streamlit_process.terminate()
    print("\nServer stopped.") 