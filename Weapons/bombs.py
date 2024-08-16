
import pygame
from random import randint

from entities import PhysObj
from common.vector import Vector
from common import GameVariables, point2world
from game.world_effects import boom
from game.visual_effects import Blast

class TNT(PhysObj):
	def __init__(self, pos):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 2
		self.color = (230,57,70)
		self.bounceBeforeDeath = -1
		self.damp = 0.2
		self.timer = 0

	def secondaryStep(self):
		self.timer += 1
		self.stable = False
		if self.timer == GameVariables().fps * 4:
			self.dead = True

	def deathResponse(self):
		boom(self.pos, 40)
		
	def draw(self, win: pygame.Surface):
		pygame.draw.rect(win, self.color, (int(self.pos.x -2) - int(GameVariables().cam_pos[0]),int(self.pos.y -4) - int(GameVariables().cam_pos[1]) , 3,8))
		pygame.draw.line(win, (90,90,90), point2world(self.pos + Vector(-1,-4)), point2world(self.pos + Vector(-1, -5*(GameVariables().fps * 4 - self.timer)/(GameVariables().fps * 4) - 4)), 1)
		if randint(0,10) == 1:
			Blast(self.pos + Vector(-1, -5*(GameVariables().fps * 4 - self.timer)/(GameVariables().fps * 4) - 4), randint(3,6), 150)






