from app.core.security import hash_password, verify_password
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, data: UserCreate):

        user = User(
            full_name=data.full_name,
            email=data.email,
            password=hash_password(data.password),
        )

        return self.repository.create(user)

    def authenticate(
        self,
        email: str,
        password: str,
    ):

        user = self.repository.get_by_email(email)

        if not user:
            return None

        if not verify_password(
            password,
            user.password,
        ):
            return None

        return user