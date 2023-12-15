from datetime import datetime
from enum import StrEnum, auto
from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    ok: bool = True
    error: str | None = None
    data: T


class Dialog(BaseModel):
    id: int
    title: str
    date: datetime | None


class MessageKind(StrEnum):
    DOC = auto()
    PHOTO = auto()
    TEXT = auto()


class MessageFilter(StrEnum):
    DOC = auto()
    PHOTO = auto()
    PHOTO_VIDEO = auto()


class MediaInfo(BaseModel):
    name: str = ""
    size: int = 0
    mime: str = ""


class Message(BaseModel):
    id: int
    kind: MessageKind
    text: str
    media: MediaInfo | None
    created_at: datetime | None
