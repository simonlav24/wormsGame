
from random import choice

from common import GameVariables, EntityWorm
from game.game_play_mode.game_play_mode import GamePlayMode


class StatsGamePlay(GamePlayMode):
    def __init__(self):
        super().__init__()

        self.damage_this_turn: int = 0

        self.most_damage: int = -1
        self.most_damage_worm: EntityWorm = None

    def on_worm_damage(self, worm: EntityWorm, damage: int):
        if worm.get_team_data().team_name == GameVariables().player.get_team_data().team_name:
            return
        self.damage_this_turn += damage
    
    def on_turn_end(self):
        super().on_turn_end()

        # comment about damage
        current_worm_name = GameVariables().player.name_str
        current_worm_color = GameVariables().player.get_team_data().color
        worm_text_dict = {'text': current_worm_name, 'color': current_worm_color}

        if self.damage_this_turn > int(GameVariables().config.worm_initial_health * 2.5):
            if self.damage_this_turn == GameVariables().config.worm_initial_health * 3:
                GameVariables().commentator.comment([{'text': "THIS IS "}, worm_text_dict])
            else:
                comment = choice([
                        [{'text': 'awesome shot '}, worm_text_dict, {'text': '!'}],
                        [worm_text_dict, {'text': ' is on fire!'}],
                        [worm_text_dict, {'text': ' shows no mercy'}],
                    ])
                GameVariables().commentator.comment(comment)

        elif self.damage_this_turn > int(GameVariables().config.worm_initial_health * 1.5):
            comment = choice([
                        [{'text': 'good shot '}, worm_text_dict, {'text': '!'}],
                        [{'text': 'nicely done '}, worm_text_dict],
                    ])
            GameVariables().commentator.comment(comment)

        # update 
        if self.damage_this_turn > self.most_damage:
            self.most_damage = self.damage_this_turn
            self.most_damage_worm = GameVariables().player
        self.damage_this_turn = 0

    def on_worm_death(self, worm: EntityWorm):
        pass

    def debug_print(self) -> str:
        output = 'StatsGamePlay\n'
        output += f'{self.damage_this_turn=}\n'
        output += f'{self.most_damage=}\n'
        output += f'{self.most_damage_worm=}\n'
        return output