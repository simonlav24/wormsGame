
from random import randint

import pygame

from common.vector import *
from common import GameVariables, point2world, sprites

from game.map_manager import MapManager, GRD
from game.visual_effects import splash
from entities import PhysObj
from entities.props import PetrolCan
from entities.shooting_target import ShootingTarget

class LongBow:
    _sleep = False
    def __init__(self, pos, direction, sleep=False):
        GameVariables().register_non_physical(self)
        self.pos = vectorCopy(pos)
        self.direction = direction
        self.vel = direction.normalize() * 20
        self.stuck = None
        self.color = (112, 74, 37)
        self.ignore = None
        self.sleep = sleep
        self.radius = 1
        self.triangle = [Vector(0,3), Vector(6,0), Vector(0,-3)]
        for vec in self.triangle:
            vec.rotate(self.direction.getAngle())
        self.timer = 0
    
    def destroy(self):
        GameVariables().unregister_non_physical(self)
    
    def step(self):
        self.timer += 1
        if self.timer >= GameVariables().fps * 3:
            self.vel.y += GameVariables().physics.global_gravity
        if not self.stuck:
            ppos = self.pos + self.vel
            iterations = 15
            for t in range(iterations):
                value = t/iterations
                testPos = (self.pos * value) + (ppos * (1-value))
                # check cans collision:
                for can in PetrolCan._cans:
                    if dist(testPos, can.pos) < can.radius + 1:
                        can.damage(10)
                        self.destroy()
                        return
                # check worm collision
                for worm in PhysObj._worms:
                    if worm == self.ignore:
                        continue
                    if dist(testPos, worm.pos) < worm.radius + 1:
                        self.wormCollision(worm)
                        return
                # check target collision:
                for target in ShootingTarget._reg:
                    if dist(testPos, target.pos) < target.radius:
                        target.explode()
                        self.destroy()
                        return
                # check MapManager().game_map collision
                if MapManager().is_on_map(testPos.vec2tupint()):
                    if MapManager().is_ground_at(testPos.vec2tupint()):
                        self.stuck = vectorCopy(testPos)
                if self.pos.y < 0:
                    self.destroy()
                    return
                if self.pos.y > MapManager().game_map.get_height() - GameVariables().water_level:
                    splash(self.pos, self.vel)
                    self.destroy()
                    return
            self.pos = ppos
        if self.stuck:
            self.stamp()
        self.secondaryStep()
    
    def wormCollision(self, worm):
        worm.vel += self.direction*4
        worm.vel.y -= 2
        worm.damage(randint(10, 20) if self.sleep else randint(15,25))
        GameVariables().cam_track = worm
        if self.sleep:
            worm.sleep = True
        self.destroy()
        MapManager().stain(worm.pos, sprites.blood, sprites.blood.get_size(), False)
    
    def secondaryStep(self):
        pass
    
    def stamp(self):
        self.pos = self.stuck
            
        points = [(self.pos - self.direction * 10 + i).vec2tupint() for i in self.triangle]
        pygame.draw.polygon(MapManager().ground_map, (230,235,240), points)
        pygame.draw.polygon(MapManager().game_map, GRD, points)
        
        pygame.draw.line(MapManager().game_map, GRD, self.pos.vec2tupint(), (self.pos - self.direction*8).vec2tupint(), 3)
        pygame.draw.line(MapManager().ground_map, self.color, self.pos.vec2tupint(), (self.pos - self.direction*8).vec2tupint(), 3)
        
        self.destroy()
    
    def draw(self, win: pygame.Surface):
        points = [point2world(self.pos - self.direction * 10 + i) for i in self.triangle]
        pygame.draw.polygon(win, (230,235,240), points)
    
        pygame.draw.line(win, self.color, point2world(self.pos), point2world(self.pos - self.direction*8), 3)
        
        points = [point2world(self.pos + i) for i in self.triangle]
        pygame.draw.polygon(win, (230,235,240), points)