

import pygame

from common import GameVariables, sprites
from common.vector import Vector

from game.game_play_mode.game_play_mode import GamePlayMode
from game.map_manager import MapManager, GRD


class ArenaGamePlay(GamePlayMode):
    def __init__(self):
        super().__init__()
        self.size = Vector()
        self.pos = Vector()
    
    def on_game_init(self):
        self.size = Vector(10 * 16, 10)
        self.pos = Vector(MapManager().game_map.get_width(), MapManager().game_map.get_height()) // 2 - self.size // 2

    def draw(self, win: pygame.Surface):
        super().draw(win)
        pygame.draw.rect(MapManager().game_map, GRD,(self.pos, self.size))
        for i in range(10):
            MapManager().ground_map.blit(sprites.sprite_atlas, self.pos + Vector(i * 16, 0), (64,80,16,16))

    def on_cycle(self):
        super().on_cycle()
        for worm in GameVariables().get_worms():
            check_pos = worm.pos + Vector(0, worm.radius * 2)
            if worm.pos.x > self.pos.x and worm.pos.x < self.pos.x + self.size.x and check_pos.y > self.pos.y and check_pos.y < self.pos.y + self.size.y:
                worm.give_point(1)
                
    

        





