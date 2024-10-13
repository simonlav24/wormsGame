import os
from random import choice, uniform

from common import GameVariables, GameGlobals, GameState, fonts, Sickness, DamageType, RandomMode, ICreateGame

from game.game_play_mode import SuddenDeathGamePlay
from game.team_manager import Team, TeamManager
from game.time_manager import TimeManager
from weapons.weapon_manager import WeaponManager
from game.world_effects import Earthquake
from entities.deployables import deploy_pack, HealthPack, WeaponPack, UtilityPack

from weapons.bubble import Bubble

def add_to_record(dic):
    keys = ["time", "winner", "mostDamage", "damager", "mode", "points"]
    if not os.path.exists("wormsRecord.xml"):
        with open("wormsRecord.xml", "w+") as file:
            file.write("<data>\n")
            file.write("<game")
            for key in keys:
                if key in dic.keys():
                    file.write(" " + key + '="' + str(dic[key]) + '"')
            file.write("/>\n</data>")
            return
    
    with open("wormsRecord.xml", "r") as file:
        contents = file.readlines()
        index = contents.index("</data>")
    
    string = "<game"
    for key in keys:
        if key in dic.keys():
            string += " " + key + '="' + str(dic[key]) + '"'
    string += "/>\n"
    contents.insert(index, string)
    
    with open("wormsRecord.xml", "w") as file:
        contents = "".join(contents)
        file.write(contents)

def check_winners() -> bool:
    game_over = False
    last_team: Team = None

    # check for last team standing
    teams = [team for team in TeamManager().teams if len(team.worms) > 0]
    if len(teams) == 1:
        game_over = True
        last_team = teams[0]
    if len(teams) == 0:
        game_over = True
    
    game_over |= GameVariables().game_mode.is_game_over()

    if not game_over:
        return False
    
    # game over
    winning_team: Team = None
    points_mode = GameVariables().game_mode.is_points_game()
    
    # determine winning team
    if not points_mode:
        winning_team = last_team
    else:
        if last_team is not None:
            last_team.points += GameVariables().game_mode.win_bonus()
        finals = sorted(TeamManager().teams, key = lambda x: x.points)
        winning_team = finals[-1]
    
    # declare winner
    if winning_team is not None:
        print("Team", winning_team.name, "won!")
        if len(winning_team.worms) > 0:
            GameVariables().cam_track = winning_team.worms[0]
        GameVariables().commentator.comment([
            {'text': 'team '},
            {'text': winning_team.name, 'color': winning_team.color},
            {'text': ' Won!'}
        ])
    else:
        print("Tie!")
        GameVariables().commentator.comment([{'text': 'its a tie!'}])
    
    # todo: add to dict
    # todo: save win as image
    return True

# def _check_winners() -> bool:
# 	end = False
# 	lastTeam = None
# 	count = 0
# 	pointsGame = False
# 	for team in TeamManager().teams:
# 		if len(team.worms) == 0:
# 			count += 1
# 	if count == GameVariables().num_of_teams - 1:
# 		# one team remains
# 		end = True
# 		for team in TeamManager().teams:
# 			if not len(team.worms) == 0:
# 				lastTeam = team
# 	if count == GameVariables().num_of_teams:
# 		# no team remains
# 		end = True
        
# 	if not end:
# 		return False
# 	# game end:
# 	dic = {}
# 	winningTeam = None
    
    
# 	# win points:
# 	if pointsGame:
# 		for team in TeamManager().teams:
# 			print("[ |", team.name, "got", team.points, "points! | ]")
# 		teamsFinals = sorted(TeamManager().teams, key = lambda x: x.points)
# 		winningTeam = teamsFinals[-1]
# 		print("[most points to team", winningTeam.name, "]")
# 		dic["points"] = str(winningTeam.points)
# 	# regular win:
# 	else:
# 		winningTeam = lastTeam
# 		if winningTeam:
# 			print("[last team standing is", winningTeam.name, "]")
    
