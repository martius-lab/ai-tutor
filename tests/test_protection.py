from types import SimpleNamespace

import pytest

from aitutor.auth.protection import state_require_login, state_require_permission
from aitutor.models import GlobalPermission


def fake_state(*, authenticated=True, permissions=()):
    return SimpleNamespace(
        is_authenticated=authenticated, global_permissions=list(permissions)
    )


def make_handler(decorator):
    @decorator
    def handler(self, value):
        return value

    return handler


@pytest.mark.parametrize(
    ("authenticated", "permissions", "allowed"),
    [
        (True, [GlobalPermission.MAINTAINER], True),
        (True, [GlobalPermission.ADMIN], True),
        (True, [GlobalPermission.LECTURER], False),
        (True, [], False),
        (False, [GlobalPermission.MAINTAINER], False),
        (False, [GlobalPermission.ADMIN], False),
    ],
)
def test_state_require_permission(authenticated, permissions, allowed):
    state = fake_state(authenticated=authenticated, permissions=permissions)
    expected = "ok" if allowed else None

    for perms in (GlobalPermission.MAINTAINER, [GlobalPermission.MAINTAINER]):
        handler = make_handler(state_require_permission(perms))
        assert handler(state, "ok") == expected


def test_state_require_permission_any_of_list():
    handler = make_handler(
        state_require_permission(
            [GlobalPermission.LECTURER, GlobalPermission.MAINTAINER]
        )
    )
    state = fake_state(permissions=[GlobalPermission.LECTURER])

    assert handler(state, "ok") == "ok"


@pytest.mark.parametrize(("authenticated", "expected"), [(True, "ok"), (False, None)])
def test_state_require_login(authenticated, expected):
    handler = make_handler(state_require_login())

    assert handler(fake_state(authenticated=authenticated), "ok") == expected
