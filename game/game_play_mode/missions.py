
from typing import Dict, List
from random import choice
from math import cos, sin, pi

import pygame

from common import GameVariables, EntityWorm, GameState, point2world, draw_dir_indicator, draw_target, fonts, WHITE, GameGlobals
from common.vector import Vector, distus, vector_from_angle

from game.game_play_mode.game_play_mode import GamePlayMode
from game.game_play_mode.stats import StatsGamePlay
from game.map_manager import MapManager, GRD
from game.team_manager import TeamManager
from game.time_manager import TimeManager


class MissionsGamePlay(GamePlayMode):
    def __init__(self, stats: StatsGamePlay):
        super().__init__()
        self.available_missions = {
            "kill a worm": 1,
            "kill _": 3,
            "hit a worm from _": 1,
            "hit _": 2,
            "reach marker": 1,
            "double kill": 3,
            "triple kill": 4,
            "hit highest worm": 1,
            "hit distant worm": 1,
            "hit 3 worms": 2, 
            "above 50 damage": 1,
        }
        self.worm_to_missions: Dict[EntityWorm, List[Mission]] = {}
        self.killed_this_turn = []
        self.hit_this_turn = []
        self.stats = stats
        self._log = ''
    
    def on_game_init(self):
        super().on_game_init()
        TimeManager().turnTime += 10
        self.cycle()

    def on_turn_begin(self):
        super().on_turn_begin()
        self.cycle()

    def assign_missions(self, worm: EntityWorm, oldMission=None):
        # choose 3 missions from available_missions
        if worm in self.worm_to_missions:
            self.evaluate_missions(worm, oldMission)
            return
        
        worm_missions = []
        self.worm_to_missions[worm] = worm_missions
        for _ in range(3):
            newMission = self.assign_one_mission(worm)
            worm_missions.append(newMission)
            self._log += f"{worm.name_str} received mission {newMission.mission_type}\n"
             
    def evaluate_missions(self, worm: EntityWorm, oldMission=None):
        replaceMissions = []

        # check if any of the missions are completed and remove them
        for mission in self.worm_to_missions[worm]:
            if mission.completed and mission.readyToChange:
                replaceMissions.append((mission, self.worm_to_missions[worm].index(mission)))

        currentWormMissionsTypes = [i.mission_type for i in self.worm_to_missions[worm]]

        # if mission_type "hit _" or "kill _" or "hit a worm from _" and target is dead, remove mission
        if "hit _" in currentWormMissionsTypes or "kill _" in currentWormMissionsTypes:
            for mission in self.worm_to_missions[worm]:
                if mission.mission_type in ["hit _", "kill _"]:
                    if mission.target not in GameVariables().get_worms() or not mission.target.alive:
                        replaceMissions.append((mission, self.worm_to_missions[worm].index(mission)))
        if "hit a worm from _" in currentWormMissionsTypes:
            for mission in self.worm_to_missions[worm]:
                if mission.mission_type == "hit a worm from _":
                    if len(mission.team_target) == 0:
                        replaceMissions.append((mission, self.worm_to_missions[worm].index(mission)))

        # count alive worms from other teams
        aliveWorms = 0
        for w in GameVariables().get_worms():
            if w.alive and w.get_team_data() != worm.get_team_data():
                aliveWorms += 1
        
        if aliveWorms < 5:
            for mission in self.worm_to_missions[worm]:
                if mission.mission_type == "hit 3 worms":
                    replaceMissions.append((mission, self.worm_to_missions[worm].index(mission)))
        if aliveWorms < 3:
            for mission in self.worm_to_missions[worm]:
                if mission.mission_type == "triple kill":
                    replaceMissions.append((mission, self.worm_to_missions[worm].index(mission)))
        if aliveWorms < 2:
            for mission in self.worm_to_missions[worm]:
                if mission.mission_type == "double kill":
                    replaceMissions.append((mission, self.worm_to_missions[worm].index(mission)))

        for mission in replaceMissions:
            if mission[0] in self.worm_to_missions[worm]:
                self.worm_to_missions[worm].remove(mission[0])
                newMission = self.assign_one_mission(worm, oldMission)
                self.worm_to_missions[worm].insert(mission[1], newMission)
                # self.worm_to_missions[worm].append(newMission)
                self._log += f"{worm.name_str} received mission {newMission.mission_type}\n"

        if len(self.worm_to_missions[worm]) < 3:
            for i in range(3 - len(self.worm_to_missions[worm])):
                newMission = self.assign_one_mission(worm, oldMission)
                self.worm_to_missions[worm].append(newMission)
                # self.worm_to_missions[worm].append(newMission)
                self._log += f"{worm.name_str} received mission {newMission.mission_type}\n"

        self.update_display()

    def assign_one_mission(self, worm, oldMission=None):
        # figure out which missions are available
        available_missions = list(self.available_missions.keys())
        for mission in self.worm_to_missions[worm]:
            available_missions.remove(mission.mission_type)
        
        if oldMission:
            available_missions.remove(oldMission.mission_type)

        # check if worms or teams exist
        if len(self.get_alive_worms_from_other_teams()) == 0:
            for i in ["hit a worm from _", "kill _", "hit _"]:
                if i in available_missions:
                    available_missions.remove(i)
        
        # choose a mission_type and create it
        chosenMission = choice(available_missions)
        newMission = Mission(chosenMission, self.available_missions[chosenMission])
        if "_" in chosenMission:
            # targeted mission
            if "kill" in chosenMission:
                newMission.target = self.choose_target()
            elif "from" in chosenMission:
                newMission.team_target = self.choose_team_target()
            elif "hit" in chosenMission:
                newMission.target = self.choose_target()
        
        if chosenMission == "reach marker":
            newMission.marker = self.create_marker()

        return newMission
    
    def get_alive_worms_from_other_teams(self):
        not_from_team = GameVariables().player.get_team_data()
        worms = []
        for worm in GameVariables().get_worms():
            if worm.get_team_data() == not_from_team:
                continue
            if not worm.alive:
                continue
            worms.append(worm)
        return worms

    def create_marker(self) -> Vector:
        return MapManager().get_good_place()

    def choose_target(self):
        worms = self.get_alive_worms_from_other_teams()
        return choice(worms)

    def choose_team_target(self):
        not_from_team = GameVariables().player.get_team_data()
        teams = []
        for team in TeamManager().teams:
            if team.data == not_from_team:
                continue
            if len(team.worms) == 0:
                continue
            teams.append(team)
        if len(teams) == 0:
            return None
        return choice(teams)

    def remove_mission(self, mission):
        if mission in self.worm_to_missions[GameVariables().player]:
            self.worm_to_missions[GameVariables().player].remove(mission)

        if GameVariables().game_state == GameState.PLAYER_PLAY:
            self.assign_missions(GameVariables().player, mission)

    def on_worm_death(self, worm: EntityWorm):
        super().on_worm_death(worm)
        if worm == GameVariables().player:
            return
        self.killed_this_turn.append(worm)
        self.check_missions(["kill a worm", "kill _", "double kill", "triple kill", "above 50 damage"])

    def on_worm_damage(self, worm: EntityWorm, damage: int):
        super().on_worm_damage(worm, damage)
        if worm in self.hit_this_turn or worm == GameVariables().player:
            self.check_missions(["above 50 damage"])
            return
        self.hit_this_turn.append(worm)
        self.check_missions(["hit a worm from _", "hit _", "hit 3 worms", "above 50 damage"])
        # check highest
        worms: List[EntityWorm] = []
        for w in GameVariables().get_worms():
            if w.alive and w.get_team_data() != GameVariables().player.get_team_data():
                worms.append(w)
        
        highestWorm = min(worms, key=lambda w: w.pos.y)
        if worm == highestWorm:
            self.check_missions(["hit highest worm"])
        # check distance
        if distus(worm.pos, GameVariables().player.pos) > 300 * 300:
            self.check_missions(["hit distant worm"])

    def check_missions(self, missionTypes):
        for mission in self.worm_to_missions[GameVariables().player]:
            if mission.mission_type in missionTypes:
                mission.check(self)

    def cycle(self):
        # start of turn, assign missions to current worm
        self.assign_missions(GameVariables().player)
        self.update_display()
        self.killed_this_turn.clear()
        self.hit_this_turn.clear()
        self.marker = None

        if "reach marker" in self.worm_to_missions[GameVariables().player]:
            self.create_marker()

    def update_display(self):
        for mission in self.worm_to_missions[GameVariables().player]:
            mission.update_display()

    def step(self):
        if GameVariables().player == None:
            return
        for mission in self.worm_to_missions[GameVariables().player]:
            mission.step(self)

    def draw(self, win: pygame.Surface):
        super().draw(win)
        if GameVariables().player == None:
            return
        current_worm = GameVariables().player
        # draw missions gui in lower right of screen
        yOffset = 0
        for mission in self.worm_to_missions[current_worm]:
            surf = mission.surf
            win.blit(surf, (GameGlobals().win_width - surf.get_width() - 5, GameGlobals().win_height - surf.get_height() - 5 - yOffset))
            yOffset += surf.get_height() + 2
        
        # draw mission indicators
        for mission in self.worm_to_missions[current_worm]:
            mission.draw(win)

