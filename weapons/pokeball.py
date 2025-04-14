

from random import choice
from enum import Enum

import pygame

from common.vector import Vector, dist, tup2vec
from common import GameVariables, point2world, blit_weapon_sprite, clamp, fonts, draw_lightning, DamageType

from entities import PhysObj, Worm
from game.world_effects import boom
from game.sfx import Sfx, SfxIndex

class BallState(Enum):
	INIT = 0
	CATCHING = 1
	HOLD = 2
	DESTROY = 3


class PokeBall(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0,0,200)
		self.damp = 0.4
		self.timer = 0
		self.hold: Worm | None = None
		self.health = 10
		self.name = None
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "pokeball")
		self.angle = 0
		self.mode = BallState.INIT
	
	def fall_damage(self) -> None:
		pass

	def damage(self, value: int, damage_type: DamageType=DamageType.HURT, kill: bool=False) -> None:
		if damage_type == 1:
			return
		dmg = int(value * GameVariables().damage_mult)
		dmg = clamp(dmg, self.health, 1)
		
		self.health -= dmg
		if self.health <= 0:
			self.health = 0
			self.dead = True
	
	def death_response(self):
		if self.hold:
			self.hold.pos = self.pos + Vector(0,- (self.radius + self.hold.radius))
			self.hold.vel = Vector(0,-1)
			GameVariables().register_physical(self.hold)
			GameVariables().get_worms().append(self.hold)
			self.hold.team.worms.append(self.hold)
		else:
			boom(self.pos, 20)
	
	def step(self):
		super().step()
		self.timer += 1
		if self.vel.getMag() > 0.25:
			self.angle -= self.vel.x * 4

		if self.mode == BallState.INIT:
			if self.timer == GameVariables().fuse_time:
				self.mode = BallState.CATCHING

		elif self.mode == BallState.CATCHING:
			if self.hold is None:
				self.stable = False
				closer = [None, 7000]
				for worm in GameVariables().get_worms():
					distance = dist(self.pos, worm.pos)
					if distance < closer[1]:
						closer = [worm, distance]
				if closer[1] < 50:
					self.hold = closer[0]
			
			if self.timer == GameVariables().fuse_time + GameVariables().fps * 2:
				if self.hold is not None:
					self.mode = BallState.HOLD
					self.cought()
				else:
					self.mode = BallState.DESTROY

		elif self.mode == BallState.HOLD:
			if self.timer <= GameVariables().fuse_time + GameVariables().fps * 2 + GameVariables().fps / 2:
				GameVariables().game_distable()

		elif self.mode == BallState.DESTROY:
			self.dead = True
		
	
	def cought(self) -> None:
		self.hold.damage(10)
		GameVariables().unregister_physical(self.hold)
		GameVariables().get_worms().remove(self.hold)

		self.hold.team.worms.remove(self.hold)
		self.name = fonts.pixel5.render(self.hold.name_str, False, self.hold.team.color)
		name = self.hold.name_str
		color = self.hold.team.color
		comments = [
			[{'text': name, 'color': color}, {'text': ', i choose you'}],
			[{'text': "gotta catch 'em al"}],
			[{'text': name, 'color': color}, {'text': ' will help beat the next gym leader'}],
		]
		GameVariables().commentator.comment(choice(comments))

	def remove_from_game(self):
		super().remove_from_game()
		if self.mode == BallState.CATCHING:
			Sfx().loop_decrease(SfxIndex.ELECTRICITY_LOOP, 100, force_stop=True)

	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		
		if GameVariables().fuse_time <= self.timer < GameVariables().fuse_time + GameVariables().fps * 2 and self.hold:
			draw_lightning(win, self.pos, self.hold.pos, (255, 255, 204))
			if self.mode == BallState.CATCHING:
				Sfx().loop_ensure(SfxIndex.ELECTRICITY_LOOP)
		else:
			if self.mode == BallState.CATCHING:
				Sfx().loop_decrease(SfxIndex.ELECTRICITY_LOOP, 100, force_stop=True)
		if self.name:
			win.blit(self.name , point2world(self.pos + Vector(-self.name.get_width()/2, -21)))
