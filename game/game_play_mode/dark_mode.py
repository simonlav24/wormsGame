

from typing import List

import pygame

from common import GameVariables, DARK_COLOR, LIGHT_RADIUS, point2world

from game.game_play_mode.game_play_mode import GamePlayMode
from game.team_manager import TeamManager
from game.visual_effects import EffectManager
from weapons.weapon_manager import WeaponManager


class DarknessGamePlay(GamePlayMode):

    def on_game_init(self, game_data: dict=None):
        super().on_game_init(game_data)
        
        # add initial flares
        for team in TeamManager().teams:
            team.ammo(WeaponManager()["flare"], 3)
        
        EffectManager().is_dark_mode = True

    def step(self):
        super().step()
    
    def on_turn_begin(self):
        # restock flares
        for team in TeamManager().teams:
            team.ammo(WeaponManager()["flare"], 1)
            if team.ammo(WeaponManager()["flare"]) > 3:
                team.ammo(WeaponManager()["flare"], -1)

        # flares reduction
        for light_source in GameVariables().get_light_sources():
            light_source.light_radius -= 10
    
    def draw(self, win: pygame.Surface):
        super().draw(win)
        center = GameVariables().player.pos
        dark_mask = EffectManager().get_dark_mask(center)
        win.blit(dark_mask, (0,0))




