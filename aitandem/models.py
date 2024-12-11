"""Module defining database models."""

import reflex as rx
from passlib.context import CryptContext
from sqlmodel import Field

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(
    rx.Model,
    table=True,  # type: ignore
):
    """User model with bcrypt password hashing."""

    email: str = Field(unique=True, nullable=False, index=True)
    password_hash: str = Field(nullable=False)
    enabled: bool = False
    role: str = "student"

    @staticmethod
    def hash_password(secret: str) -> str:
        """Hash the secret using bcrypt.

        Args:
            secret: The password to hash.

        Returns:
            The hashed password.
        """
        return pwd_context.hash(secret)

    def verify(self, secret: str) -> bool:
        """Validate the user's password.

        Args:
            secret: The password to check.

        Returns:
            True if the hashed secret matches this user's password_hash.
        """
        return pwd_context.verify(
            secret,
            self.password_hash,
        )


class Tag(rx.Model):
    """Database model for storing allowed tags."""

    tag: str = rx.var(unique=True)


class Exercise(rx.Model):
    """Database model for storing exercise informations."""

    exeID: int = rx.var(unique=True)
    title: str
    prompt: str
    tags: list[str]
    image: str
