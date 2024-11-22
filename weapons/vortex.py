
from enum import Enum
from random import randint

import pygame

from common import GameVariables, point2world, GameGlobals
from common.vector import *

from weapons.grenades import Grenade
from game.sfx import Sfx, SfxIndex


class Vortex():
    vortexRadius = 180
    def __init__(self, pos):
        GameVariables().register_non_physical(self)
        self.pos = Vector(pos[0], pos[1])
        self.rot = 0
        self.inhale = True
        self.is_boom_affected = False
        Sfx().play(SfxIndex.VORTEX_IN)

    def step(self):
        GameVariables().game_distable()
        if self.inhale:
            self.rot += 0.001
            if self.rot > 0.1:
                self.rot = 0.1
                self.inhale = False
                Sfx().play(SfxIndex.VORTEX_OUT)
        else:
            self.rot -= 0.001
        
        if self.inhale:
            for worm in GameVariables().get_physicals():
                if distus(self.pos, worm.pos) < Vortex.vortexRadius * Vortex.vortexRadius:
                    worm.acc += (self.pos - worm.pos) * 1/dist(self.pos, worm.pos)
                    if randint(0,20) == 1:
                        worm.vel.y -= 2
                if worm in GameVariables().get_worms() and dist(self.pos, worm.pos) < Vortex.vortexRadius/2:
                    if randint(0,20) == 1:
                        worm.damage(randint(1,8))
        else:
            for worm in GameVariables().get_physicals():
                if distus(self.pos, worm.pos) < Vortex.vortexRadius * Vortex.vortexRadius:
                    worm.acc -= (self.pos - worm.pos) * 1/dist(self.pos, worm.pos)
            
        if not self.inhale and self.rot < 0:
            GameVariables().unregister_non_physical(self)

    def draw(self, win: pygame.Surface):
        width = 50
        arr = []
        halfwidth = width//2
        for x in range(int(self.pos.x) - halfwidth, int(self.pos.x) + halfwidth):
            for y in range(int(self.pos.y) - halfwidth, int(self.pos.y) + halfwidth):
                if distus(Vector(x,y), self.pos) > halfwidth * halfwidth:
                    continue
                rot = (dist(Vector(x,y), self.pos) - halfwidth) * self.rot
                direction = Vector(x,y) - self.pos
                direction.rotate(rot)
                getAt = point2world(self.pos + direction)
                if getAt[0] < 0 or getAt[0] >= GameGlobals().win_width or getAt[1] < 0 or getAt[1] >= GameGlobals().win_height:
                    arr.append((0,0,0))
                else:
                    pixelColor = win.get_at(getAt)
                    arr.append(pixelColor)
        for x in range(int(self.pos.x) - halfwidth, int(self.pos.x) + halfwidth):
            for y in range(int(self.pos.y) - halfwidth, int(self.pos.y) + halfwidth):
                if distus(Vector(x,y), self.pos) > halfwidth * halfwidth:
                    continue
                
                win.set_at(point2world((x,y)), arr.pop(0))


class VortexGrenade(Grenade):
    def __init__(self, pos, direction, energy):
        super().__init__(pos, direction, energy, "vortex grenade")
        self.radius = 3
        self.color = (25, 102, 102)
        self.damp = 0.5

    def death_response(self):
        Vortex(self.pos)