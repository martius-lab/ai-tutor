"""Module defining database models."""

import reflex as rx  # type: ignore
from passlib.context import CryptContext  # type: ignore
from sqlmodel import Field, Relationship  # type: ignore

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


class Tag(rx.Model, table=True):  # type: ignore  # Tag-Tabelle
    """Database model for storing allowed tags."""

    id: int = Field(primary_key=True)
    name: str = Field(unique=True, nullable=False)


class Exercise(rx.Model, table=True):  # type: ignore  # Exercise-Tabelle
    """Database model for storing exercise information."""

    id: int = Field(primary_key=True)
    exeID: int = Field(unique=True)
    title: str = Field(nullable=False)
    prompt: str = Field(nullable=False)
    tags: list[Tag] = Relationship(back_populates="exercises")  # Many-to-Many
    image: str = Field(nullable=False)
