
import pygame
from random import randint

from GameVariables import GameVariables, point2world
from Effects import Blast
from vector import *
import globals

class WormTool:
    def __init__(self):
        self.is_done: bool = False

    def step(self):
        pass

    def draw(self):
        pass

    def apply_force(self):
        pass

class JetPack(WormTool):
    def __init__(self, worm: 'physical'):
        super().__init__()
        self.worm = worm
        self.fuel = 100

    def apply_force(self):
        if self.fuel <= 0:
            self.is_done = True
            return
        if pygame.key.get_pressed()[pygame.K_UP]:
            self.worm.acc.y -= GameVariables().physics.global_gravity + 0.5
            self.fuel -= 0.5
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            self.worm.acc.x -= 0.5
            self.fuel -= 0.5
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.worm.acc.x += 0.5
            self.fuel -= 0.5
    
    def step(self):
        self.worm.vel.limit(5)
        if pygame.key.get_pressed()[pygame.K_UP]:
            Blast(self.worm.pos + Vector(0, self.worm.radius * 1.5) + vectorUnitRandom() * 2, randint(5,8), 80)
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            Blast(self.worm.pos + Vector(self.worm.radius * 1.5, 0) + vectorUnitRandom() * 2, randint(5,8), 80)
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            Blast(self.worm.pos + Vector(-self.worm.radius * 1.5, 0) + vectorUnitRandom() * 2, randint(5,8), 80)

    def draw(self, win):
        globals.weapon_manager.blitWeaponSprite(win, point2world(self.worm.pos - Vector(8,8)), "jet pack")
        value = 20 * (self.fuel/100)
        if value < 1:
            value = 1
        pygame.draw.rect(win, (220,220,220),(point2world(self.worm.pos + Vector(-10, -25)), (20,3)))
        pygame.draw.rect(win, (0,0,220),(point2world(self.worm.pos + Vector(-10, -25)), (int(value),3)))