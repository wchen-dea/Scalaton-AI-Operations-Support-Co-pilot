"""Backend role re-check for Teams actions (`tech-arch §8`, `design §4.2`).

Card visibility is not authorization: the operator's role is re-checked at the backend
when a Teams action reaches it. The scaffold models a simple role-to-action policy.
"""

from __future__ import annotations

# Minimal action -> required-role policy. A live deployment binds this to the identity
# provider and the Teams identity-to-role mapping (`design §10`).
_ACTION_POLICY: dict[str, set[str]] = {
    "run_data_quality_check": {"operator", "data_engineer", "bi_analyst"},
    "create_jira_bug": {"data_engineer"},
    "acknowledge_diagnosis": {"operator", "data_engineer", "bi_analyst"},
    "approve_change_request": {"engineering_lead"},
}


def authorize_teams_action(action: str, user_roles: set[str]) -> bool:
    """Return True when a user holding ``user_roles`` may perform ``action``."""

    required = _ACTION_POLICY.get(action)
    if required is None:
        return False
    return bool(required & set(user_roles))
