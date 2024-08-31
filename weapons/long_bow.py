
from random import randint, uniform
from math import degrees, pi, cos, sin

import pygame

from common.vector import *
from common import GameVariables, point2world, sprites, blit_weapon_sprite, EntityWorm

from game.map_manager import MapManager, GRD
from game.visual_effects import splash, Frost, DropLet, Blast
from game.world_effects import boom
from entities import Fire
from entities.props import PetrolCan
from entities.shooting_target import ShootingTarget

class LongBow:
    _sleep = False
    def __init__(self, pos: Vector, direction: Vector, worm_ignore: EntityWorm=None):
        GameVariables().register_non_physical(self)
        self.pos = vectorCopy(pos)
        self.direction = direction
        self.vel = direction.normalize() * 20
        self.stuck = None
        self.color = (112, 74, 37)
        self.ignore = worm_ignore
        self.sleep = False
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
                for worm in GameVariables().get_worms():
                    if worm == self.ignore:
                        continue
                    if dist(testPos, worm.pos) < worm.radius + 1:
                        self.worm_collision(worm)
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
    
    def worm_collision(self, worm: EntityWorm):
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


class Icicle(LongBow):
	def __init__(self, pos, direction):
		GameVariables().register_non_physical(self)
		self.pos = vectorCopy(pos)
		self.direction = direction
		self.vel = direction.normalize() * 20
		self.stuck = None
		self.color = (112, 74, 255)
		self.ignore = None
		self.radius = 1
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "icicle")
		self.timer = 0
	
	def secondaryStep(self):
		if randint(0,5) == 0:
			Frost(self.pos + vectorUnitRandom() * 3)
	
	def destroy(self):
		GameVariables().unregister_non_physical(self)
		for _ in range(8):
			DropLet(self.pos, Vector())
	
	def stamp(self):
		self.pos = self.stuck
		Frost(self.stuck)
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
		MapManager().ground_map.blit(surf, self.pos - tup2vec(surf.get_size())//2)
		for y in range(self.surf.get_height()):
			for x in range(self.surf.get_width()):
				if not self.surf.get_at((x,y))[3] < 255:
					self.surf.set_at((x,y), GRD)
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
		MapManager().game_map.blit(surf, self.pos - tup2vec(surf.get_size())//2)
		
		self.destroy()
	
	def worm_collision(self, worm: EntityWorm):
		for i in range(8):
			pos = worm.pos + vectorFromAngle(2 * pi * i / 8, worm.radius + 1)
			Frost(pos)
		worm.vel += self.direction*4
		worm.vel.y -= 2
		worm.damage(randint(20,30))
		GameVariables().cam_track = worm
		for i in range(8):
			DropLet(self.pos, Vector())
		self.destroy()
	
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
		win.blit(surf, point2world(self.pos - tup2vec(surf.get_size())//2))


class FireBall(LongBow):
	def __init__(self, pos, direction):
		GameVariables().register_non_physical(self)
		self.radius = 1
		self.pos = vectorCopy(pos)
		self.direction = direction
		self.vel = direction.normalize() * 20
		self.stuck = None
		self.color = (112, 74, 255)
		self.ignore = None
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "fire ball")
		self.timer = 0
	
	def secondaryStep(self):
		if randint(0,2) == 0:
			Fire(self.pos)
		Blast(self.pos + vectorUnitRandom()*2 - 10 * normalize(self.vel), randint(5,8), 30, 3)
	
	def destroy(self):
		if self.stuck:
			boomPos = self.stuck
		else:
			boomPos = self.pos
		boom(boomPos, 15)
		for i in range(40):
			s = Fire(boomPos, 5)
			s.vel = Vector(cos(2 * pi * i / 40), sin(2 * pi * i / 40)) * uniform(1.3, 2)
		GameVariables().unregister_non_physical(self)
	
	def stamp(self):
		self.destroy()
	
	def worm_collision(self, worm):
		self.stuck = worm.pos + vectorUnitRandom() * 2
		self.destroy()
	
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
		win.blit(surf, point2world(self.pos - tup2vec(surf.get_size())//2))