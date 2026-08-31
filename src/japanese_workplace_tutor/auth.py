"""Local demo-account registration and authentication."""

from dataclasses import dataclass
import unicodedata

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import User

MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 64
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128
INVALID_LOGIN_MESSAGE = "Invalid username or password."


class RegistrationError(ValueError):
    pass


class AuthenticationError(ValueError):
    pass


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    username: str


def normalize_username(username: str) -> tuple[str, str]:
    display_name = unicodedata.normalize("NFKC", username).strip()
    if not MIN_USERNAME_LENGTH <= len(display_name) <= MAX_USERNAME_LENGTH:
        raise RegistrationError(
            f"Username must be {MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} characters."
        )
    if any(unicodedata.category(character).startswith("C") for character in display_name):
        raise RegistrationError("Username cannot contain control characters.")
    return display_name, display_name.casefold()


def validate_password(password: str) -> None:
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise RegistrationError(
            f"Password must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters."
        )


class AuthenticationService:
    def __init__(self, engine: Engine, password_hasher: PasswordHasher | None = None) -> None:
        self._engine = engine
        self._password_hasher = password_hasher or PasswordHasher()

    def register(self, username: str, password: str) -> AuthenticatedUser:
        display_name, normalized_username = normalize_username(username)
        validate_password(password)
        user = User(
            username=display_name,
            normalized_username=normalized_username,
            password_hash=self._password_hasher.hash(password),
        )

        try:
            with Session(self._engine) as session:
                session.add(user)
                session.commit()
                session.refresh(user)
                return AuthenticatedUser(id=user.id, username=user.username)
        except IntegrityError as error:
            raise RegistrationError("That username is already registered.") from error

    def authenticate(self, username: str, password: str) -> AuthenticatedUser:
        try:
            _, normalized_username = normalize_username(username)
        except RegistrationError as error:
            raise AuthenticationError(INVALID_LOGIN_MESSAGE) from error
        if len(password) > MAX_PASSWORD_LENGTH:
            raise AuthenticationError(INVALID_LOGIN_MESSAGE)

        with Session(self._engine) as session:
            user = session.scalar(
                select(User).where(User.normalized_username == normalized_username)
            )
            if user is None:
                raise AuthenticationError(INVALID_LOGIN_MESSAGE)
            try:
                self._password_hasher.verify(user.password_hash, password)
            except VerificationError as error:
                raise AuthenticationError(INVALID_LOGIN_MESSAGE) from error

            if self._password_hasher.check_needs_rehash(user.password_hash):
                user.password_hash = self._password_hasher.hash(password)
                session.commit()
            return AuthenticatedUser(id=user.id, username=user.username)