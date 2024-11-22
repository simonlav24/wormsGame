
from enum import Enum, auto
from typing import Dict
from pathlib import Path

import pygame

from common import SingletonMeta

class SfxIndex(Enum):
    NONE = auto()
    BOOM1 = auto()
    BOOM2 = auto()
    BOOM3 = auto()
    FIRE_MISSILE = auto()
    THROW1 = auto()
    THROW2 = auto()
    THROW3 = auto()
    SPLASH1 = auto()
    SPLASH2 = auto()
    SPLASH3 = auto()
    COL1 = auto()
    COL2 = auto()
    COL3 = auto()
    COL4 = auto()
    FIRE_LOOP = auto()
    JUMP1 = auto()
    JUMP2 = auto()
    JUMP3 = auto()
    HURT1 = auto()
    HURT2 = auto()
    HURT3 = auto()
    GUN_SHOT1 = auto()
    GUN_SHOT2 = auto()
    GUN_SHOT3 = auto()
    DRILL_LOOP = auto()
    THRUST_LOOP = auto()
    GAS_LOOP = auto()
    MINE_ACTIVATE = auto()
    MINE_LOOP = auto()
    ELECTRICITY_LOOP = auto()
    BOW = auto()
    ARROW_HIT = auto()
    GAMMA_RAY = auto()
    LASER_LOOP = auto()
    BUBBLE_BLOW = auto()
    BUBBLE_BURST = auto()
    PLANT_LOOP = auto()
    PLANT_BITE = auto()
    PLANT_OPEN = auto()
    ACID_LOOP = auto()
    SHEEP_BAA1 = auto()
    SHEEP_BAA2 = auto()
    BAT_LOOP = auto()
    PUNCH = auto()
    BASEBALL = auto()
    GIRDER = auto()
    ROPE = auto()
    PARACHUTE = auto()
    TURRET_ACTIVATE = auto()
    PORTAL = auto()
    TRAMPOLINE_BOUNCE = auto()
    AIRSTRIKE = auto()
    CHUM_SPLASH = auto() # prob
    EARTHQUAKE_LOOP = auto()
    BEES_LOOP = auto()
    VORTEX_IN = auto()
    VORTEX_OUT = auto()

    BULL = auto()
    EARTH_SPIKE = auto()
    ICICLE = auto()
    FIREBALL = auto()
    TORNADO_LOOP = auto()
    PICKAXE = auto()
    BUILD = auto()


class EmptySound:
    def play(self, index: SfxIndex):
        return


class Sfx(metaclass=SingletonMeta):
    def __init__(self):
        self.sound_dict: Dict[SfxIndex, pygame.mixer.Sound] = {}
        for element in SfxIndex:
            if element is SfxIndex.NONE:
                self.sound_dict[element] = EmptySound()
                continue

            path = rf'assets/sfx/{element.name.lower()}.mp3'
            if not Path(path).exists():
                print(f'no sound {element.name}')
                continue
            self.sound_dict[element] = pygame.mixer.Sound(path)

        self.in_loop = {index : 0 for index in SfxIndex}
    
    def play(self, index: SfxIndex) -> None:
        if index == SfxIndex.NONE:
            return
        self.sound_dict[index].play()

    def loop_increase(self, index: SfxIndex) -> None:
        play = self.in_loop[index] == 0
        self.in_loop[index] += 1
        if play:
            self.sound_dict[index].play(-1)
    
    def loop_ensure(self, index: SfxIndex) -> None:
        ''' if not playing play in loop. if playing, do nothing '''
        if self.in_loop[index] > 0:
            return
        self.loop_increase(index)
    
    def loop_decrease(self, index: SfxIndex, fade_out_ms=0, force_stop=False) -> None:
        if not index in self.in_loop.keys():
            return
        self.in_loop[index] -= 1
        if force_stop:
            self.in_loop[index] = 0
        if self.in_loop[index] == 0:
            self.sound_dict[index].fadeout(fade_out_ms)
            

