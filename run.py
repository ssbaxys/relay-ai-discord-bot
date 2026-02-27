import os
import threading
from flask import Flask
from dotenv import load_dotenv
from app.core.bot import client

# Tiny web server to keep Render happy
app = Flask(__name__)

@app.route('/')
def home():
    return "Mirra AI Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Check if token exists in environment BEFORE loading .env
    env_token = os.getenv("DISCORD_TOKEN")
    
    # Load .env but DON'T override existing environment variables
    load_dotenv(override=False)
    
    # Final token check
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("[CRITICAL] DISCORD_TOKEN not found in environment or .env!")
        exit(1)
    
    # Diagnostics (Safe)
    source = "Render Dashboard" if env_token else ".env file / GitHub"
    clean_token = token.strip().strip('"').strip("'")
    
    print(f"[DIAGNOSTIC] Token Source: {source}")
    print(f"[DIAGNOSTIC] Token Length: {len(clean_token)}")
    if len(clean_token) > 10:
        print(f"[DIAGNOSTIC] Token Format: {clean_token[:4]}...{clean_token[-4:]}")
    
    # Start web server in a separate thread
    threading.Thread(target=run_web, daemon=True).start()
    
    client.run(clean_token)
