from typing import Annotated
from fastapi import APIRouter, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_extra_types import phone_numbers
import uuid

from common import validate_session
from lib.tc import TC
from t import Response


class SendCodeRequestBody(BaseModel):
    phone: phone_numbers.PhoneNumber


class SendCodeResponseData(BaseModel):
    phone_code_hash: str


class LoginRequestBody(BaseModel):
    phone: str
    phone_code_hash: str
    code: int
    password: str | None = Field(default=None)


class LoginResponseData(BaseModel):
    pass


class LogoutResponseData(BaseModel):
    pass


def new_auth_router(tc: TC):
    r = APIRouter()

    @r.post("/send_code")
    async def send_code(b: SendCodeRequestBody):
        session = str(uuid.uuid4())
        session_path = f"sessions/{session}"
        async with tc.session(session_path) as s:
            phone_code_hash = await s.send_code(b.phone)
            resp_content = Response(
                data=SendCodeResponseData(phone_code_hash=phone_code_hash)
            ).model_dump()
            resp = JSONResponse(resp_content)
            resp.set_cookie("session", session, samesite="strict", httponly=True)
            return resp

    @r.post("/login")
    async def login(
        b: LoginRequestBody, session: Annotated[str | None, Cookie()] = None
    ) -> Response[LoginResponseData]:
        session_path = validate_session(session)
        async with tc.session(session_path) as s:
            await s.login(
                phone=b.phone,
                phone_code_hash=b.phone_code_hash,
                code=b.code,
                password=b.password,
            )
        return Response(data=LoginResponseData())

    @r.post("/logout")
    async def logout(
        session: Annotated[str | None, Cookie()] = None,
    ) -> Response[LogoutResponseData]:
        session_path = validate_session(session)
        async with tc.session(session_path) as s:
            await s.logout()
        return Response(data=LogoutResponseData())

    return r