class Mission:
    def __init__(self, mission_type, reward):
        self.mission_type = mission_type
        self.reward = reward
        self.target = None
        self.team_target = None
        self.marker = None
        self.completed = False
        self.readyToChange = False
        self.timer = 3 * GameVariables().fps
        self.textSurf = None
        self.surf = None

    def __str__(self):
        return self.mission_type

    def __repr__(self):
        return self.mission_type

    def mission_to_string(self):
        string = self.mission_type
        if "_" in string:
            if "from" in string:
                string = string.replace("_", self.team_target.name)
            elif "kill" in string or "hit" in string:
                string = string.replace("_", self.target.name_str)

        string += " (" + str(self.reward) + ")"
        return string

    def complete(self, stringReplacement = None):
        string = self.mission_type
        if "_" in string:
            string = string.replace("_", stringReplacement)
        comment = [
            {'text': 'mission '}, {'text': string, 'color': GameVariables().player.team.color}, {'text': ' passed'}
        ]

        GameVariables().commentator.comment(comment)
        GameVariables().player.give_point(self.reward)

        self.completed = True
        # MissionManager._log += f"{GameVariables().player.name_str} completed mission {self.mission_type} {str(self.reward)}\n"
        
    def check(self, mission_manager: MissionsGamePlay):
        # check complete
        if self.completed:
            return
        if self.mission_type == "kill a worm":
            if len(mission_manager.killed_this_turn) > 0:
                self.complete()
        elif self.mission_type == "reach marker":
            self.complete()
            self.marker = None
        elif self.mission_type == "double kill":
            if len(mission_manager.killed_this_turn) > 1:
                self.complete()
        elif self.mission_type == "triple kill":
            if len(mission_manager.killed_this_turn) > 2:
                self.complete()
        elif self.mission_type == "hit highest worm":
            self.complete()
        elif self.mission_type == "hit distant worm":
            self.complete()
        elif self.mission_type == "hit 3 worms":
            if len(mission_manager.hit_this_turn) > 2:
                self.complete()
        elif self.mission_type == "kill _":
            if self.target in mission_manager.killed_this_turn:
                self.complete(self.target.name_str)
        elif self.mission_type == "hit a worm from _":
            team = self.team_target
            for worm in mission_manager.hit_this_turn:
                if worm.team == team:
                    self.complete(team.name)
        elif self.mission_type == "hit _":
            if self.target in mission_manager.hit_this_turn:
                self.complete(self.target.name_str)
        elif self.mission_type == "above 50 damage":
            if mission_manager.stats.damage_this_turn >= 50:
                self.complete()

    def step(self, mission_manager: MissionsGamePlay):
        if self.marker:
            if distus(self.marker, GameVariables().player.pos) < 20 * 20:
                self.check(mission_manager)
        if self.completed:
            self.timer = max(0, self.timer - 1)
            self.update_display()
            if self.timer == 0 and GameVariables().game_state == GameState.PLAYER_PLAY:
                self.readyToChange = True
                mission_manager.remove_mission(self)

    def draw(self, win: pygame.Surface):
        # draw indicators
        # draw distance indicator
        current_worm = GameVariables().player
        if self.mission_type == "hit distant worm":
            radius = 300
            da = 2 * pi / 40
            time = da * int(GameVariables().time_overall / 2)
            time_angles = [time + i * pi / 2 for i in range(4)]
            for ta in time_angles:
                for i in range(9):
                    size = int(i / 3)
                    pos = current_worm.pos + vector_from_angle(ta + i * da, radius)
                    pygame.draw.circle(win, (255,0,0), point2world(pos), size)
        # draw marker
        elif self.marker:
            offset = sin(GameVariables().time_overall / 5) * 5
            pygame.draw.circle(win, (255,0,0), point2world(self.marker), 10 + offset, 1)
            draw_dir_indicator(win, self.marker)
        # draw indicators
        elif self.target:
            draw_dir_indicator(win, self.target.pos)
            draw_target(win, self.target.pos)

    def update_display(self):
        if not self.textSurf:
            self.textSurf = fonts.pixel5.render(self.mission_to_string(), False, WHITE)
            self.surf = pygame.Surface((self.textSurf.get_width() + 2, self.textSurf.get_height() + 2))

        # interpolate from Black to Green base on timer [0, 3 * fps]
        amount = (1 - self.timer / (3 * GameVariables().fps)) * 4
        back_color = (0, min(255 * amount, 255), 0)

        self.surf.fill(back_color)
        self.surf.blit(self.textSurf, (1,1))