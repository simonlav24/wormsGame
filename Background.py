
import pygame
from random import uniform, randint, choice
from typing import List
from math import exp

from vector import Vector, vectorUnitRandom
from GameVariables import GameVariables
from Constants import DARK_COLOR
import globals
from MapManager import MapManager

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
        
        if self.pos.x > GameVariables().cam_pos[0] + GameVariables().win_width + 100 or self.pos.x < GameVariables().cam_pos[0] - 100 - self.cWidth:
            self._toRemove.append(self)
            
    def draw(self, win: pygame.Surface):
        win.blit(self.surf, globals.point2world(self.pos))


class BackGround:
    ''' manages background. clouds, mountains, water '''
    def __init__(self, feelColor, isDark=False):
        self.mountains = [render_mountain((180, 110), feelColor[3]), render_mountain((180, 150), feelColor[2])]
        colorRect = pygame.Surface((2,2))
        pygame.draw.line(colorRect, feelColor[0], (0,0), (2,0))
        pygame.draw.line(colorRect, feelColor[1], (0,1), (2,1))
        self.imageSky = pygame.transform.smoothscale(colorRect, (GameVariables().win_width, GameVariables().win_height))

        self.backColor = feelColor[0]
        if isDark:
            self.backColor = DARK_COLOR



        # Water.level = GameVariables().initial_variables.water_level
        # Water.waterColor = [tuple((feelColor[0][i] + feelColor[1][i]) // 2 for i in range(3))]
        # Water.waterColor.append(tuple(min(int(Water.waterColor[0][i] * 1.5), 255) for i in range(3)))

        # Water.createLayers()
    
    def step(self):
        self.step_clouds()
        # Water.stepAll()
    
    def step_clouds(self):
        if len(Cloud._reg) < 8 and randint(0,10) == 1:
            pos = Vector(choice([GameVariables().cam_pos[0] - Cloud.cWidth - 100, GameVariables().cam_pos[0] + GameVariables().win_width + 100]), randint(5, MapManager().get_map_height() - 150))
            Cloud(pos)
        for cloud in Cloud._reg: cloud.step()
        for cloud in Cloud._toRemove: Cloud._reg.remove(cloud)
        Cloud._toRemove = []
    
    def draw(self, win: pygame.Surface):
        win.fill(self.backColor)
        win.blit(pygame.transform.scale(self.imageSky, (win.get_width(), MapManager().get_map_height())), (0,0 - GameVariables().cam_pos[1]))
        
        for cloud in Cloud._reg:
            cloud.draw(win)
        self.drawBackGround(self.mountains[1], 4, win)
        self.drawBackGround(self.mountains[0], 2, win)
        # Water.layerTop.draw(22)
    
    def drawSecondary(self):
        pass
        # draw top layer of water
        # Water.layerMiddle.draw(12)
        # Water.layerBottom.draw(2)
    
    def drawBackGround(self, surf, parallax, win):
        width = surf.get_width()
        height = surf.get_height()
        offset = (GameVariables().cam_pos[0] / parallax) // width
        times = GameVariables().win_width // width + 2
        for i in range(times):
            x = int(-GameVariables().cam_pos[0] / parallax) + int(int(offset) * width + i * width)
            y = int(MapManager().get_map_height() - GameVariables().initial_variables.water_level - height) - int(GameVariables().cam_pos[1]) + int((MapManager().get_map_height() - GameVariables().initial_variables.water_level - GameVariables().win_height - int(GameVariables().cam_pos[1]))/(parallax*1.5)) + 20 - parallax * 3
            win.blit(surf, (x, y))
    
    def drawBackGroundxy(self, surf, parallax, win):
        width = surf.get_width()
        height = surf.get_height()
        offsetx = (GameVariables().cam_pos[0] / parallax) // width
        offsety = (GameVariables().cam_pos[1] / parallax) // height
        timesx = GameVariables().win_width // width + 2
        timesy = GameVariables().win_height // height + 2
        for i in range(timesx):
            for j in range(timesy):
                x = int(-GameVariables().cam_pos[0] / parallax) + int(int(offsetx) * width + i * width)
                y = int(-GameVariables().cam_pos[1]/parallax) + int(int(offsety) * height + j * height)
                win.blit(surf, (x, y))
