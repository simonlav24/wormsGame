

import pygame
from random import randint, uniform
from math import degrees

from common import blit_weapon_sprite, point2world, GameVariables, sprites, GameState, JUMP_VELOCITY, LEFT
from common.vector import Vector, vectorCopy, tup2vec, normalize, distus

from game.map_manager import MapManager
from game.team_manager import TeamManager
from entities import PhysObj
from game.visual_effects import Blast, EffectManager
from entities.gun_shell import GunShell

TRAMPOLINE_MAX_VEL = 8
TRAMPOLINE_MIN_VEL = 3

class Flare(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		GameVariables().get_light_sources().append(self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (128, 0, 0)
		self.damp = 0.4
		self.light_radius = 50
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "flare")
		self.angle = 0
	
	def step(self):
		super().step()
		if self.vel.getMag() > 0.25:
			self.angle -= self.vel.x * 4
		if randint(0,10) == 1:
			Blast(self.pos, randint(self.radius,7), 150)
		if self.light_radius < 0:
			self.remove_from_game()
			return
		EffectManager().add_light(vectorCopy(self.pos), self.light_radius, (100, 0, 0, 100))
	
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size()) / 2))
	
	def remove_from_game(self) -> None:
		super().remove_from_game()
		GameVariables().get_light_sources().remove(self)


def draw_trampoline_hint(win: pygame.Surface) -> None:
	surf = pygame.Surface((24, 7), pygame.SRCALPHA)
	surf.blit(sprites.sprite_atlas, (0,0), (100, 117, 24, 7))
	position = GameVariables().player.pos + GameVariables().player.get_shooting_direction() * 20
	anchored = False
	for i in range(25):
		cpos = position.y + i
		if MapManager().is_ground_at(Vector(position.x, cpos)):
			anchored = True
			break
	if anchored:
		surf.set_alpha(200)
	else:
		surf.set_alpha(100)
	
	win.blit(surf, point2world(position - Vector(24,7) / 2))


class Trampoline:
	_sprite = None
	def __init__(self, pos):
		GameVariables().register_non_physical(self)
		self.pos = vectorCopy(pos)
		self.directionalVel = 0
		self.offset = 0
		self.stable = False
		for i in range(25):
			if MapManager().is_ground_at(self.pos + Vector(0, i)):
				self.anchor = self.pos + Vector(0, i)
				break
		self.size = Vector(24, 8)
		if Trampoline._sprite == None:
			Trampoline._sprite = pygame.Surface((24, 7), pygame.SRCALPHA)
			Trampoline._sprite.blit(sprites.sprite_atlas, (0,0), (100, 117, 24, 7))
	
	def collide(self, pos):
		if pos.x > self.pos.x - self.size.x / 2 and pos.x < self.pos.x + self.size.x / 2 and pos.y > self.pos.y - self.size.y / 2 and pos.y < self.pos.y + self.size.y:
			return True
		return False
	
	def step(self):
		if not self.stable:
			acc = - 1 * self.offset
			self.directionalVel += acc
			self.directionalVel *= 0.8
			self.offset += self.directionalVel
			if abs(self.directionalVel) < 0.2 and abs(self.offset) < 0.2:
				self.directionalVel = 0
				self.offset = 0
				self.stable = True
		
		if not MapManager().is_ground_at(self.anchor):
			GameVariables().unregister_non_physical(self)
			gs = GunShell(vectorCopy(self.pos))
			gs.surf = Trampoline._sprite
		
		for obj in GameVariables().get_physicals():
			# trampoline
			if obj.vel.y > 0 and self.collide(obj.pos):
				self.spring(obj.vel.y)

				if abs(obj.vel.y) <= TRAMPOLINE_MAX_VEL:
					obj.vel.y *= -1.3
				else:
					obj.vel.y = -obj.vel.y
				
				if abs(obj.vel.y) <= TRAMPOLINE_MIN_VEL:
					obj.vel.y = -TRAMPOLINE_MIN_VEL

				# prevent stucking on trampoline
				if GameVariables().game_state == GameState.WAIT_STABLE:
					obj.vel.x += uniform(-0.5,0.5)
	
	def spring(self, amount):
		self.offset = -amount
		self.stable = False
	
	def draw(self, win: pygame.Surface):
		startPos = self.anchor.y
		endPos = self.pos.y + self.offset - 4
		i = startPos
		while i > endPos:
			win.blit(sprites.sprite_atlas, point2world((self.pos.x - 5, i)), (107, 124, 10, 4))
			i -= 4
		win.blit(Trampoline._sprite, point2world(self.pos + Vector(0, self.offset) - self.size / 2))


class Baseball:
	def __init__(self):	
		self.direction = GameVariables().player.get_shooting_direction()
		GameVariables().register_non_physical(self)
		self.timer = 0
		hitted = []
		for t in range(5, 25):
			testPositions = []
			testPos = GameVariables().player.pos + self.direction * t
			testPositions.append(testPos)
			testPositions.append(testPos + normalize(self.direction).getNormal() * 3)
			testPositions.append(testPos - normalize(self.direction).getNormal() * 3)
			
			for worm in GameVariables().get_worms():
				for point in testPositions:
					if worm in hitted:
						continue
					if distus(point, worm.pos) < worm.radius * worm.radius:
						hitted.append(worm)
						worm.damage(randint(15,25))
						worm.vel += self.direction * 8
						GameVariables().cam_track = worm

	def step(self):
		self.timer += 1 * GameVariables().dt
		if self.timer >= 15:
			GameVariables().unregister_non_physical(self)

	def draw(self, win: pygame.Surface):
		angle = -degrees(self.direction.getAngle()) + 180
		weaponSurf = pygame.transform.rotate(pygame.transform.flip(GameVariables().weapon_hold, False, GameVariables().player.facing == LEFT), angle)
		win.blit(weaponSurf, point2world(GameVariables().player.pos - tup2vec(weaponSurf.get_size()) / 2 + self.direction * 16))


class WormSwitcher:
	def __init__(self):
		GameVariables().register_non_physical(self)
		GameVariables().register_cycle_observer(self)
		GameVariables().get_event_handlers().append(self)
	
	def handle_event(self, event) -> None:
		if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
			if GameVariables().game_state == GameState.PLAYER_PLAY:
				self.switch()
	
	def step(self) -> None:
		pass

	def draw(self, win: pygame.Surface) -> None:
		pass

	def switch(self) -> None:
		worm = GameVariables().player
		current_worm_index = TeamManager().current_team.worms.index(worm)
		total_worms = len(TeamManager().current_team.worms)
		current_worm_index = (current_worm_index + 1) % total_worms
		GameVariables().player = TeamManager().current_team.worms[current_worm_index]
		GameVariables().cam_track = GameVariables().player


	def on_cycle(self):
		GameVariables().unregister_non_physical(self)
		GameVariables().unregister_cycle_observer(self)
		GameVariables().get_event_handlers().remove(self)