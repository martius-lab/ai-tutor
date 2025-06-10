"""Checks if the user has the required role to access a specific feature."""

from aitutor.auth.state import SessionState


def has_role_at_least(role):
    """
    Check if the user has the required role to access a specific feature.
    """
    user_role = SessionState.user_role
    return user_role is not None and user_role >= role
