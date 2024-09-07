

from enum import Enum
from math import pi, degrees, cos, sin
from random import randint, choice

import pygame

from common import GameVariables, point2world, RIGHT, LEFT, DOWN, UP, fonts, sprites, GameState, grayen, comments_damage, comments_flew, clamp, CRITICAL_FALL_VELOCITY, TeamData
from common.vector import *

from game.team_manager import Team
from game.time_manager import TimeManager
from game.visual_effects import FloatingText, splash
from entities.physical_entity import PhysObj
from game.map_manager import MapManager, GRD
from entities.worm_tools import WormTool
from weapons.sick_gas import GasParticles

class DeathCause(Enum):
    FLEW_OUT = 0
    DAMAGE = 1

class Worm (PhysObj):
    healthMode = 0
    roped = False
    def __init__(self, pos, name, team=None):
        super().__init__(pos)
        GameVariables().get_worms().append(self)

        self.color = (255, 206, 167)
        self.radius = 3.5
        self.damp = 0.2

        self.facing = RIGHT if self.pos.x < MapManager().game_map.get_width() / 2 else LEFT
        self._shoot_angle = pi / 2
        self.shoot_acc = 0
        self.shoot_vel = 0

        self.health = GameVariables().config.worm_initial_health
        self.alive: bool = True
        self.team: Team = team

        self.sick = 0
        self.sleep = False

        self.gravity = DOWN
        self.name_str = name
        self.name = fonts.pixel5.render(self.name_str, False, self.team.color)
        self.healthStr = fonts.pixel5.render(str(self.health), False, self.team.color)
        self.score = 0
        self.is_worm_collider = True

        # create surf
        self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        self.surf.blit(sprites.sprite_atlas, (0,0), (0,0,16,16))
        self.surf.blit(self.team.hat_surf, (0,0))

        self.angle = 0
        self.stableCount = 0
        self.worm_tool = WormTool()
    
    def get_team_data(self) -> TeamData:
        return self.team.data

    def apply_force(self):
        # gravity:
        if self.gravity == DOWN:
            self.acc.y += GameVariables().physics.global_gravity			
            self.worm_tool.apply_force()

        else:# up
            self.acc.y -= GameVariables().physics.global_gravity
    
    def drawCursor(self, win: pygame.Surface):
        shoot_vec = self.pos + self.get_shooting_direction() * 20
        pygame.draw.circle(win, (255,255,255), (int(shoot_vec.x) - int(GameVariables().cam_pos[0]), int(shoot_vec.y) - int(GameVariables().cam_pos[1])), 2)
    
    def sicken(self, sickness = 1):
        self.sick = sickness
        self.surf.fill((0,0,0,0))
        self.surf.blit(sprites.sprite_atlas, (0,0), (16,0,16,16))
        self.surf.blit(self.team.hat_surf, (0,0))
        self.color = (128, 189,66)
    
    def heal(self, hp):
        self.health += hp
        if self.healthMode == 1:
            self.healthStr = fonts.pixel5.render(str(self.health), False, self.team.color)
        self.sick = 0
        self.color = (255, 206, 167)
        self.surf.fill((0,0,0,0))
        self.surf.blit(sprites.sprite_atlas, (0,0), (0,0,16,16))
        self.surf.blit(self.team.hat_surf, (0,0))
            
    def damage(self, value, damageType=0):
        if self.alive:
            dmg = int(value * GameVariables().damage_mult)
            if dmg < 1:
                dmg = 1
            if dmg > self.health:
                dmg = self.health
            
            if dmg != 0: FloatingText(self.pos.vec2tup(), str(dmg))
            self.health -= dmg
            if self.health < 0:
                self.health = 0
            if Worm.healthMode == 1:
                self.healthStr = fonts.pixel5.render(str(self.health), False, self.team.color)
            
            GameVariables().game_mode.on_worm_damage(self, dmg)
    
    def draw(self, win: pygame.Surface):
        # draw collision
        if not self is GameVariables().player and self.alive:
            pygame.draw.circle(MapManager().worm_col_map, GRD, self.pos.vec2tupint(), int(self.radius)+1)

        # draw tool
        self.worm_tool.draw(win)

        # draw worm sprite
        angle = 45 * int(self.angle / 45)
        fliped = pygame.transform.flip(self.surf, self.facing == RIGHT, False)
        rotated = pygame.transform.rotate(fliped, angle)
        if self.gravity == UP:
            rotated = pygame.transform.flip(rotated, False, True)
        pygame.draw.circle(win, self.color, point2world(self.pos), self.radius + 1)
        win.blit(rotated, point2world(self.pos - tup2vec(rotated.get_size())//2))
        
        # draw name
        nameHeight = -21
        namePos = Vector(self.pos.x - self.name.get_width() / 2, max(self.pos.y + nameHeight, 10))
        win.blit(self.name , point2world(namePos))

        # draw height when above map
        if self.alive and self.pos.y < 0:
            num = fonts.pixel5.render(str(int(-self.pos.y)), False, self.team.color)
            win.blit(num, point2world(namePos + Vector(self.name.get_width() + 2,0)))
        
        # draw health
        if self.alive and GameVariables().initial_variables.draw_health_bar:
            self.draw_health(win)
        
        # draw sleep
        if self.sleep and self.alive:
            if GameVariables().time_overall % GameVariables().fps == 0:
                FloatingText(self.pos, "z", (0,0,0))

        # draw holding weapon
        if self is GameVariables().player and GameVariables().game_state == GameState.PLAYER_PLAY:
            adjust_degrees = 180 if self.facing == LEFT else 0
            weaponSurf = pygame.transform.rotate(pygame.transform.flip(GameVariables().weapon_hold, False, self.facing == LEFT), -degrees(self._shoot_angle - pi/2) * self.facing + adjust_degrees)
            win.blit(weaponSurf, point2world(self.pos - tup2vec(weaponSurf.get_size())/2 + Vector(0, 5)))

    def __str__(self):
        return self.name_str
    
    def __repr__(self):
        return str(self)
    
    def dieded(self, cause=DeathCause.DAMAGE):
        
        self.alive = False
        self.color = (167,167,167)
        self.surf.fill((0,0,0,0))
        self.surf.blit(sprites.sprite_atlas, (0,0), (32,0,16,16))
        self.name = fonts.pixel5.render(self.name_str, False, grayen(self.team.color))

        self.health = 0
                
        # comment:
        if cause == DeathCause.DAMAGE:
            comment = choice(comments_damage)
        elif cause == DeathCause.FLEW_OUT:
            comment = choice(comments_flew)
        comment_dict = [
            {'text': comment[0]},
            {'text': self.name_str, 'color': self.team.color},
            {'text': comment[1]},
        ]
        GameVariables().commentator.comment(comment_dict)
                
        # remove from regs:
        if self in GameVariables().get_worms():
            GameVariables().get_worms().remove(self)
        if self in self.team.worms:
            self.team.worms.remove(self)
        if cause != DeathCause.DAMAGE:
            self.remove_from_game()
        
        # if under control 
        if GameVariables().player == self:
            GameVariables().game_next_state = GameState.PLAYER_RETREAT
            GameVariables().game_state = GameVariables().game_next_state
            TimeManager().time_remaining_die()
                
        # todo: notify killed
        GameVariables().game_mode.on_worm_death(self)

    def draw_health(self, win: pygame.Surface):
        healthHeight = -15
        if Worm.healthMode == 0:
            value = 20 * min(self.health / GameVariables().config.worm_initial_health, 1)
            if value < 1:
                value = 1
            pygame.draw.rect(win, (220,220,220),(point2world(self.pos + Vector(-10, healthHeight)),(20,3)))
            pygame.draw.rect(win, (0,220,0),(point2world(self.pos + Vector(-10, healthHeight)), (int(value),3)))
        else:
            win.blit(self.healthStr , point2world(self.pos + Vector(-self.healthStr.get_width()/2, healthHeight)))

    def turn(self, direction: int) -> None:
        if not GameVariables().player_can_move:
            return
        self.facing = direction
        GameVariables().cam_track = self

    def get_shooting_direction(self) -> Vector:
        return Vector(cos(self._shoot_angle - pi / 2) * self.facing, sin(self._shoot_angle - pi / 2))

    def get_shooting_angle(self) -> float:
        return self._shoot_angle

    def step(self) -> None:
        super().step()
        if self.stable and self.alive:
            self.stableCount += 1
            if self.stableCount >= 30:
                
                self.angle *= 0.8
        else:
            self.stableCount = 0
            if not self is GameVariables().player:
                self.angle -= self.vel.x * 4
                self.angle = self.angle % 360

        self.worm_tool.step()
        
        # virus
        if self.sick == 2 and self.health > 0 and not GameVariables().game_state == GameState.WAIT_STABLE:
            if randint(1,200) == 1:
                GasParticles._sp.addSmoke(self.pos, color=(102, 255, 127))
        
        # shooting angle
        self.shoot_vel = clamp(self.shoot_vel + self.shoot_acc, 0.1, -0.1)
        self._shoot_angle = clamp(self._shoot_angle + self.shoot_vel * self.facing, pi, 0)

        # check if killed:
        if self.health <= 0 and self.alive:
            self.dieded()
        
        # check if on map:
        if self.pos.y > MapManager().game_map.get_height() - GameVariables().water_level:
            splash(self.pos, self.vel)
            angle = self.vel.getAngle()
            if 3.14 > angle > 2.7 or 0.4 > angle > 0:
                if self.vel.getMag() > 7:
                    self.pos.y = MapManager().game_map.get_height() - GameVariables().water_level - 1
                    self.vel.y *= -1
                    self.vel.x *= 0.7
            else:
                self.dieded(DeathCause.FLEW_OUT)
        
        if self.pos.y < 0:
            self.gravity = DOWN
        
        # check key bindings
        move_action = False
        if (self is GameVariables().player and
            GameVariables().player_can_move and
            GameVariables().player_in_control and
            self.alive):

            # move and turn
            if not self.worm_tool.in_use():
                keys = pygame.key.get_pressed()
                if keys[pygame.K_RIGHT]:
                    self.facing = RIGHT
                    move_action = True
                if keys[pygame.K_LEFT]:
                    self.facing = LEFT
                    move_action = True

                if move_action:
                    self.move(self.facing)

            # shooting angle
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                self.shoot_acc = -0.04 * self.facing
            elif keys[pygame.K_DOWN]:
                self.shoot_acc = +0.04 * self.facing
            else:
                self.shoot_acc = 0
                self.shoot_vel = 0
        else:
            self.damp = 0.2
            self.shoot_acc = 0
            self.shoot_vel = 0

        # collision with worms
        if not self.stable:
            velocity = self.vel.getMag()
            if velocity > 5:
                for worm in GameVariables().get_worms():
                    if worm == self or not worm.stable:
                        continue
                    if distus(self.pos, worm.pos) < (self.radius + worm.radius) * (self.radius + worm.radius):
                        worm.vel = vectorCopy(self.vel)

    def on_collision(self, ppos):
        if self.vel.getMag() > CRITICAL_FALL_VELOCITY and not self.worm_tool.in_use():
            MapManager().stain(self.pos, sprites.blood, sprites.blood.get_size(), False)
    
    def give_point(self, points: int) -> None:
        self.team.points += points