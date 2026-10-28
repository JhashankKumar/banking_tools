from app.core.errors import NotFoundError
from app.modules.alerts.service import AlertNotFoundError
from app.modules.cases.service import CaseNotFoundError
from app.modules.users.service import UserNotFoundError


def test_not_found_errors_share_the_404_base() -> None:
    for error in (AlertNotFoundError, CaseNotFoundError, UserNotFoundError):
        assert issubclass(error, NotFoundError)
        assert error.status == 404
