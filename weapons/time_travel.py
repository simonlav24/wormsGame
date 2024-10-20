
from dataclasses import dataclass
from typing import Tuple, List
from enum import Enum

import pygame

from common import GameVariables, RIGHT, point2world
from common.vector import tup2vec, vectorCopy

class TimeState(Enum):
    RECORD = 0
    PLAY = 1
    END = 2


@dataclass
class TimeRecord:
    pos: Tuple[int, int]
    facing: int



class TimeTravel:
    def __init__(self):
        GameVariables().register_non_physical(self)
        GameVariables().register_fire_observer(self)
        self.worm = GameVariables().player
        self.record: List[TimeRecord] = []
        self.current_record: TimeRecord = None
        self.state = TimeState.RECORD
        self.fire_kwargs = None
        self.initial_pos = vectorCopy(self.worm.pos)
        self.fired = False
    
    def remove_from_game(self):
        GameVariables().unregister_non_physical(self)
        GameVariables().unregister_fire_observer(self)
    

    def end_record(self):
        self.state = TimeState.PLAY
        self.current_record = self.record.pop(0)
        self.worm.vel *= 0
        self.worm.pos = self.initial_pos

    def on_fire(self, **kwargs) -> bool:
        if self.fired:
            return False
        self.fired = True
        self.fire_kwargs = kwargs
        self.end_record()
        return True

    def fire(self):
        weapon_func = self.fire_kwargs['weapon_func']
        weapon_func(**self.fire_kwargs)

    def step(self):
        if self.state == TimeState.RECORD:
            self.record.append(TimeRecord(self.worm.pos.vec2tupint(), self.worm.facing))
        
        elif self.state == TimeState.PLAY:
            self.current_record = self.record.pop(0)

            if len(self.record) == 0:
                self.state = TimeState.END
                self.fire()
                self.current_record = None
        
        elif self.state == TimeState.END:
            self.remove_from_game()

    def draw(self, win: pygame.Surface):
        if self.state == TimeState.PLAY:
            pygame.draw.circle(win, self.worm.color, point2world(self.current_record.pos), self.worm.radius + 1)
            surf = pygame.transform.flip(self.worm.surf, self.current_record.facing == RIGHT, False)
            win.blit(surf, point2world(tup2vec(self.current_record.pos) - tup2vec(surf.get_size()) // 2))


