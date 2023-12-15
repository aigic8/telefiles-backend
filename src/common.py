import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException


class Config:
    api_id: int
    api_hash: str

    def __init__(self, api_id: int, api_hash: str) -> None:
        self.api_id = api_id
        self.api_hash = api_hash


def load_config() -> Config:
    load_dotenv()
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    if api_id is None:
        raise ValueError("TELEGRAM_API_ID can not be empty")
    if api_hash is None:
        raise ValueError("TELEGRAM_API_HASH can not be empty")
    try:
        api_id_int = int(api_id)
        return Config(api_id_int, api_hash)
    except ValueError:
        raise ValueError("TELEGRAM_API_ID should be a number")


def validate_session(session: str | None) -> str:
    if session is None:
        raise HTTPException(status_code=403, detail="bad session")
    session_path = f"sessions/{session}.session"
    session_file = Path(session_path)
    if not session_file.is_file():
        raise HTTPException(status_code=403, detail="bad session")
    return session_path
