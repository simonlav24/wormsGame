
import pygame
from random import uniform, randint, choice
from typing import List
from math import exp, sin

from common import GameVariables, point2world, DARK_COLOR, WATER_AMP, GameGlobals
from common.vector import *

from game.map_manager import MapManager

def perlinNoise1D(count, seed, octaves, bias) -> List[float]:
    output = []
    for x in range(count):
        noise = 0.0
        scaleAcc = 0.0
        scale = 1.0
        
        for o in range(octaves):
            pitch = count >> o
            sample1 = (x // pitch) * pitch
            sample2 = (sample1 + pitch) % count
            blend = (x - sample1) / pitch
            sample = (1 - blend) * seed[int(sample1)] + blend * seed[int(sample2)]
            scaleAcc += scale
            noise += sample * scale
            scale = scale / bias
        output.append(noise / scaleAcc)
    return output


def render_mountain(dims, color) -> pygame.Surface:
    ''' creates a mountain surf '''
    mount = pygame.Surface(dims, pygame.SRCALPHA)
    mount.fill((0,0,0,0))
    
    noiseSeed = [uniform(0,1) for _ in range(dims[0])]
    noiseSeed[0] = 0.5
    surface = perlinNoise1D(dims[0], noiseSeed, 7, 2) # 8 , 2.0
    
    for x in range(0,dims[0]):
        for y in range(0,dims[1]):
            if y >= surface[x] * dims[1]:
                mount.set_at((x,y), color)
    return mount


def renderCloud(colors=[(224, 233, 232), (192, 204, 220)]) -> pygame.Surface:
    ''' create cloud surface '''
    c1 = colors[0]
    c2 = colors[1]
    surf = pygame.Surface((170, 70), pygame.SRCALPHA)
    circles = []
    leng = randint(15,30)
    space = 5
    gpos = (20, 40) 
    for i in range(leng):
        pos = Vector(gpos[0] + i * space, gpos[1]) + vectorUnitRandom() * uniform(0, 10)
        radius = max(20 * (exp(-(1/(5*leng)) * ((pos[0]-gpos[0])/space -leng/2)**2)), 5) * uniform(0.8,1.2)
        circles.append((pos, radius))
    circles.sort(key=lambda x: x[0][0])
    for c in circles:
        pygame.draw.circle(surf, c2, c[0], c[1])
    for c in circles:
        pygame.draw.circle(surf, c1, c[0] - Vector(1,1) * 0.7 * 0.2 * c[1], c[1] * 0.8)
    for i in range(0,len(circles),int(len(circles)/4)):
        pygame.draw.circle(surf, c2, circles[i][0], circles[i][1])
    for i in range(0,len(circles),int(len(circles)/8)):
        pygame.draw.circle(surf, c1, circles[i][0] - Vector(1,1) * 0.8 * 0.2 * circles[i][1], circles[i][1] * 0.8)
    
    return surf


class Cloud:
    ''' single cloud, procedurally rendered, affected by wind '''
    _reg = []
    _toRemove = []
    cWidth = 170
    def __init__(self, pos):
        self._reg.append(self)
        self.pos = Vector(pos[0],pos[1])
        self.vel = Vector(0,0)
        self.acc = Vector(0,0)
        self.surf = renderCloud()
        self.randomness = uniform(0.97, 1.02)
        
    def step(self):
        self.acc.x = GameVariables().physics.wind
        self.vel += self.acc * GameVariables().dt
        self.vel *= 0.85 * self.randomness
        self.pos += self.vel * GameVariables().dt
        
        if self.pos.x > GameVariables().cam_pos[0] + GameGlobals().win_width + 100 or self.pos.x < GameVariables().cam_pos[0] - 100 - self.cWidth:
            self._toRemove.append(self)
            
    def draw(self, win: pygame.Surface):
        win.blit(self.surf, point2world(self.pos))


class WaterLayer:
    def __init__(self, water_color, y_offset: int) -> None:
        self.time = 0
        self.y_offset = y_offset
        self.points = [Vector(i * 20, 3 + WATER_AMP + WATER_AMP * (-1)**i) for i in range(-1,12)]
        self.speeds = [uniform(0.95, 1.05) for _ in range(-1,11)]
        self.phase = [sin(self.time / (3 * self.speeds[i])) for i in range(-1,11)]

        self.surf = pygame.Surface((200, WATER_AMP * 2 + 6), pygame.SRCALPHA)
        self.water_color = water_color

    def step(self) -> None:
        self.time += 1
        self.surf.fill((0,0,0,0))
        self.points = [Vector(i * 20, 3 + WATER_AMP + self.phase[i % 10] * WATER_AMP * (-1)**i) for i in range(-1,12)]
        pygame.draw.polygon(self.surf, self.water_color[0], self.points + [(200, WATER_AMP * 2 + 6), (0, WATER_AMP * 2 + 6)])
        pygame.draw.lines(self.surf, self.water_color[1], False, self.points, 2)
        
        self.phase = [sin(self.time / (3 * self.speeds[i])) for i in range(-1,11)]

    def draw(self, win: pygame.Surface) -> None:
        width = 200
        height = 10
        offset = (GameVariables().cam_pos[0])//width
        times = GameGlobals().win_width // width + 2
        for i in range(times):
            x = int(-GameVariables().cam_pos[0]) + int(int(offset) * width + i * width)
            y =  int(MapManager().get_map_height() - GameVariables().water_level - 3 - WATER_AMP - self.y_offset) - int(GameVariables().cam_pos[1])
            win.blit(self.surf, (x, y))
        
        pygame.draw.rect(win, self.water_color[0], ((0,y + height), (GameGlobals().win_width, GameVariables().water_level)))


class BackGround:
    ''' manages background. clouds, mountains, water '''
    def __init__(self, feel_color, is_dark=False):
        self.mountains = [render_mountain((180, 110), feel_color[3]), render_mountain((180, 150), feel_color[2])]
        colorRect = pygame.Surface((2,2))
        pygame.draw.line(colorRect, feel_color[0], (0,0), (2,0))
        pygame.draw.line(colorRect, feel_color[1], (0,1), (2,1))
        self.imageSky = pygame.transform.smoothscale(colorRect, (GameGlobals().win_width, GameGlobals().win_height))

        self.backColor = feel_color[0]
        if is_dark:
            self.backColor = DARK_COLOR

        water_color = [tuple((feel_color[0][i] + feel_color[1][i]) // 2 for i in range(3))]
        water_color.append(tuple(min(int(water_color[0][i] * 1.5), 255) for i in range(3)))

        self.water_layers_bottom = [
            WaterLayer(water_color, 22),
        ]

        self.water_layers_top = [
            WaterLayer(water_color, 12),
            WaterLayer(water_color, 2),
        ]
        self.water_rise_amount = 0

    def water_rise(self, amount: int) -> None:
        ''' water rise by amount '''
        self.water_rise_amount = amount

    def step(self) -> None:
        self.step_clouds()
        for layer in self.water_layers_bottom:
            layer.step()
        for layer in self.water_layers_top:
            layer.step()
        
        if self.water_rise_amount > 0:
            GameVariables().water_level += 1
            self.water_rise_amount -= 1
    
    def step_clouds(self) -> None:
        if len(Cloud._reg) < 8 and randint(0,10) == 1:
            pos = Vector(choice([
                GameVariables().cam_pos[0] - Cloud.cWidth - 100,
                GameVariables().cam_pos[0] + GameGlobals().win_width + 100
                ]), randint(5, MapManager().get_map_height() - 150))
            Cloud(pos)
        for cloud in Cloud._reg: cloud.step()
        for cloud in Cloud._toRemove: Cloud._reg.remove(cloud)
        Cloud._toRemove = []
    
    def draw(self, win: pygame.Surface):
        win.fill(self.backColor)
        win.blit(
            pygame.transform.scale(self.imageSky, (win.get_width(), MapManager().get_map_height())),
            (0,0 - GameVariables().cam_pos[1]))
        
        for cloud in Cloud._reg:
            cloud.draw(win)
        self.drawBackGround(self.mountains[1], 4, win)
        self.drawBackGround(self.mountains[0], 2, win)
        for layer in self.water_layers_bottom:
            layer.draw(win)
    
    def drawSecondary(self, win):
        for layer in self.water_layers_top:
            layer.draw(win)
    
    def drawBackGround(self, surf: pygame.Surface, parallax: float, win: pygame.Surface):
        width = surf.get_width()
        height = surf.get_height()
        offset = (GameVariables().cam_pos[0] / parallax) // width
        times = GameGlobals().win_width // width + 2
        for i in range(times):
            x = int(-GameVariables().cam_pos[0] / parallax) + int(int(offset) * width + i * width)
            y = (
                int(MapManager().get_map_height() - GameVariables().initial_variables.water_level - height)
                - int(GameVariables().cam_pos[1]) + int((MapManager().get_map_height()
                - GameVariables().initial_variables.water_level - GameGlobals().win_height 
                - int(GameVariables().cam_pos[1])) / (parallax * 1.5)) + 20 - parallax * 3
            )
            win.blit(surf, (x, y))
    