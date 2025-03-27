from fastapi import FastAPI
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.post("/call-bot")
def call_bot(room: str):
    subprocess.Popen(["python", "bot/run.py", room])
    return {"status": "Bot is joining", "room": room}
