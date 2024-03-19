from strenum import StrEnum


class UserRole(StrEnum):
    OPERATOR = "operator"
    ADMIN = "admin"


class IdleType(StrEnum):
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"


class IdleReason(StrEnum):
    # Sheduled Idle Reasons
    REPAIR = "repair"
    NO_ORDERS = "no_orders"
    COIL_REPLACE = "coil_replace"
    # Unsheduled Idle Reasons
    BREAKDOWN = "breakdown"
    OTHER = "other"


class LineName(StrEnum):
    FISHER = "Фишер"
    BUDMASH = "Будмаш"
