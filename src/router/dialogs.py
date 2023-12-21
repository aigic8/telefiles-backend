from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Cookie
from pydantic import BaseModel


from common import validate_session
from lib.tc import TC
from t import Dialog, Message, Response


class GetDialogsResponseData(BaseModel):
    dialogs: list[Dialog]


class GetMessagesResponseData(BaseModel):
    messages: list[Message]


def new_dialogs_router(tc: TC):
    r = APIRouter()

    @r.get("/dialogs")
    async def get_dialogs(
        offset_date: str | None = None,
        limit: int = 30,
        session: Annotated[str | None, Cookie()] = None,
    ) -> Response[GetDialogsResponseData]:
        session_path = validate_session(session)
        async with tc.session(session_path) as s:
            offset_dt = parse_optional_date(offset_date)
            dialogs = await s.get_dialogs(limit=limit, offset_date=offset_dt)
            return Response(data=GetDialogsResponseData(dialogs=dialogs))

    return r


def parse_optional_date(date_str: str | None) -> datetime | None:
    if date_str is not None:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    return None
