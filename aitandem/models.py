"""Module defining database models."""

import reflex as rx
from passlib.context import CryptContext
from sqlmodel import Field, Column, JSON
from typing import Optional, List

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


class Tag(rx.Model, table=True):  # type: ignore
    """Tag model for storing allowed tags."""

    id: Optional[int] = Field(default=None, primary_key=True)  # Automatische ID
    name: str = Field(unique=True, nullable=False, index=True)  # Tag-Name, einzigartig

    def __repr__(self):
        return f"<Tag(name='{self.name}')>"


class Exercise(rx.Model, table=True):  # type: ignore
    """Exercise model for storing exercises."""

    id: Optional[int] = Field(default=None, primary_key=True)  # Automatische ID
    title: str = Field(nullable=False)  # Titel der Übung
    prompt: str = Field(nullable=False)  # Prompt für das LLM
    description: Optional[str] = Field(default=None)  # Beschreibung der Übung
    tags: List[str] = Field(
        sa_column=Column(JSON), default=[]
    )  # Liste der Tags als JSON
    image: Optional[str] = Field(default=None)  # Pfad oder URL zum Bild

    def __repr__(self):
        return f"<Exercise(title='{self.title}', tags={self.tags})>"
