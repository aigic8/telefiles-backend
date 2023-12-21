from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from lib.tc import TC, Session
from router import auth, messages, dialogs
from main import add_exception_handlers


def base_tc_mock():
    tc_mock = mock.create_autospec(TC)
    session_mock = mock.create_autospec(Session)
    tc_mock.session.return_value = session_mock
    session_mock.connect.return_value = None
    session_mock.disconnect.return_value = None
    session_mock.__aenter__.return_value = session_mock
    session_mock.__aexit__.return_value = None
    return tc_mock, session_mock


def client_test(tc_mock: TC):
    app = FastAPI()
    add_exception_handlers(app)
    app.include_router(auth.new_auth_router(tc_mock))
    app.include_router(messages.new_messages_router(tc_mock))
    app.include_router(dialogs.new_dialogs_router(tc_mock))
    return TestClient(app)
