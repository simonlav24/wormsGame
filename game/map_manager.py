
import os
import pygame
from math import cos, pi, sin
from random import choice, randint
from typing import List, Tuple

from common import PATH_ASSETS, feels, GameVariables, SingletonMeta
from common.vector import *

SKY = (0,0,0,0)
GRD = (255,255,255,255)

class ErrorImageNotFound(Exception):
    pass

def grab_maps(paths: List[str]) -> List[str]:
    ''' returns list of available map files '''
    maps = []
    for path in paths:
        if not os.path.isdir(path):
            continue
        for image_file in os.listdir(path):
            if not image_file.endswith(".png"):
                continue
            string = os.path.join(path, image_file)
            string = os.path.abspath(string)
            maps.append(string)
    return maps

class MapManager(metaclass=SingletonMeta):
    def __init__(self) -> None:
        # default value for game map dimensions
        self.game_map: pygame.Surface = pygame.Surface((GameVariables().win_width, GameVariables().win_height))
        self.ground_map: pygame.Surface = None
        self.ground_secondary: pygame.Surface = None

        self.draw_ground_secondary = True

    def get_map_height(self) -> int:
        return self.game_map.get_height()

    def get_map_size(self) -> Vector:
        return Vector(self.game_map.get_width(), self.game_map.get_height())

    def create_map_image(self, image_path: str, map_height: int, recolor: bool=False) -> None:
        ''' craete a map by an image '''
        
        feel_color =  feels[GameVariables().config.feel_index]

        # load map
        if not os.path.exists(image_path):
            raise FileNotFoundError(f'image path: {image_path} not found')
        
        map_image = pygame.image.load(image_path)

        # check for hard ratio
        first = image_path.find("big")
        if first != -1:
            second = image_path.find(".", first)
            if second != -1:
                map_height = int(image_path[first+3:second])

        # rescale based on ratio
        ratio = map_image.get_width() / map_image.get_height()
        map_image = pygame.transform.scale(map_image, (int(map_height * ratio), map_height))

        self.create_map_surfaces((map_image.get_width(), map_image.get_height() + GameVariables().initial_variables.water_level))

        # fill gameMap
        image = map_image.copy()
        image_pixels = pygame.PixelArray(image)
        extracted = image_pixels.extract(SKY)
        image_pixels.close()
        extracted.replace((0,0,0), (255,0,0))
        extracted.replace((255,255,255), SKY)
        extracted.replace((255,0,0), GRD)
        self.game_map.blit(extracted.make_surface(), (0,0))
        extracted.close()

        map_image.set_colorkey((0,0,0))

        ## make ground map
        self.ground_map.fill(SKY)
        self.ground_map.blit(map_image, (0,0))
        self.ground_secondary.fill(feel_color[0])
        map_image.set_alpha(64)
        self.ground_secondary.blit(map_image, (0,0))
        self.ground_secondary.set_colorkey(feel_color[0])

        if recolor:
            self.recolor_ground()

    def create_map_digging(self, ratio: int) -> None:
        ''' craete a digging match map '''
        self.create_map_surfaces((int(1024 * 1.5), ratio))
        self.game_map.fill(GRD)
        self.recolor_ground()

    def create_map_surfaces(self, dims) -> None:
        ''' create all map related surfaces '''

        self.game_map = pygame.Surface(dims)
        self.game_map.fill(SKY)

        self.worm_col_map = pygame.Surface(dims)
        self.worm_col_map.fill(SKY)

        self.objects_col_map = pygame.Surface(dims)
        self.objects_col_map.fill(SKY)

        self.ground_map = pygame.Surface(dims).convert_alpha()
        self.ground_secondary = pygame.Surface(dims).convert_alpha()

    def is_ground_at(self, pos) -> bool:
        try:
            map_at = self.game_map.get_at(pos)
        except TypeError:
            map_at = self.game_map.get_at((int(pos[0]), int(pos[1])))
        except IndexError:
            return False

        return map_at == GRD

    def recolor_ground(self) -> None:
        ''' recolor the ground map with pattern and grass '''

        feel_color =  feels[GameVariables().config.feel_index]
        assets = os.listdir(PATH_ASSETS)
        patterns = []
        for asset in assets:
            if "pattern" in asset:
                patterns.append(asset)
        pattern_image = pygame.image.load(os.path.join(PATH_ASSETS, choice(patterns)))
        grass_color = choice([(10, 225, 10), (10,100,10)] + [i[3] for i in feels])

        for x in range(0, self.game_map.get_width()):
            for y in range(0, self.game_map.get_height()):
                if self.game_map.get_at((x,y)) == GRD:
                    self.ground_map.set_at((x,y), pattern_image.get_at((x % pattern_image.get_width(), y % pattern_image.get_height())))

        # add random colors
        colors = pygame.Surface((8,5), pygame.SRCALPHA)
        for x in range(8):
            for y in range(5):
                random_color = (randint(0,50), randint(0,50), randint(0,50))
                colors.set_at((x, y), choice([random_color, (0,0,0)]))
        self.ground_map.blit(pygame.transform.smoothscale(colors, (self.game_map.get_width(), self.game_map.get_height())), (0,0), special_flags=pygame.BLEND_SUB)

        # draw grass
        for x in range(0, self.game_map.get_width()):
            for y in range(0, self.game_map.get_height()):
                if self.game_map.get_at((x,y)) == GRD:
                    if y > 0 and self.game_map.get_at((x, y - 1)) != GRD:
                        for i in range(randint(3,5)):
                            if y + i < self.game_map.get_height():
                                if self.game_map.get_at((x, y + i)) == GRD:
                                    self.ground_map.set_at((x,y + i), [min(abs(i + randint(-30, 30)), 255) for i in grass_color])

        # secondary ground
        self.ground_secondary.fill(feel_color[0])
        ground_copy = self.ground_map.copy()
        ground_copy.set_alpha(64)
        self.ground_secondary.blit(ground_copy, (0,0))
        self.ground_secondary.set_colorkey(feel_color[0])

    def check_free_pos(self, radius, pos: Vector, worm_col = False) -> bool:
        r = 0
        while r < 2 * pi:
            testPos = Vector(radius * cos(r) + pos.x, radius * sin(r) + pos.y)
            if testPos.x >= self.game_map.get_width() or testPos.y >= self.game_map.get_height() - GameVariables().water_level or testPos.x < 0:
                if GameVariables().config.option_closed_map:
                    return False
                else:
                    r += pi /8
                    continue
            if testPos.y < 0:
                if self.game_map.get_at((int(testPos.x), 0)) == GRD:
                    return False
                else:
                    r += pi /8
                    continue
            
            getAt = testPos.vec2tupint()
            if self.game_map.get_at(getAt) == GRD:
                return False
            if self.objects_col_map.get_at(getAt) != (0,0,0):
                return False
            if worm_col and self.worm_col_map.get_at(getAt) != (0,0,0):
                return False
            
            r += pi /8
        return True

    def is_on_map(self, vec: Vector) -> bool:
        return not (vec[0] < 0 or vec[0] >= self.game_map.get_width() or vec[1] < 0 or vec[1] >= self.game_map.get_height())

    def stain(self, pos: Vector, surf: pygame.Surface, size: Tuple[int], alphaMore: bool) -> None:
        rotated = pygame.transform.rotate(pygame.transform.scale(surf, size), randint(0, 360))
        if alphaMore:
            rotated.set_alpha(randint(100,180))
        size = rotated.get_size()
        grounder = pygame.Surface(size, pygame.SRCALPHA)
        grounder.blit(self.ground_map, (0,0), (pos - tup2vec(size)/2, size))
        patch = pygame.Surface(size, pygame.SRCALPHA)
        
        patch.blit(self.game_map, (0,0), (pos - tup2vec(size)/2, size))
        patch.set_colorkey(GRD)
        
        grounder.blit(rotated, (0,0))
        grounder.blit(patch, (0,0))
        
        grounder.set_colorkey(SKY)
        self.ground_map.blit(grounder, pos - tup2vec(size)/2)


    