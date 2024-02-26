from strenum import StrEnum


class UserRole(StrEnum):
    OPERATOR = "operator"
    ADMIN = "admin"


class IdleType(StrEnum):
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"
