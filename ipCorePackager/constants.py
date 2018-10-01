from enum import Enum


class INTF_DIRECTION(Enum):
    """
    Interface direction, used in interface direction resolving process.
    """
    MASTER = 0
    SLAVE = 1
    TRISTATE = 2
    UNKNOWN = 3

    @classmethod
    def asDirection(cls, val):
        return INTF_DIRECTION_asDirecton[val]

    @classmethod
    def opposite(cls, d):
        return INTF_DIRECTION_opposite[d]


class DIRECTION(Enum):
    """
    Used to describe direction of signal.
    """
    IN = 0
    OUT = 1
    INOUT = 2

    @classmethod
    def asIntfDirection(cls, d):
        return DIRECTION_asIntfDirection[d]

    @classmethod
    def opposite(cls, d):
        return DIRECTION_opposite[d]


INTF_DIRECTION_opposite = {
    INTF_DIRECTION.SLAVE: INTF_DIRECTION.MASTER,
    INTF_DIRECTION.MASTER: INTF_DIRECTION.SLAVE,
    INTF_DIRECTION.TRISTATE: INTF_DIRECTION.TRISTATE,
}


INTF_DIRECTION_asDirecton = {
    INTF_DIRECTION.SLAVE: DIRECTION.IN,
    INTF_DIRECTION.MASTER: DIRECTION.OUT,
    INTF_DIRECTION.TRISTATE: DIRECTION.INOUT,
}

INTF_DIRECTION_to_str = {
    INTF_DIRECTION.SLAVE: "SLAVE",
    INTF_DIRECTION.MASTER: "MASTER",
    INTF_DIRECTION.TRISTATE: "TRISTATE",
}

DIRECTION_asIntfDirection = {
    DIRECTION.IN: INTF_DIRECTION.SLAVE,
    DIRECTION.OUT: INTF_DIRECTION.MASTER,
    DIRECTION.INOUT: INTF_DIRECTION.TRISTATE,
}

DIRECTION_to_str = {
    DIRECTION.IN: "IN",
    DIRECTION.OUT: "OUT",
    DIRECTION.INOUT: "INOUT",
}

DIRECTION_opposite = {
    DIRECTION.IN: DIRECTION.OUT,
    DIRECTION.OUT: DIRECTION.IN,
    DIRECTION.INOUT: DIRECTION.INOUT,
}
