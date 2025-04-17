''' arena game mode '''

from random import randint, uniform

import pygame

from common import GameVariables, sprites
from common.vector import Vector

from game.game_play_mode.game_play_mode import GamePlayMode
from game.map_manager import MapManager, GRD
from game.visual_effects import EffectManager
from game.world_effects import Earthquake

class ArenaGamePlay(GamePlayMode):
    ''' arena game mode '''
    def __init__(self) -> None:
        super().__init__()
        self.size = Vector()
        self.pos = Vector()

    def on_game_init(self, game_data: dict=None) -> None:
        self.size = Vector(10 * 16, 10)
        self.pos = Vector(
            randint(50, MapManager().game_map.get_width() - 50),
            randint(50, MapManager().game_map.get_height() - 50)
        )

    def step(self) -> None:
        super().step()
        if randint(0, 30) == 1:
            pos = Vector(self.pos[0] + uniform(0, 1) * self.size[0], self.pos[1])
            EffectManager().create_particle(pos, Vector(uniform(-1,1), -2), (255,255,255))

    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        pygame.draw.rect(MapManager().game_map, GRD,(self.pos, self.size))
        for i in range(10):
            MapManager().ground_map.blit(sprites.sprite_atlas, self.pos + Vector(i * 16, 0), (64,80,16,16))

    def on_turn_end(self) -> None:
        super().on_turn_end()
        for worm in GameVariables().get_worms():
            check_pos = worm.pos + Vector(0, worm.radius * 2)
            if worm.pos.x > self.pos.x and worm.pos.x < self.pos.x + self.size.x and check_pos.y > self.pos.y and check_pos.y < self.pos.y + self.size.y:
                worm.give_point(1)
        
        if randint(1, 10) == 1:
            GameVariables().commentator.comment([{'text': 'moving arena'}])
            Earthquake(1 * GameVariables().fps, True, 0.5)
            self.pos = Vector(
                randint(50, MapManager().game_map.get_width() - 50),
                randint(50, MapManager().game_map.get_height() - 50)
            )
    
    def is_points_game(self) -> bool:
        return True
