from enum import Enum, auto


class Job(Enum):
    UNCLEAR = auto()  # DEFAULT
    BIGATTACK = auto()
    CREEPER = auto()
    DEFENDATTACK = auto()
    WALKER = auto()  # drone to build
    BUILDER = auto()  # drone to build
    INJECTER = auto()  # queen
    MIMMINER = auto()
    GASMINER = auto()
    BERSERKER = auto()  # fights to death
    HOLY = auto()  # do not touch
    SLAVE = auto()  # follows a broodlord
    WOUNDED = auto()
    SCRATCHED = auto()
    NURSE = auto()  # queen
    SPRAYER = auto()
    GUARD = auto()  # drone
    TRANSPORTER = auto()  # overlordtransport or passenger
    VOLUNTEER = auto()
    TIRED = auto()  # waits for energy
    CREEPLORD = auto()  # overlord
    ROAMER = auto()  # overlord
    HANGER = auto()  # overlord
    FREESPINE = auto()  # drone, overlordtransport, spinecrawler
    SPY = auto()  # changeling
    SCOUT = auto()
    SACRIFICIAL_SCOUT = auto()
    NYDUSUSER = auto()
