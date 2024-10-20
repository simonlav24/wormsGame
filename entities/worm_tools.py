
import pygame
from random import randint

from common import GameVariables, point2world, sprites, blit_weapon_sprite, EntityPhysical
from common.vector import *

from game.visual_effects import Blast
from game.map_manager import MapManager, GRD


class WormUtility:
    def __init__(self):
        self.is_done: bool = False

    def activate(self) -> None:
        pass

    def release(self) -> None:
        self.is_done = True

    def is_movement_blocking(self) -> bool:
        return True

    def step(self):
        pass

    def draw(self):
        pass

    def apply_force(self):
        pass

class JetPack(WormUtility):
    def __init__(self, worm: EntityPhysical):
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
        blit_weapon_sprite(win, point2world(self.worm.pos - Vector(8,8)), "jet pack")
        value = 20 * (self.fuel/100)
        if value < 1:
            value = 1
        pygame.draw.rect(win, (220,220,220),(point2world(self.worm.pos + Vector(-10, -25)), (20,3)))
        pygame.draw.rect(win, (0,0,220),(point2world(self.worm.pos + Vector(-10, -25)), (int(value),3)))

class Rope(WormUtility):
    def __init__(self, worm: EntityPhysical, pos: Vector, direction: Vector):
        super().__init__()
        self.worm = worm
        self.rope = []
        self.initial_pos = pos
        self.initial_direction = direction
    
    def activate(self) -> None:
        self.shoot(self.initial_pos, self.initial_direction)

    def shoot(self, pos: Vector, direction: Vector):
        hit = False
        for t in range(5, 500):
            testPos = pos + direction * t
            if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() or testPos.x < 0 or testPos.y < 0:
                continue
            if MapManager().game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
                self.rope = [[testPos], dist(self.worm.pos, testPos)]
                self.worm.damp = 0.6
                self.worm.is_fall_affected = False
                hit = True
                break
        if not hit:
            self.release()
    
    def release(self) -> None:
        self.is_done = True
        self.worm.damp = 0.2
        self.worm.is_fall_affected = True

    def apply_force(self):
        if self.is_done:
            return
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            self.worm.acc.x -= 0.1
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.worm.acc.x += 0.1
        if pygame.key.get_pressed()[pygame.K_UP]:
            if self.rope[1] > 5:
                self.rope[1] = self.rope[1]-2
                directionToRope = (self.rope[0][-1] - self.worm.pos).getDir()
                ppos = self.worm.pos + directionToRope * (dist(self.worm.pos, self.rope[0][-1]) - self.rope[1])
                if not MapManager().check_free_pos(self.worm.radius, ppos):
                    self.rope[1] = self.rope[1]+2
        if pygame.key.get_pressed()[pygame.K_DOWN]:
            self.rope[1] = self.rope[1]+2
            directionToRope = (self.rope[0][-1] - self.worm.pos).getDir()
            ppos = self.worm.pos + directionToRope * (dist(self.worm.pos, self.rope[0][-1]) - self.rope[1])
            if not MapManager().check_free_pos(self.worm.radius, ppos):
                self.rope[1] = self.rope[1]-2
        
    def step(self):
        if self.is_done:
            return
        if dist(self.worm.pos, self.rope[0][-1]) > self.rope[1]:
            directionToRope = (self.rope[0][-1] - self.worm.pos).getDir()
            ppos = self.worm.pos + directionToRope * (dist(self.worm.pos, self.rope[0][-1]) - self.rope[1])
            self.worm.pos = ppos
            normal = directionToRope.normal()
            mul = dotProduct(self.worm.vel, normal)/(normal.getMag()**2)
            self.worm.vel = normal * mul
        
        if dist(self.worm.pos, self.rope[0][-1]) < self.rope[1] - 2:
            directionToRope = (self.rope[0][-1] - self.worm.pos).getDir()
            ppos = self.worm.pos + directionToRope * (dist(self.worm.pos, self.rope[0][-1]) - self.rope[1])
            self.worm.pos = ppos
            normal = directionToRope.normal()
            mul = dotProduct(self.worm.vel, normal)/(normal.getMag()**2)
            self.worm.vel = normal * mul
        
        # check secondary rope position
        for i in range(int(self.rope[1])-2):
            start = self.worm.pos
            direction = (self.rope[0][-1] - self.worm.pos).normalize()
            testPos = start + direction * i
            if not MapManager().is_on_map(testPos):
                break
            if MapManager().game_map.get_at(testPos.vec2tupint()) == GRD:
                self.rope[0].append(testPos)
                self.rope[1] = dist(self.worm.pos, self.rope[0][-1])
                break
        if len(self.rope[0]) > 1:
            count = int(dist(self.worm.pos, self.rope[0][-2]))
            for i in range(int(dist(self.worm.pos, self.rope[0][-2]))):
                start = self.worm.pos
                direction = (self.rope[0][-2] - self.worm.pos).normalize()
                testPos = start + direction * i
                if not MapManager().is_on_map(testPos):
                    break
                if MapManager().game_map.get_at(testPos.vec2tupint()) == GRD:
                    break
                if i == count-1:
                    self.rope[1] = dist(self.worm.pos, self.rope[0][-2])
                    self.rope[0].pop(-1)
        self.worm.damp = 0.7

    def draw(self, win: pygame.Surface):
        if self.is_done:
            return
        rope = [point2world(x) for x in self.rope[0]]
        rope.append(point2world(self.worm.pos))
        pygame.draw.lines(win, (250,250,0), False, rope)

class Parachute(WormUtility):
    def __init__(self, worm: EntityPhysical):
        super().__init__()
        self.worm = worm

    def is_movement_blocking(self) -> bool:
        return False

    def apply_force(self):
        if self.worm.vel.y > 1:
            self.worm.vel.y = 1
    
    def draw(self, win: pygame.Surface):
        win.blit(sprites.sprite_atlas, point2world(self.worm.pos - Vector(46, 31) // 2 + Vector(0, -15)), (80, 64, 46, 31))

    def step(self):
        if self.worm.vel.y < 1:
            self.release()
        self.worm.vel.x = GameVariables().physics.wind * 1.5

class WormTool():
    def __init__(self):
        self.tool: WormUtility = None

    def set(self, tool: WormUtility) -> bool:
        ''' sets the current tool, return true if set.
            if ocupied, release the tool and return false '''
        if self.tool is None:
            self.tool = tool
            self.tool.activate()
            return True
        else:
            self.release()
            return False

    def activate(self):
        if self.tool is not None:
            self.tool.activate()

    def release(self):
        if self.tool is not None:
            self.tool.release()
            self.tool = None

    def apply_force(self):
        if self.tool:
            self.tool.apply_force()

    def step(self):
        if self.tool:
            self.tool.step()
            if self.tool.is_done:
                self.release()
    
    def draw(self, win: pygame.Surface):
        if self.tool:
            self.tool.draw(win)

    def in_use(self) -> bool:
        ''' return true if tool in use '''
        return self.tool is not None
    
    def is_movement_blocking(self) -> bool:
        if self.tool is None:
            return False
        return self.tool.is_movement_blocking()

