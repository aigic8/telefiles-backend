from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import (
    MessageMediaPhoto,
    Photo,
    Document,
    TypeDocumentAttribute,
    TypeMessageMedia,
    DocumentAttributeFilename,
    MessageMediaDocument,
    Message as Msg,
    InputMessagesFilterDocument,
    InputMessagesFilterPhotos,
    InputMessagesFilterPhotoVideo,
)
from telethon.tl.custom import Dialog as Dlg
import asyncio
import socks

from t import Dialog, MediaInfo, Message, MessageFilter, MessageKind


@dataclass(kw_only=True, frozen=True)
class FileInfo:
    mime: str
    name: str | None = None
    size: int | None = None


class Session:
    def __init__(self, session_path: str, api_id: int, api_hash: str) -> None:
        proxy = (socks.SOCKS5, "192.168.43.1", 10800)
        self._c = TelegramClient(session_path, api_id, api_hash, proxy=proxy)

    async def connect(self):
        await self._c.connect()

    async def disconnect(self):
        res = self._c.disconnect()
        if res is not None:
            await res
        else:
            await asyncio.sleep(0)

    async def get_dialogs(
        self, *, limit=30, offset_date: datetime | None = None
    ) -> list[Dialog]:
        raw_dialogs = await self._c.get_dialogs(limit=limit, offset_date=offset_date)
        dialogs: list[Dialog] = []
        for dialog in raw_dialogs:
            d: Dlg = dialog
            dialogs.append(Dialog(id=d.id, title=d.title, date=d.date))
        return dialogs

    async def get_messages(
        self,
        *,
        chat_id: int,
        limit: int = 30,
        filter: MessageFilter,
        offset_id: int | None = None,
    ) -> list[Message]:
        telethon_filter = filter_to_telethon_filter(filter)
        messages = (
            await self._c.get_messages(chat_id, filter=telethon_filter, limit=limit)
            if offset_id is None
            else await self._c.get_messages(
                chat_id, filter=telethon_filter, offset_id=offset_id, limit=limit
            )
        )
        return [telethon_message_to_message(m) for m in messages]

    async def download_file(
        self, *, chat_id: int, message_id: int
    ) -> tuple[AsyncIterator, FileInfo]:
        msg: Msg = await self._c.get_messages(chat_id, ids=message_id)  # type: ignore
        if msg.media is None:
            raise ValueError("message does not have media")
        elif isinstance(msg.media, MessageMediaDocument) and isinstance(
            msg.media.document, Document
        ):
            mime = msg.media.document.mime_type
            name = get_doc_file_name(msg.media.document.attributes)
            size = msg.media.document.size
            file_info = FileInfo(name=name, mime=mime, size=size)
            return self._c.iter_download(msg.media), file_info
        elif isinstance(msg.media, MessageMediaPhoto) and isinstance(
            msg.media.photo, Photo
        ):
            return self._c.iter_download(msg.media), FileInfo(mime="image/jpeg")
        else:
            raise ValueError("message does not have a supported media")

    async def send_code(self, phone: str) -> str:
        res = await self._c.send_code_request(phone)
        return res.phone_code_hash

    async def login(
        self,
        *,
        phone: str,
        phone_code_hash: str,
        password: str | None = None,
        code: int,
    ):
        try:
            await self._c.sign_in(phone, code, phone_code_hash=phone_code_hash)
        except SessionPasswordNeededError:
            if password is None:
                raise ValueError("password is required")
            await self._c.sign_in(phone=phone, password=password)

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    async def __aenter__(self):
        await self._c.connect()
        return self

    async def logout(self) -> bool:
        res = await self._c.log_out()
        return res


class TC:
    def __init__(self, api_id: int, api_hash: str) -> None:
        self._api_id = api_id
        self._api_hash = api_hash

    def session(self, session_path: str) -> Session:
        return Session(session_path, self._api_id, self._api_hash)


def filter_to_telethon_filter(filter: MessageFilter):
    match filter:
        case MessageFilter.DOC:
            return InputMessagesFilterDocument
        case MessageFilter.PHOTO:
            return InputMessagesFilterPhotos
        case MessageFilter.PHOTO_VIDEO:
            return InputMessagesFilterPhotoVideo
        case _:
            raise ValueError(f"unknown message filter {filter}")


def telethon_message_to_message(msg: Msg) -> Message:
    message_kind = get_message_kind(msg)
    media_info = get_message_media_info(msg, message_kind)
    return Message(
        id=msg.id,
        kind=message_kind,
        text=msg.message,
        media=media_info,
        created_at=msg.date,
    )


def get_message_kind(msg: Msg) -> MessageKind:
    if msg.media is None:
        return MessageKind.TEXT
    elif is_media_doc(msg.media):
        return MessageKind.DOC
    elif is_media_photo(msg.media):
        return MessageKind.PHOTO
    raise ValueError("unknown message kind")


def get_message_media_info(msg: Msg, kind: MessageKind) -> MediaInfo | None:
    if kind == MessageKind.TEXT:
        return None
    elif kind == MessageKind.PHOTO:
        return MediaInfo()
    elif kind == MessageKind.DOC:
        doc: Document = msg.media.document  # type: ignore
        name = get_doc_file_name(doc.attributes)
        if name is None:
            name = ""
        return MediaInfo(name=name, size=doc.size, mime=doc.mime_type)
    raise ValueError(f"unknown message kind: {kind}")


def is_media_photo(media: TypeMessageMedia) -> bool:
    return (
        isinstance(media, MessageMediaPhoto)
        and media.photo is not None
        and isinstance(media.photo, Photo)
    )


def is_media_doc(media: TypeMessageMedia) -> bool:
    return (
        isinstance(media, MessageMediaDocument)
        and media.document is not None
        and isinstance(media.document, Document)
    )


def get_doc_file_name(attrs: list[TypeDocumentAttribute]) -> str | None:
    for attr in attrs:
        if isinstance(attr, DocumentAttributeFilename):
            return attr.file_name
    return None
