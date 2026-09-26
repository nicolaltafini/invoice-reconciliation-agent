from dataclasses import dataclass

from reconciliation.approvals import Role


@dataclass(frozen=True)
class DemoUser:
    id: str
    name: str
    role: Role


DEMO_USERS: dict[str, DemoUser] = {
    user.id: user
    for user in [
        DemoUser("giulia", "Giulia Rossi", Role.VIEWER),
        DemoUser("marco", "Marco Bianchi", Role.OPERATOR),
    ]
}