# 	if end:
# 		if winningTeam is not None:
# 			print("Team", winningTeam.name, "won!")
# 			dic["time"] = str(GameVariables().time_overall // GameVariables().fps)
# 			dic["winner"] = winningTeam.name
# 			if Game._game.mostDamage[1]:
# 				dic["mostDamage"] = str(int(Game._game.mostDamage[0]))
# 				dic["damager"] = Game._game.mostDamage[1]
# 			add_to_record(dic)
# 			if len(winningTeam.worms) > 0:
# 				GameVariables().cam_track = winningTeam.worms[0]
# 			GameVariables().commentator.comment([
# 				{'text': 'team '},
# 				{'text': winningTeam.name, 'color': winningTeam.color},
# 				{'text': ' Won!'}
# 			])

# 		else:
# 			GameVariables().commentator.comment([{'text': 'its a tie!'}])
# 			print("Tie!")
        
# 		# add teams to dic
# 		dic["teams"] = {}
# 		for team in TeamManager().teams:
# 			dic["teams"][team.name] = [team.color, team.points]

# 		Game._game.endGameDict = dic
# 		GameVariables().state_machine.update(GameState.WIN)
        
# 		GroundScreenShoot = pygame.Surface((MapManager().ground_map.get_width(), MapManager().ground_map.get_height() - GameVariables().water_level), pygame.SRCALPHA)
# 		GroundScreenShoot.blit(MapManager().ground_map, (0,0))
# 		pygame.image.save(GroundScreenShoot, "lastWormsGround.png")
# 	return end


def deploy_crate() -> None:
    # deploy crate if privious turn was last turn in round
    if ((GameVariables().game_turn_count) % (GameVariables().turns_in_round)) == (GameVariables().turns_in_round - 1):
        comments = [
            [{'text': 'a jewel from the heavens!'}],
            [{'text': 'its raining crates, halelujah!'}],
            [{'text': ' '}],
        ]
        GameVariables().commentator.comment(choice(comments))

        for _ in range(GameVariables().config.deployed_packs):
            w = deploy_pack(choice([HealthPack, UtilityPack, WeaponPack]))
            GameVariables().cam_track = w

def sudden_death():
    GameVariables().hud.add_toast(fonts.pixel10.render("sudden death", False, (220,0,0)))
    Earthquake(1.5 * GameGlobals().fps, decorative=True, strength=0.25)
    GameVariables().game_mode.add_mode(SuddenDeathGamePlay())
    GameVariables().is_sudden_death = True

