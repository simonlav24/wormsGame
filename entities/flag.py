


import pygame

from common.vector import Vector, dist
from common import GameVariables, point2world, EntityWorm

from entities import PhysObj

class Flag(PhysObj):
    def __init__(self, pos=(0,0)):
        super().__init__(pos)
        self.pos = Vector(pos[0], pos[1])
        self.radius = 3.5
        self.color = (220,0,0)
        self.damp = 0.1
        self.holder: EntityWorm = None
        self.is_gone = False
    
    def step(self):
        super().step()
        if GameVariables().player is not None:
            if not GameVariables().player in GameVariables().get_worms():
                return
            if dist(GameVariables().player.pos, self.pos) < self.radius + GameVariables().player.radius:
                # worm has flag
                self.holder = GameVariables().player
                self.remove_from_game()
                return
    
    def remove_from_game(self) -> None:
        super().remove_from_game()
        self.is_gone = True
    
    def draw(self, win: pygame.Surface):
        pygame.draw.line(win, (51, 51, 0), point2world(self.pos + Vector(0, self.radius)), point2world(self.pos + Vector(0, -3 * self.radius)))
        pygame.draw.rect(win, self.color, (point2world(self.pos + Vector(1, -3 * self.radius)), (self.radius * 2, self.radius * 2)))