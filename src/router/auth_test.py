import uuid

from router import auth
from testutils import base_tc_mock, client_test
from t import Response


class TestAuth:
    def test_send_code_normal(self):
        tc_mock, session_mock = base_tc_mock()
        phone_code_hash = str(uuid.uuid4())
        session_mock.send_code.return_value = phone_code_hash

        client = client_test(tc_mock)
        response = client.post("/send_code", json={"phone": "+989999999999"})
        assert response.status_code == 200
        resp_data = response.json()
        expected_data = Response(
            data=auth.SendCodeResponseData(phone_code_hash=phone_code_hash)
        ).model_dump()
        assert resp_data == expected_data

    def test_send_code_bad_number_format(self):
        tc_mock, session_mock = base_tc_mock()
        phone_code_hash = str(uuid.uuid4())
        session_mock.send_code.return_value = phone_code_hash

        client = client_test(tc_mock)
        response = client.post("/send_code", json={"phone": "bad_phone_number"})
        assert response.status_code == 403
        resp_data = response.json()
        assert not resp_data["ok"]

    def test_login_normal(self):
        pass

    def test_login_no_password_but_required(self):
        pass

    def test_login_no_code(self):
        pass
