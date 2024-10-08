from schema import Schema

from shared.authentication.password import PasswordService
from user.models import User


class TestUser:
    def test_user_sign_up(self, client, test_session):
        # given

        # when
        response = client.post(
            "/users/sign-up",
            json={"username": "test", "password": "test-pw"}
        )

        # then
        assert response.status_code == 201
        assert Schema(
            {
                "id": int,
                "username": "test",
                "created_at": str,
            }
        ).validate(response.json())

        user = test_session.query(User).filter(User.username == "test").first()

        assert user
        assert PasswordService().check_password(plain_text="test-pw", hashed_password=user.password_hash)
