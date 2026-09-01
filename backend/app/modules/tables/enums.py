from enum import Enum


class TableStatus(str, Enum):

    FREE = "FREE"

    RESERVED = "RESERVED"

    WAITING_ORDER = "WAITING_ORDER"

    ORDERING = "ORDERING"

    IN_KITCHEN = "IN_KITCHEN"

    READY = "READY"

    EATING = "EATING"

    WAITING_PAYMENT = "WAITING_PAYMENT"

    PAID = "PAID"

    CLOSED = "CLOSED"

    BLOCKED = "BLOCKED"