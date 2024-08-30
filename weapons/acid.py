from random import uniform, randint, choice
from math import pi, sin, cos

import pygame


from common import GameVariables, point2world, LEFT, RIGHT, blit_weapon_sprite
from common.vector import *

from game.map_manager import MapManager, SKY
from game.visual_effects import SmokeParticles
from game.world_effects import boom
from entities import PhysObj, Worm
from weapons.fire_weapons import PetrolBomb

def square_collision(pos1, pos2, rad1, rad2) -> bool:
	return True if pos1.x < pos2.x + rad2 * 2 and pos1.x + rad1 * 2 > pos2.x and pos1.y < pos2.y + rad2 * 2 and pos1.y + rad1 * 2 > pos2.y else False

class Acid(PhysObj):
	def __init__(self, pos, vel):
		super().__init__(pos)
		self.pos = vectorCopy(pos)
		self.vel = vectorCopy(vel)
		self.life = randint(70, 170)
		self.radius = 2
		self.damp = 0
		self.is_wind_affected = 0.5
		self.inGround = False
		self.is_worm_collider = True
		self.color = (200,255,200)
		self.damageCooldown = 0
	
	def on_collision(self, ppos):
		self.inGround = True
	
	def secondaryStep(self):
		if self.inGround:
			pygame.draw.circle(MapManager().game_map, SKY, self.pos + Vector(0, 1), self.radius + 2)
			pygame.draw.circle(MapManager().ground_map, SKY, self.pos + Vector(0, 1), self.radius + 2)
			self.pos.x += choice([LEFT, RIGHT])
		self.life -= 1
		if self.life == 50:
			self.radius -= 1
		if self.life <= 0:
			self.dead = True
			
		if self.damageCooldown != 0:
			self.damageCooldown -= 1
		else:
			for worm in GameVariables().get_worms():
				if square_collision(self.pos, worm.pos, self.radius, worm.radius):
					worm.damage(randint(0,1))
					self.damageCooldown = 30
		self.inGround = False
		if randint(0,50) < 1:
			SmokeParticles._sp.addSmoke(self.pos, color=(200,255,200))
		GameVariables().game_distable()
	
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, self.color, point2world(self.pos + Vector(0,1)), self.radius + 1)

class AcidBottle(PetrolBomb):
	def __init__(self, pos, direction, energy):
		super().__init__(pos, direction, energy)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (200,255,200)
		self.bounce_before_death = 1
		self.damp = 0.5
		self.angle = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "acid bottle")
	
	def secondaryStep(self):
		self.angle -= self.vel.x*4
	
	def death_response(self):
		boom(self.pos, 10)
		for i in range(40):
			s = Acid(self.pos, Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,2))
	
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
