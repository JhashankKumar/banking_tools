from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.users.models import Role
from tests.factories import assert_error, signed_in


def test_signed_in_returns_headers_for_a_new_user_of_that_role(
    client: TestClient, db_session: Session
) -> None:
    headers = signed_in(client, db_session, Role.AUDITOR)

    me = client.get("/api/v1/auth/me", headers=headers).json()["data"]
    assert (me["username"], me["role"]) == ("auditor.one", "auditor")


def test_assert_error_checks_status_and_code(client: TestClient) -> None:
    response = client.get("/api/v1/cases")

    assert_error(response, 401, "AUTH_NOT_AUTHENTICATED")