def cycle_worms() -> GameState:
    ''' reset special effect
        comments about damage
        check for winners
        flare reduction
        sick worms
        chose next worm
    '''

    # reset special effects:
    GameVariables().physics.global_gravity = 0.2
    GameVariables().damage_mult = 0.8
    GameVariables().boom_radius_mult = 1
    GameVariables().mega_weapon_trigger = False
    GameVariables().aim_aid = False

    # release worm tool
    worm_tool = GameVariables().player.get_tool()
    if worm_tool is not None:
        worm_tool.release()
    
    if check_winners():
        return GameState.WIN

    new_round = False
    GameVariables().game_turn_count += 1
    if GameVariables().game_turn_count % GameVariables().turns_in_round == 0:
        GameVariables().game_round_count += 1
        new_round = True
    
    if new_round:
        GameVariables().config.rounds_for_sudden_death -= 1
        if GameVariables().config.rounds_for_sudden_death == 0:
            sudden_death()
        GameVariables().game_mode.on_new_round()
    
    # update stuff
    GameVariables().get_debries().clear()
    Bubble.cought = []
    
    # change wind:
    GameVariables().physics.wind = uniform(-1, 1)
    
    # sick:
    for worm in GameVariables().get_worms():
        if worm.sick != Sickness.NONE and worm.health > 5:
            worm.damage(min(int(5 / GameVariables().damage_mult) + 1, int((worm.health - 5) / GameVariables().damage_mult) + 1), DamageType.SICK)
        
    # select next team
    index = TeamManager().teams.index(TeamManager().current_team)
    index = (index + 1) % GameVariables().num_of_teams
    TeamManager().current_team = TeamManager().teams[index]
    while not len(TeamManager().current_team.worms) > 0:
        index = TeamManager().teams.index(TeamManager().current_team)
        index = (index + 1) % GameVariables().num_of_teams
        TeamManager().current_team = TeamManager().teams[index]
        
    # sort worms by health for drawing
    GameVariables().get_physicals().sort(key = lambda worm: worm.health if worm.health else 0)
    
    # end turn
    GameVariables().on_turn_end()
    GameVariables().game_mode.on_turn_end()

    # actual worm switch:
    switched = False
    while not switched:
        w = TeamManager().current_team.worms.pop(0)
        TeamManager().current_team.worms.append(w)
        if w.sleep:
            w.sleep = False
            continue
        switched = True
        
    if GameVariables().config.random_mode == RandomMode.COMPLETE: # complete random
        TeamManager().current_team = choice(TeamManager().teams)
        while not len(TeamManager().current_team.worms) > 0:
            TeamManager().current_team = choice(TeamManager().teams)
        w = choice(TeamManager().current_team.worms)
    if GameVariables().config.random_mode == RandomMode.IN_TEAM: # random in the current team
        w = choice(TeamManager().current_team.worms)

    GameVariables().player = w
    GameVariables().cam_track = GameVariables().player
    GameVariables().player_can_move = True

    GameVariables().on_turn_begin()
    GameVariables().game_mode.on_turn_begin()

    WeaponManager().switch_weapon(WeaponManager().current_weapon)
    return GameState.PLAYER_PLAY


class StateMachine:
    def __init__(self, game_creator: ICreateGame):
        self.game_creator = game_creator
        self.is_stable_check = False
        self.stable_count = 0
        self.stable_max_count = 10
        self.next_state = GameState.RESET

    def step(self) -> None:
        if self.is_stable_check:
            self.stable_count += 1
            if self.stable_count == self.stable_max_count:
                self.stable_count = 0
                self.is_stable_check = False
                self.update()

    def stable_check(self, max_count=10) -> None:
        self.is_stable_check = True
        self.stable_max_count = max_count
        self.stable_count = 0

    def distable(self) -> None:
        self.stable_count = 0

    def update(self, state: GameState = None) -> None:
        ''' set state to new state and handle state '''

        if state is None:
            state = self.next_state
        GameVariables().game_state = state
        
        if state == GameState.RESET:
            GameVariables().game_stable = False
            
            self.game_creator.create_new_game()
            self.update(GameState.PLAYER_PLAY)
        
        elif state == GameState.PLAYER_PLAY:
            self.next_state = GameState.PLAYER_RETREAT
        
        elif state == GameState.PLAYER_RETREAT:
            self.next_state = GameState.WAIT_STABLE
        
        elif state == GameState.WAIT_STABLE:
            self.stable_check()
            self.next_state = GameState.AUTONOMOUS_PLAY
        
        elif state == GameState.AUTONOMOUS_PLAY:
            self.stable_check()
            GameVariables().engage_autonomous()
            self.next_state = GameState.DEPLOYEMENT
        
        elif state == GameState.DEPLOYEMENT:
            self.stable_check()
            deploy_crate()
            GameVariables().game_mode.on_deploy()
            if GameVariables().is_sudden_death:
                self.next_state = GameState.SUDDEN_DEATH_PLAY
            else:
                self.next_state = GameState.TURN_CYCLE

        elif state == GameState.SUDDEN_DEATH_PLAY:
            GameVariables().game_mode.on_sudden_death_turn()
            self.stable_check()
            self.next_state = GameState.TURN_CYCLE

        elif state == GameState.TURN_CYCLE:
            next_state = cycle_worms()
            TimeManager().time_reset()
            self.update(next_state)

        elif state == GameState.WIN:
            self.stable_check(3 * GameGlobals().fps)
            self.next_state = GameState.GAME_OVER
        
        elif state == GameState.GAME_OVER:
            GameVariables().game_end = True
