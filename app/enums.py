from strenum import StrEnum


class UserRole(StrEnum):
    OPERATOR = "operator"
    ADMIN = "admin"


class IdleType(StrEnum):
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"


class ScheduledIdleReason(StrEnum):
    REPAIR = "repair"
    NO_ORDERS = "no_orders"
    COIL_REPLACE = "coil_replace"


class UnscheduledIdleReason(StrEnum):
    BREAKDOWN = "breakdown"
    OTHER = "other"


class ProductionLine(StrEnum):
    FISHER = "Фишер"
    BUDMASH = "Будмаш"
