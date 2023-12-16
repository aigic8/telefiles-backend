from typing import Annotated
import uuid
from fastapi import APIRouter, Cookie
from fastapi.responses import FileResponse
from pydantic import BaseModel
import aiofiles

from src.common import validate_session
from src.lib.tc import TC
from src.t import Message, MessageFilter, Response


class GetMessagesResponseData(BaseModel):
    messages: list[Message]


class DownloadMessageResponseData(BaseModel):
    message: Message


def new_messages_router(tc: TC):
    r = APIRouter()

    @r.get("/messages")
    async def get_messages(
        chat: int,
        after_id: int | None = None,
        filter: MessageFilter = MessageFilter.DOC,
        limit: int = 30,
        session: Annotated[str | None, Cookie()] = None,
    ) -> Response[GetMessagesResponseData]:
        session_path = validate_session(session)
        async with tc.session(session_path) as s:
            messages = await s.get_messages(
                chat_id=chat, limit=limit, filter=filter, offset_id=after_id
            )
            return Response(data=GetMessagesResponseData(messages=messages))

    @r.get("/message/download")
    async def download_message(
        chat: int, message_id: int, session: Annotated[str | None, Cookie()] = None
    ):
        session_path = validate_session(session)
        file_path = ""
        async with tc.session(session_path) as s:
            stream, info = await s.download_file(chat_id=chat, message_id=message_id)
            file_path = f"files/{str(uuid.uuid4())}"
            async with aiofiles.open(file_path, "wb") as fd:
                async for chunk in stream:
                    await fd.write(chunk)

        headers = {"Content-Type": info.mime}
        if info.name is not None:
            headers["Content-Disposition"] = f'attachment; filename="{info.name}"'
        if info.size is not None:
            headers["Content-Length"] = f"{info.size}"
        resp = FileResponse(file_path, headers=headers)
        return resp

    return r
