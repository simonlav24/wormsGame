
from enum import Enum

from common.vector import Vector
from common import GameVariables

from entities import PhysObj

class AutonomousState(Enum):
    IDLE = 0
    ENGAGING = 1

class AutonomousObject(PhysObj):
    def __init__(self, pos: Vector, **kwargs):
        super().__init__(pos, **kwargs)
        self.type = type
        self.state = AutonomousState.IDLE
        GameVariables().register_autonomous(self)

    def engage(self) -> bool:
        self.state = AutonomousState.ENGAGING
        return True
    
    def done(self) -> None:
        self.state = AutonomousState.IDLE

    def remove_from_game(self) -> None:
        super().remove_from_game()
        GameVariables().unregister_autonomous(self)