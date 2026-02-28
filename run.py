import os
import threading
from flask import Flask
from dotenv import load_dotenv
from app.core.bot import client

# Tiny web server to keep Render happy
app = Flask(__name__)

@app.route('/')
def home():
    return "Relay AI Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    load_dotenv()
    
    # Start web server in a separate thread
    threading.Thread(target=run_web, daemon=True).start()
    
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("[CRITICAL] DISCORD_TOKEN not found!")
        exit(1)
    
    client.run(token)
