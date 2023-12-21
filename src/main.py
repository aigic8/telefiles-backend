from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from pathlib import Path
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteException

from common import load_config
from lib.tc import TC
from router import auth, dialogs, messages
from t import Response

sessions_path = Path("sessions")
sessions_path.mkdir(parents=True, exist_ok=True)

files_path = Path("files")
files_path.mkdir(parents=True, exist_ok=True)

app = FastAPI()
c = load_config()
tc = TC(c.api_id, c.api_hash)


class ErrorResponseData(BaseModel):
    pass


def add_exception_handlers(application: FastAPI):
    @application.exception_handler(StarletteException)
    async def http_exception_handler(req: Request, exc: StarletteException):
        return JSONResponse(
            status_code=exc.status_code,
            content=Response(
                ok=False, error=exc.detail, data=ErrorResponseData()
            ).model_dump(),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(req: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=403,
            content=Response(
                ok=False, error=str(exc), data=ErrorResponseData()
            ).model_dump(),
        )


add_exception_handlers(app)
app.include_router(auth.new_auth_router(tc))
app.include_router(dialogs.new_dialogs_router(tc))
app.include_router(messages.new_messages_router(tc))
