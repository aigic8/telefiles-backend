from common import load_config
from lib.tc import TC
from router import auth, dialogs, messages
from fastapi import FastAPI
from pathlib import Path

sessions_path = Path("sessions")
sessions_path.mkdir(parents=True, exist_ok=True)

files_path = Path("files")
files_path.mkdir(parents=True, exist_ok=True)

app = FastAPI()
c = load_config()
tc = TC(c.api_id, c.api_hash)

app.include_router(auth.new_auth_router(tc))
app.include_router(dialogs.new_dialogs_router(tc))
app.include_router(messages.new_messages_router(tc))
