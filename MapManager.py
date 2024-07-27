import os
import pygame
from random import choice, randint
from typing import List

import globals
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
    
    def create_map_image(self, image_path: str, map_height: int, recolor: bool=False):
        ''' craete a map by an image '''
        
        # load map
        if not os.path.exists(image_path):
            raise FileNotFoundError(f'image path: {image_path} not found')
        
        map_image = pygame.image.load(image_path)

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

    def create_map_noise(self, ratio: int):
        ''' craete a random map using noise '''
        ...

    def create_map_digging(self, ratio: int):
        ''' craete a digging match map '''
        ...

    def create_map_surfaces(self, dims):
        """
        create all map related surfaces
        """
        self.game_map = pygame.Surface(dims)
        self.game_map.fill(SKY)
        self.worm_col_map = pygame.Surface(dims)
        self.worm_col_map.fill(SKY)
        self.objects_col_map = pygame.Surface(dims)
        self.objects_col_map.fill(SKY)

        self.ground_map = pygame.Surface(dims).convert_alpha()
        self.ground_secondary = pygame.Surface(dims).convert_alpha()
        # if self.darkness:
        #     self.darkMask = pygame.Surface(dims).convert_alpha()

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
        ##############################################
        
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