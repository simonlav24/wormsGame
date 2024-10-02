
import os
import pygame
from math import cos, pi, sin, atan2
from random import choice, randint
from typing import List, Tuple, Any

from common import PATH_ASSETS, feels, GameVariables, SingletonMeta, point2world, sprites, EntityPhysical
from common.vector import *

SKY = (0,0,0,0)
GRD = (255,255,255,255)

SKY_COL = (0,0,0)
GRD_COL = (255,255,255)

class ErrorImageNotFound(Exception):
    pass

def grab_maps(paths: List[str]) -> List[str]:
    ''' returns list of available map files '''
    maps = []
    for path in paths:
        if not os.path.isdir(path):
            continue
        for root, _, files in os.walk(path):
            for file in files:
                conditions = [
                    file.endswith('.png'),
                    'perlin' not in file,
                    'generated' not in file,
                    'noise' not in file,
                ]
                if not all(conditions):
                    continue
                maps.append(os.path.join(root, file))
    return maps

class MapManager(metaclass=SingletonMeta):
    def __init__(self) -> None:
        # default value for game map dimensions
        self.game_map: pygame.Surface = pygame.Surface((GameVariables().win_width, GameVariables().win_height))
        self.ground_map: pygame.Surface = None
        self.ground_secondary: pygame.Surface = None

        self.draw_ground_secondary = True
        self._is_digging_map = False

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
        self._is_digging_map = True

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
            try:
                map_at = self.game_map.get_at((int(pos[0]), int(pos[1])))
            except IndexError:
                return False
        except IndexError:
            return False

        return map_at == GRD

    def is_ground_around(self, place, radius = 5):
        for i in range(8):
            checkPos = place + Vector(radius * cos((i/4) * pi), radius * sin((i/4) * pi))
            if checkPos.x < 0 or checkPos.x > self.game_map.get_width() or checkPos.y < 0 or checkPos.y > self.game_map.get_height():
                return False
            try:
                at = (int(checkPos.x), int(checkPos.y))
                if self.game_map.get_at(at) == GRD or self.worm_col_map.get_at(at) != (0,0,0) or self.objects_col_map.get_at(at) != (0,0,0):
                    return True
            except IndexError:
                print("is_ground_around index error")
                
        return False

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

    def draw_land(self, win: pygame.Surface):
        if self.game_map.get_width() == 0:
            return
        if self.draw_ground_secondary:
            win.blit(self.ground_secondary, point2world((0,0)))
        win.blit(self.ground_map, point2world((0,0)))
        
        self.worm_col_map.fill(SKY)
        self.objects_col_map.fill(SKY)

    def get_normal(self, pos, vel: Vector, radius: int, wormCollision: bool, extraCollision: bool) -> Vector:
        ''' returns collision with world response '''
        response = Vector(0,0)
        angle = atan2(vel.y, vel.x)
        r = angle - pi
        while r < angle + pi:
            testPos = Vector((radius) * cos(r) + pos.x, (radius) * sin(r) + pos.y)
            if testPos.x >= self.game_map.get_width() or testPos.y >= self.game_map.get_height() - GameVariables().water_level or testPos.x < 0:
                if GameVariables().config.option_closed_map:
                    response += pos - testPos
                    r += pi /8
                    continue
                else:
                    r += pi /8
                    continue
            if testPos.y < 0:
                r += pi /8
                continue
            
            if self.game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
                response += pos - testPos
            if wormCollision and self.worm_col_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
                response += pos - testPos
            if extraCollision and self.objects_col_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
                response += pos - testPos
            
            r += pi /8
        return response
    
    def get_closest_pos_available(self, pos: Vector, radius: int):
        ''' return the closest position to pos that is not in ground '''
        r = 0
        found = None
        org_pos = vectorCopy(pos)
        t = 0
        while not found:
            check_pos = org_pos + t * vector_from_angle(r)
            if self.check_free_pos(radius, check_pos, True):
                found = check_pos
                break

            r += pi/8
            if r > 2*pi - 0.01 and r < 2*pi + 0.01:
                r = 0
                t += 1
                if t > 100:
                    return None
        return check_pos

    def girder(self, pos: Vector) -> None:
        ''' place girder in position '''
        surf = pygame.Surface((GameVariables().girder_size, 10)).convert_alpha()
        for i in range(GameVariables().girder_size // 16 + 1):
            surf.blit(sprites.sprite_atlas, (i * 16, 0), (64, 80, 16, 16))
        surf_ground = pygame.transform.rotate(surf, GameVariables().girder_angle)
        self.ground_map.blit(
            surf_ground,
            (int(pos[0] - surf_ground.get_width() / 2), int(pos[1] - surf_ground.get_height() / 2)) 
        )
        surf.fill(GRD)
        surfMap = pygame.transform.rotate(surf, GameVariables().girder_angle)
        self.game_map.blit(
            surfMap,
            (int(pos[0] - surfMap.get_width() / 2), int(pos[1] - surfMap.get_height() / 2))
        )

    def get_good_place(self, *, div = -1, girder_place = True) -> Vector:
        ''' return unobscured, unoccupied place on ground '''
        goodPlace = False
        counter = 0
        
        if div != -1:
            half = self.game_map.get_width() / GameVariables().num_of_teams
            slice = div % GameVariables().num_of_teams
            
            left = half * slice
            right = left + half
            if left <= 0:
                left += 6
            if right >= self.game_map.get_width():
                right -= 6
        else:
            left, right = 6, self.game_map.get_width() - 6
        
        if self._is_digging_map:
            while not goodPlace:
                place = Vector(randint(int(left), int(right)), randint(6, self.game_map.get_height() - 50))
                goodPlace = True
                for worm in GameVariables().get_worms():
                    if distus(worm.pos, place) < 5625:
                        goodPlace = False
                        break
                    if  not goodPlace:
                        continue
            return place
        
        while not goodPlace:
            # give rand place
            counter += 1
            goodPlace = True
            place = Vector(randint(int(left), int(right)), randint(6, self.game_map.get_height() - 6))
            
            # if in .ground_map 
            if self.is_ground_around(place):
                goodPlace = False
                continue
            
            if counter > 8000:
                # if too many iterations, girder place
                if not girder_place:
                    return None
                for worm in GameVariables().get_worms():
                    if distus(worm.pos, place) < 2500:
                        goodPlace = False
                        break
                if  not goodPlace:
                    continue
                self.girder(place + Vector(0, 20))
                return place
            
            # put place down
            y = place.y
            for i in range(self.game_map.get_height()):
                if y + i >= self.game_map.get_height():
                    goodPlace = False
                    break
                if (self.game_map.get_at((place.x, y + i)) == GRD
                    or self.worm_col_map.get_at((place.x, y + i)) != SKY_COL
                    or self.objects_col_map.get_at((place.x, y + i)) != SKY_COL):
                    y = y + i - 7
                    break
            if  not goodPlace:
                continue
            place.y = y
            
            # check for nearby worms in radius 50
            for worm in GameVariables().get_worms():
                if distus(worm.pos, place) < 2500:
                    goodPlace = False
                    break
            if  not goodPlace:
                continue
                    
            # check for nearby petrol cans in radius 30
            for can in GameVariables().get_obscuring_objects():
                if distus(can.pos, place) < 1600:
                    goodPlace = False
                    break
            if  not goodPlace:
                continue
            
            # if all conditions are met, make hole and place
            if self.is_ground_around(place):
                pygame.draw.circle(self.game_map, SKY, place.vec2tup(), 5)
                pygame.draw.circle(self.ground_map, SKY, place.vec2tup(), 5)
        return place
    
    def place_object(self, cls: Any, args, girder_place: bool=False) -> EntityPhysical:
        ''' create an instance of cls, return the last created'''
        place = self.get_good_place(girder_place=girder_place)
        if place:
            if args is None:
                instance = cls()
            else:
                instance = cls(*args)
            instance.pos = Vector(place.x, place.y - 2)
        else:
            return None
        return instance