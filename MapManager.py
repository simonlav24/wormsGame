import os
import pygame
from random import choice, randint
from typing import List

import globals
from Common import *
from Constants import *

class ErrorImageNotFound(Exception):
    pass

def grabMapsFrom(paths: List[str]) -> List[str]:
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


class MapManager:
    def __init__(self) -> None:
        self.game_map: pygame.Surface = None
        self.ground_map: pygame.Surface = None
        self.ground_secondary: pygame.Surface = None
    
    def create_map_image(self, image_path: str, map_height: int, recolor: bool=False) -> None:
        ''' craete a map by an image '''
        
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

        self.create_map_surfaces((map_image.get_width(), map_image.get_height() + globals.game_manager.initialWaterLevel))

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
        self.ground_secondary.fill(globals.game_manager.feelColor[0])
        map_image.set_alpha(64)
        self.ground_secondary.blit(map_image, (0,0))
        self.ground_secondary.set_colorkey(globals.game_manager.feelColor[0])

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
        self.dark_mask = pygame.Surface(dims).convert_alpha()

    def is_ground_at(self, pos) -> bool:
        try:
            map_at = self.game_map.get_at(pos)
        except IndexError:
            return False

        return map_at == GRD

    def recolor_ground(self) -> None:
        ''' recolor the ground map with pattern and grass '''
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
        self.ground_secondary.fill(globals.game_manager.feelColor[0])
        ground_copy = self.ground_map.copy()
        ground_copy.set_alpha(64)
        self.ground_secondary.blit(ground_copy, (0,0))
        self.ground_secondary.set_colorkey(globals.game_manager.feelColor[0])

    def create_maps0(self):
        ## choose map
        maps = grabMapsFrom(["wormsMaps", "wormsMaps/moreMaps"])

        imageChoice = [None, None] # path, ratio
        if globals.game_manager.args.map_choice == "":
            # no map chosen in arguments. pick one at random
            imageChoice[0] = choice(maps)
        else:
            # if perlin map, recolor ground
            if "PerlinMaps" in globals.game_manager.args.map_choice:
                globals.game_manager.args.recolor_ground = True
            # search for chosen map
            for m in maps:
                if globals.game_manager.args.map_choice in m:
                    imageChoice[0] = m
                    break
            # if not found, then custom map
            if imageChoice[0] == None:
                imageChoice[0] = globals.game_manager.args.map_choice

        imageChoice[1] = globals.game_manager.hardRatioValue(imageChoice[0])
        if globals.game_manager.args.map_ratio != -1:
            imageChoice[1] = globals.game_manager.args.map_ratio

        globals.game_manager.mapChoice = imageChoice

        ## make game map
        globals.game_manager.lstepmax = globals.game_manager.wormsPerTeam * len(globals.team_manager.teams) + 1
        if globals.game_manager.diggingMatch:
            globals.game_manager.createMapSurfaces((int(1024 * 1.5), 512))
            self.game_map.fill(GRD)
            return

        # load map
        globals.game_manager.mapImage = pygame.image.load(imageChoice[0])

        # flip for fun
        if randint(0,1) == 0:
            globals.game_manager.mapImage = pygame.transform.flip(globals.game_manager.mapImage, True, False)

        # rescale based on ratio
        ratio = globals.game_manager.mapImage.get_width() / globals.game_manager.mapImage.get_height()
        globals.game_manager.mapImage = pygame.transform.scale(globals.game_manager.mapImage, (int(imageChoice[1] * ratio), imageChoice[1]))

        globals.game_manager.createMapSurfaces((globals.game_manager.mapImage.get_width(), globals.game_manager.mapImage.get_height() + globals.game_manager.initialWaterLevel))
        
        # fill gameMap
        image = globals.game_manager.mapImage.copy()
        imagepixels = pygame.PixelArray(image)
        extracted = imagepixels.extract(SKY)
        imagepixels.close()
        extracted.replace((0,0,0), (255,0,0))
        extracted.replace((255,255,255), SKY)
        extracted.replace((255,0,0), GRD)    
        self.game_map.blit(extracted.make_surface(), (0,0))
        extracted.close()

        globals.game_manager.mapImage.set_colorkey((0,0,0))
        
        ## make ground map
        self.ground_map.fill(SKY)
        if globals.game_manager.diggingMatch or globals.game_manager.args.recolor_ground:
            assets = os.listdir("./assets/")
            patterns = []
            for asset in assets:
                if "pattern" in asset:
                    patterns.append(asset)
            patternImage = pygame.image.load("./assets/" + choice(patterns))
            grassColor = choice([(10, 225, 10), (10,100,10)] + [i[3] for i in feels])

            for x in range(0, globals.game_manager.mapWidth):
                for y in range(0, globals.game_manager.mapHeight):
                    if self.game_map.get_at((x,y)) == GRD:
                        self.ground_map.set_at((x,y), patternImage.get_at((x % patternImage.get_width(), y % patternImage.get_height())))

            colorfulness = pygame.Surface((8,5), pygame.SRCALPHA)
            for x in range(8):
                for y in range(5):
                    randColor = (randint(0,50), randint(0,50), randint(0,50))
                    colorfulness.set_at((x, y), choice([randColor, (0,0,0)]))
            self.ground_map.blit(pygame.transform.smoothscale(colorfulness, (globals.game_manager.mapWidth, globals.game_manager.mapHeight)), (0,0), special_flags=pygame.BLEND_SUB)

            for x in range(0, globals.game_manager.mapWidth):
                for y in range(0, globals.game_manager.mapHeight):
                    if self.game_map.get_at((x,y)) == GRD:
                        if y > 0 and self.game_map.get_at((x,y - 1)) != GRD:
                            for i in range(randint(3,5)):
                                if y + i < globals.game_manager.mapHeight:
                                    if self.game_map.get_at((x, y + i)) == GRD:
                                        self.ground_map.set_at((x,y + i), [min(abs(i + randint(-30,30)), 255) for i in grassColor])

            self.ground_secondary.fill(globals.game_manager.feelColor[0])
            groundCopy = self.ground_map.copy()
            groundCopy.set_alpha(64)
            self.ground_secondary.blit(groundCopy, (0,0))
            self.ground_secondary.set_colorkey(globals.game_manager.feelColor[0])
            return

        self.ground_map.blit(globals.game_manager.mapImage, (0,0))
        self.ground_secondary.fill(globals.game_manager.feelColor[0])
        globals.game_manager.mapImage.set_alpha(64)
        self.ground_secondary.blit(globals.game_manager.mapImage, (0,0))
        self.ground_secondary.set_colorkey(globals.game_manager.feelColor[0])


    