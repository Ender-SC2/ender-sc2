from enum import Enum, auto


class Job(Enum):
    UNCLEAR = auto() # DEFAULT
    BIGATTACK = auto()
    CREEPING = auto()
    DEFENDATTACK = auto()
    APPRENTICE = auto()  # drone to build
    WALKER = auto()  # drone to build
    BUILDER = auto()  # drone to build
    INJECTING = auto() # queen
    MIMMINER = auto()
    GASMINER = auto()
    BLOCKER = auto() # hangs around an expansion spot
    BERSERKER = auto() # fights to death
    SLAVE = auto() # follows a broodlord
    WOUNDED = auto()
    SCRATCHED = auto()
    NURSE = auto() # queen
    SPRAYER = auto()
    GUARD = auto() # drone
    TRANSPORTER = auto() # overlordtransport or passenger
    VOLUNTEER = auto()
    TIRED = auto() # waits for energy
    CREEPLORD = auto() # overlord
    ROAMER = auto() # overlord
    HANGER = auto() # overlord
    FREESPINE = auto() # drone, overlordtransport, spinecrawler