
from common import GameVariables, EntityWorm
from game.game_play_mode.game_play_mode import GamePlayMode


class PointsGamePlay(GamePlayMode):
    
    def on_worm_damage(self, worm: EntityWorm, damage: int):
        if worm.get_team_data().team_name == GameVariables().player.get_team_data().team_name:
            return
        GameVariables().player.give_point(damage)
    
    def on_worm_death(self, worm: EntityWorm):
        if worm.get_team_data().team_name == GameVariables().player.get_team_data().team_name:
            return
        GameVariables().player.give_point(50)
    
    def win_bonus(self) -> int:
        return 150

    def is_points_game(self) -> bool:
        return True