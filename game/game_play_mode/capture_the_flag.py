

import pygame

from common import GameVariables, EntityWorm, point2world
from common.vector import Vector

from game.game_play_mode.game_play_mode import GamePlayMode
from entities.flag import Flag
from entities.deployables import deploy_pack


class CTFGamePlay(GamePlayMode):
    def __init__(self):
        super().__init__()
        self.flag: Flag = None
        self.current_holder: EntityWorm = None

    def on_game_init(self):
        self.flag = deploy_pack(Flag)
        GameVariables().cam_track = self.flag

    def step(self):
        super().step()

        # check if flag has holder
        if self.flag is not None:
            if self.flag.holder is not None and self.flag.is_gone:
                # worm is holding the flag
                self.current_holder = self.flag.holder

            if self.flag.holder is None and self.flag.is_gone:
                # flag is gone but no holder
                self.flag = deploy_pack(Flag)
                GameVariables().cam_track = self.flag

    def on_worm_damage(self, worm: EntityWorm, damage: int):
        super().on_worm_damage(worm, damage)
        if worm is self.current_holder:
            # worm withdraws flag
            self.flag = Flag(self.current_holder.pos)
            self.current_holder = None


    def draw(self, win: pygame.Surface):
        super().draw(win)
        if self.current_holder is not None:
            pygame.draw.line(win, (51, 51, 0), point2world(self.current_holder.pos), point2world(self.current_holder.pos + Vector(0, -3 * self.current_holder.radius)))
            pygame.draw.rect(win, (220,0,0), (point2world(self.current_holder.pos + Vector(1, -3 * self.current_holder.radius)), (self.current_holder.radius * 2, self.current_holder.radius * 2)))


    def on_cycle(self):
        super().on_cycle()
        if self.current_holder:
            self.current_holder.give_point(1)


        





