
from random import randint, choice

import pygame

from common import GameVariables, sprites, point2world, EntityWorm
from common.vector import *

from game.visual_effects import FloatingText
from game.map_manager import MapManager, GRD
from weapons.weapon_manager import WeaponManager
from entities.props import ExplodingProp


class Deployable(ExplodingProp):
	def __init__(self, pos = (0,0)):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.radius = 5
		self.damp = 0.01
		self.health = 5
		self.is_fall_affected = False
		self.is_wind_affected = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)

	def draw(self, win: pygame.Surface):
		win.blit(self.surf , point2world(self.pos - tup2vec(self.surf.get_size())/2))

	def step(self):
		super().step()
		if distus(GameVariables().player.pos, self.pos) < (self.radius + GameVariables().player.radius + 5) * (self.radius + GameVariables().player.radius + 5)\
			and not GameVariables().player.health <= 0:
			self.effect(GameVariables().player)
			self.remove_from_game()
			return
		if self.health <= 0:
			self.death_response()
			self.remove_from_game()

	def effect(self, worm: EntityWorm):
		...

class HealthPack(Deployable):
	def __init__(self, pos = (0,0)):
		super().__init__(pos)
		self.surf.blit(sprites.sprite_atlas, (0,0), (112, 96, 16, 16))

	def effect(self, worm: EntityWorm):
		worm.heal(50)
		FloatingText(self.pos, "+50", (0,230,0))

class UtilityPack(Deployable):
	def __init__(self, pos = (0,0)):
		super().__init__(pos)
		self.box = choice(["moon gravity", "double damage", "aim aid", "teleport", "switch worms", "time travel", "jet pack", "tool set", "travel kit"])
		self.surf.blit(sprites.sprite_atlas, (0,0), (96, 96, 16, 16))

	def effect(self, worm: EntityWorm):
		FloatingText(self.pos, self.box, (0,200,200))
		if self.box == "tool set":
			worm.team.ammo(WeaponManager()["portal gun"], 1)
			worm.team.ammo(WeaponManager()["ender pearl"], 5)
			worm.team.ammo(WeaponManager()["trampoline"], 3)
			return
		if self.box == "travel kit":
			worm.team.ammo(WeaponManager()["rope"], 3)
			worm.team.ammo(WeaponManager()["parachute"], 3)
			return
		worm.team.ammo(WeaponManager()[self.box], 1)

class WeaponPack(Deployable):
	def __init__(self, pos = (0,0)):
		super().__init__(pos)
		weaponsInBox = ["banana", "holy grenade", "earthquake", "gemino mine", "sentry turret", "bee hive", "vortex grenade", "chilli pepper", "covid 19", "raging bull", "electro boom", "pokeball", "green shell", "guided missile", "fireworks"]
		if GameVariables().initial_variables.allow_air_strikes:
			weaponsInBox .append("mine strike")
		self.box = WeaponManager()[choice(weaponsInBox)]
		self.surf.blit(sprites.sprite_atlas, (0,0), (80, 96, 16, 16))

	def effect(self, worm: EntityWorm):
		FloatingText(self.pos, self.box, (0,200,200))
		worm.team.ammo(self.box, 1)

def deploy_pack(pack):
	x = 0
	ymin = 20
	goodPlace = False #1 has MapManager().ground_map under. #2 not in MapManager().ground_map. #3 not above worm 
	while not goodPlace:
		x = randint(10, MapManager().game_map.get_width() - 10)
		y = randint(10, ymin)
		
		goodPlace = True
		# test1
		if MapManager().is_ground_around(Vector(x,y), 10):
			goodPlace = False
			ymin += 10
			if ymin > 500:
				ymin = 20
			continue
		
		# test2
		for i in range(MapManager().game_map.get_height()):
			if y + i >= MapManager().game_map.get_height() - GameVariables().water_level:
				# no MapManager().ground_map bellow
				goodPlace = False
				continue
			if MapManager().game_map.get_at((x, y + i)) == GRD:
				goodPlace = True
				break
		# test3 (hopefully always possible)
		for worm in GameVariables().get_worms():
			if x > worm.pos.x - 15 and x < worm.pos.x + 15:
				goodPlace = False
				continue
	
	p = pack(Vector(x, y))
	return p
