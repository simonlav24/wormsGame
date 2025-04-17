
from typing import Dict, List
from random import randint, choice

from common import GameVariables, ArtifactType
from common.vector import Vector, dist

from game.map_manager import MapManager
from game.game_play_mode.game_play_mode import GamePlayMode
from game.team_manager import TeamManager, Team
from weapons.weapon_manager import WeaponManager
from entities.deployables import deploy_pack

from weapons.artifacts.deployable_artifact import DeployableArtifact
from weapons.artifacts.mjolnir_artifact import MjolnirArtifact
from weapons.artifacts.plant_master import PlantMasterLeaf
from weapons.artifacts.avatar_artifact import AvatarArtifact
from weapons.artifacts.minecraft_artifact import PickAxeArtifact


def drop_artifact(artifact, artifact_type: ArtifactType, pos: Vector, comment=False) -> DeployableArtifact:
    deploy = False
    if not pos:
        # find good position for artifact
        goodPlace = False
        count = 0
        deploy = False
        while not goodPlace:
            pos = Vector(randint(20, MapManager().game_map.get_width() - 20), -50)
            if not MapManager().is_ground_at((pos.x, 0)):
                goodPlace = True
            count += 1
            if count > 2000:
                break
        if not goodPlace:
            deploy = True
    
    if not deploy:
        m = artifact(pos, artifact_type)
    else:
        m = deploy_pack(artifact)
    
    if comment:
        m.comment_creation()
    GameVariables().cam_track = m
    return m



class ArtifactsGamePlay(GamePlayMode):
    def __init__(self):
        super().__init__()
        self.team_artifact_dict: Dict[Team, ArtifactType] = {}
        self.world_artifacts = [
            ArtifactType.MJOLNIR,
            ArtifactType.PLANT_MASTER,
            ArtifactType.AVATAR,
            ArtifactType.MINECRAFT
        ]
        self.artifact_classes = {
            ArtifactType.MJOLNIR: MjolnirArtifact,
            ArtifactType.PLANT_MASTER: PlantMasterLeaf,
            ArtifactType.AVATAR: AvatarArtifact,
            ArtifactType.MINECRAFT: PickAxeArtifact,
        }
        self.triger_artifact = False
        self.deployed_artifacts: List[DeployableArtifact] = []
    
    def on_game_init(self, game_data: dict=None):
        super().on_game_init(game_data)
        for team in TeamManager().teams:
            self.team_artifact_dict[team] = ArtifactType.NONE

    def step(self):
        super().step()

        # check for picked
        current_player = GameVariables().player
        current_team = {team.name: team for team in self.team_artifact_dict.keys()}[current_player.get_team_data().team_name]
        artifacts_to_remove = []
        if self.team_artifact_dict[current_team] == ArtifactType.NONE:
            for artifact in self.deployed_artifacts:
                if dist(current_player.pos, artifact.pos) < artifact.radius + current_player.radius + 5 and current_player.alive: 
                    # pick up
                    artifact.remove_from_game()
                    comment_text = artifact.comment_pick()
                    artifacts_to_remove.append(artifact)
                    comment = [
                        {'text': comment_text[0]},
                        {'text': current_player.name_str, 'color': current_team.color},
                        {'text': comment_text[1]}
                    ]
                    GameVariables().commentator.comment(comment)
                    # give weapons
                    self.give_artifacts_weapons(current_team, artifact.artifact_type)
                    self.team_artifact_dict[current_team] = artifact.artifact_type
        self.deployed_artifacts = [a for a in self.deployed_artifacts if a not in artifacts_to_remove]
        artifacts_to_remove.clear()

        # check for gone
        for artifact in self.deployed_artifacts:
            if artifact.is_gone:
                self.world_artifacts.append(artifact.artifact_type)
                artifacts_to_remove.append(artifact)
        self.deployed_artifacts = [a for a in self.deployed_artifacts if a not in artifacts_to_remove]

    def give_artifacts_weapons(self, team: Team, artifact_type: ArtifactType):
        # when team pick up artifact add them to weapon_set
        if artifact_type == ArtifactType.NONE:
            return
        for weapon in WeaponManager().weapons:
            if weapon.artifact == artifact_type:
                team.ammo(weapon.index, weapon.initial_amount, True)

    def on_deploy(self):
        super().on_deploy()
        # drop artifact
        if len(self.world_artifacts) > 0:
            chance = randint(0, 10)
            if chance == 0 or self.triger_artifact:
                self.triger_artifact = False
                artifact_type = choice(self.world_artifacts)
                self.world_artifacts.remove(artifact_type)
                deplyoed_artifact = drop_artifact(self.artifact_classes[artifact_type], artifact_type, None, comment=True)
                self.deployed_artifacts.append(deplyoed_artifact)

    def on_turn_begin(self):
        super().on_turn_begin()

        # refresh artifact weapon count
        for team, artifact_type in self.team_artifact_dict.items():
            self.give_artifacts_weapons(team, artifact_type)
