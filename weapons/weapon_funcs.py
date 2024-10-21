
from typing import Callable, Any, Dict, Type
from random import randint, uniform, choice

from common import GameVariables, EntityPhysical
from common.vector import Vector

from game.map_manager import MapManager
from game.world_effects import Earthquake, Tornado
from entities.worm_tools import Rope, Parachute, JetPack
from weapons.missiles import Missile, GravityMissile, DrillMissile, HomingMissile, Seeker
from weapons.grenades import Grenade, StickyBomb, GasGrenade, HolyGrenade, Banana
from weapons.cluster_grenade import ClusterGrenade
from weapons.electric import ElectricGrenade, ElectroBoom
from weapons.raon import Raon
from weapons.guns import fire_shotgun, fire_minigun, fire_long_bow, fire_bubble_gun, fire_spear, fire_laser, fire_gamma_gun, fire_flame_thrower, fire_icicle, fire_earth_spike, fire_fire_ball, fire_razor_leaf
from weapons.fire_weapons import PetrolBomb, ChilliPepper
from weapons.bombs import TNT, Sheep, Bull
from weapons.mine import Mine, Gemino
from weapons.portal import fire_portal_gun
from weapons.acid import AcidBottle
from weapons.snail import SnailShell
from weapons.plants import PlantSeed, PlantMode
from weapons.covid import Covid19
from weapons.sentry_gun import SentryGun
from weapons.ender_pearl import EndPearl
from weapons.tools import Trampoline, Flare, Baseball, WormSwitcher
from weapons.aerial import fire_airstrike, fire_minestrike, fire_napalmstrike, Chum
from weapons.artillery import Artillery
from weapons.bee_hive import BeeHive
from weapons.vortex import VortexGrenade
from weapons.pokeball import PokeBall
from weapons.green_shell import GreenShell
from weapons.guided_missile import GuidedMissile
from weapons.fireworks import fire_firework
from weapons.artifacts.mjolnir_artifact import MjolnirStrike, MjolnirFly, MjolnirThrow
from weapons.artifacts.plant_master import PlantControl
from weapons.artifacts.minecraft_artifact import build, mine
from weapons.time_travel import TimeTravel
from weapons.paintball import fire_paint_ball

weapon_funcs: Dict[str, Callable[[Any], Any]] = {}

def get_pos_dir_energy(**kwargs):
    return (
        kwargs.get('pos'),
        kwargs.get('direction'),
        kwargs.get('energy'),
    )

def create_with_pos_dir_energy(cls: Type[EntityPhysical], **kwargs) -> EntityPhysical:
    return cls(*get_pos_dir_energy(**kwargs))

def fire_missile(*args, **kwargs) -> EntityPhysical:
    """ fire missile """
    return create_with_pos_dir_energy(Missile, **kwargs)



def fire_gravity_missile(*args, **kwargs) -> EntityPhysical:
    """ fire gravity missile """
    return create_with_pos_dir_energy(GravityMissile, **kwargs)



def fire_drill_missile(*args, **kwargs) -> EntityPhysical:
    """ fire drill missile """
    return create_with_pos_dir_energy(DrillMissile, **kwargs)



def fire_homing_missile(*args, **kwargs) -> EntityPhysical:
    """ fire homing missile """
    return create_with_pos_dir_energy(HomingMissile, **kwargs)



def fire_seeker(*args, **kwargs) -> EntityPhysical:
    """ fire seeker """
    return create_with_pos_dir_energy(Seeker, **kwargs)



def fire_grenade(*args, **kwargs) -> EntityPhysical:
    """ fire grenade """
    return create_with_pos_dir_energy(Grenade, **kwargs)



def fire_cluster_grenade(*args, **kwargs) -> EntityPhysical:
    """ fire cluster grenade """
    return create_with_pos_dir_energy(ClusterGrenade, **kwargs)



def fire_sticky_bomb(*args, **kwargs) -> EntityPhysical:
    """ fire sticky bomb """
    return create_with_pos_dir_energy(StickyBomb, **kwargs)



def fire_gas_grenade(*args, **kwargs) -> EntityPhysical:
    """ fire gas grenade """
    return create_with_pos_dir_energy(GasGrenade, **kwargs)



def fire_electric_grenade(*args, **kwargs) -> EntityPhysical:
    """ fire electric grenade """
    return create_with_pos_dir_energy(ElectricGrenade, **kwargs)



def fire_raon_launcher(*args, **kwargs) -> EntityPhysical:
    """ fire raon launcher """
    pos, direction, energy = get_pos_dir_energy(**kwargs)
    obj = Raon(pos, direction, energy * 0.95)
    obj = Raon(pos, direction, energy * 1.05)
    if randint(0, 10) == 0 or GameVariables().mega_weapon_trigger:
        obj = Raon(pos, direction, energy * 1.08)
        obj = Raon(pos, direction, energy * 0.92)
    return obj



def fire_shotgun(*args, **kwargs) -> EntityPhysical:
    """ fire shotgun """
    return fire_shotgun(**kwargs)



def fire_long_bow(*args, **kwargs) -> EntityPhysical:
    """ fire long bow """
    return fire_long_bow(**kwargs)



def fire_minigun(*args, **kwargs) -> EntityPhysical:
    """ fire minigun """
    return fire_minigun(**kwargs)



def fire_gamma_gun(*args, **kwargs) -> EntityPhysical:
    """ fire gamma gun """
    return fire_gamma_gun(**kwargs)



def fire_spear(*args, **kwargs) -> EntityPhysical:
    """ fire spear """
    return fire_spear(**kwargs)



def fire_laser_gun(*args, **kwargs) -> EntityPhysical:
    """ fire laser gun """
    return fire_laser(**kwargs)



def fire_bubble_gun(*args, **kwargs) -> EntityPhysical:
    """ fire bubble gun """
    return fire_bubble_gun(**kwargs)



def fire_petrol_bomb(*args, **kwargs) -> EntityPhysical:
    """ fire petrol bomb """
    return create_with_pos_dir_energy(PetrolBomb, **kwargs)



def fire_flame_thrower(*args, **kwargs) -> EntityPhysical:
    """ fire flame thrower """
    return fire_flame_thrower(**kwargs)



def fire_TNT(*args, **kwargs) -> EntityPhysical:
    """ fire TNT """
    obj = TNT(kwargs.get('pos'))
    obj.vel = Vector(GameVariables().player.facing * 0.5, -0.8)
    return obj



def fire_mine(*args, **kwargs) -> EntityPhysical:
    """ fire mine """
    obj = Mine(kwargs.get('pos'), GameVariables().fps * 2.5)
    obj.vel.x = GameVariables().player.facing * 0.5
    return obj


def fire_acid_bottle(*args, **kwargs) -> EntityPhysical:
    """ fire acid bottle """
    return create_with_pos_dir_energy(AcidBottle, **kwargs)



def fire_sheep(*args, **kwargs) -> EntityPhysical:
    """ fire sheep """
    obj = Sheep(kwargs.get('pos') + Vector(0, -5))
    obj.facing = GameVariables().player.facing
    return obj



def fire_snail(*args, **kwargs) -> EntityPhysical:
    """ fire snail """
    pos, direction, energy = get_pos_dir_energy(**kwargs)
    obj = SnailShell(pos, direction, energy, GameVariables().player.facing)
    return obj



def fire_venus_fly_trap(*args, **kwargs) -> EntityPhysical:
    """ fire venus fly trap """
    pos, direction, energy = get_pos_dir_energy(**kwargs)
    obj = PlantSeed(pos, direction, energy, PlantMode.VENUS)
    return obj



def fire_covid_19(*args, **kwargs) -> EntityPhysical:
    """ fire covid 19 """
    obj = Covid19(kwargs.get('pos'), GameVariables().player.get_team_data().team_name)
    return obj



def fire_baseball(*args, **kwargs) -> EntityPhysical:
    """ fire baseball """
    Baseball()



def fire_girder(*args, **kwargs) -> EntityPhysical:
    """ fire girder """
    return MapManager().girder(kwargs.get('pos'))



def fire_rope(*args, **kwargs) -> bool:
    """ fire rope """
    direction: Vector = kwargs.get('direction')
    angle = direction.getAngle()
    
    if GameVariables().player.get_tool() is not None:
        GameVariables().player.get_tool().release()
        return False
    elif angle <= 0:
        GameVariables().player.set_tool(Rope(GameVariables().player, kwargs.get('pos'), direction))
        return GameVariables().player.get_tool() is not None



def fire_parachute(*args, **kwargs) -> bool:
    """ fire parachute """
    if GameVariables().player.vel.y > 1:
        GameVariables().player.set_tool(Parachute(GameVariables().player))
    return GameVariables().player.get_tool() is not None


def fire_sentry_turret(*args, **kwargs) -> EntityPhysical:
    """ fire sentry turret """
    obj = SentryGun(kwargs.get('pos'), GameVariables().player.get_team_data().color, GameVariables().player.get_team_data().team_name)
    obj.pos.y -= GameVariables().player.radius + obj.radius



def fire_ender_pearl(*args, **kwargs) -> EntityPhysical:
    """ fire ender pearl """
    return create_with_pos_dir_energy(EndPearl, **kwargs)



def fire_trampoline(*args, **kwargs) -> EntityPhysical:
    """ fire trampoline """
    success = False
    position = GameVariables().player.pos + GameVariables().player.get_shooting_direction() * 20
    anchored = False
    for i in range(25):
        if MapManager().is_ground_at((position + Vector(0, i)).integer()):
            anchored = True
            break
    if anchored:
        Trampoline(position)
        success = True
    return success



def fire_artillery_assist(*args, **kwargs) -> EntityPhysical:
    """ fire artillery assist """
    return create_with_pos_dir_energy(Artillery, **kwargs)



def fire_chum_bucket(*args, **kwargs) -> EntityPhysical:
    """ fire chum bucket """
    pos, direction, energy = get_pos_dir_energy(**kwargs)
    Chum(pos, direction * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 1)
    Chum(pos, direction * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 2)
    Chum(pos, direction * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 3)
    Chum(pos, direction * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 1)
    obj = Chum(pos, direction, energy)
    return obj



def fire_holy_grenade(*args, **kwargs) -> EntityPhysical:
    """ fire holy grenade """
    return create_with_pos_dir_energy(HolyGrenade, **kwargs)



def fire_banana(*args, **kwargs) -> EntityPhysical:
    """ fire banana """
    return create_with_pos_dir_energy(Banana, **kwargs)



def fire_earthquake(*args, **kwargs) -> EntityPhysical:
    """ fire earthquake """
    Earthquake()



def fire_gemino_mine(*args, **kwargs) -> EntityPhysical:
    """ fire gemino mine """
    return create_with_pos_dir_energy(Gemino, **kwargs)



def fire_bee_hive(*args, **kwargs) -> EntityPhysical:
    """ fire bee hive """
    return create_with_pos_dir_energy(BeeHive, **kwargs)



def fire_vortex_grenade(*args, **kwargs) -> EntityPhysical:
    """ fire vortex grenade """
    return create_with_pos_dir_energy(VortexGrenade, **kwargs)



def fire_chilli_pepper(*args, **kwargs) -> EntityPhysical:
    """ fire chilli pepper """
    return create_with_pos_dir_energy(ChilliPepper, **kwargs)



def fire_raging_bull(*args, **kwargs) -> EntityPhysical:
    """ fire raging bull """
    obj = Bull(kwargs.get('pos') + Vector(0, -5))
    obj.facing = GameVariables().player.facing
    obj.ignore.append(GameVariables().player)
    return obj



def fire_electro_boom(*args, **kwargs) -> EntityPhysical:
    """ fire electro boom """
    args = get_pos_dir_energy(**kwargs)
    return ElectroBoom(*args, GameVariables().player.get_team_data().team_name)



def fire_pokeball(*args, **kwargs) -> EntityPhysical:
    """ fire pokeball """
    return create_with_pos_dir_energy(PokeBall, **kwargs)



def fire_green_shell(*args, **kwargs) -> EntityPhysical:
    """ fire green shell """
    obj = GreenShell(kwargs.get('pos') + Vector(0, -5))
    obj.facing = GameVariables().player.facing
    obj.ignore.append(GameVariables().player)
    return obj



def fire_guided_missile(*args, **kwargs) -> EntityPhysical:
    """ fire guided missile """
    return GuidedMissile(kwargs.get('pos') + Vector(0, -5))



def fire_moon_gravity(*args, **kwargs) -> EntityPhysical:
    """ fire moon gravity """
    GameVariables().physics.global_gravity = 0.1
    GameVariables().commentator.comment([{'text': "small step for wormanity"}])



def fire_double_damage(*args, **kwargs) -> EntityPhysical:
    """ fire double damage """
    GameVariables().damage_mult *= 2
    GameVariables().boom_radius_mult *= 1.5
    comments = ["that's will hurt", "that'll leave a mark"]
    GameVariables().commentator.comment([{'text': choice(comments)}])



def fire_aim_aid(*args, **kwargs) -> EntityPhysical:
    """ fire aim aid """
    GameVariables().aim_aid = True
    GameVariables().commentator.comment([{'text': "snipe em'"}])



def fire_teleport(*args, **kwargs) -> EntityPhysical:
    """ fire teleport """
    GameVariables().player.pos = kwargs['pos']



def fire_switch_worms(*args, **kwargs) -> EntityPhysical:
    """ fire switch worms """
    WormSwitcher()
    GameVariables().commentator.comment([{'text': "the ol' switcheroo"}])



def fire_time_travel(*args, **kwargs) -> EntityPhysical:
    """ fire time travel """
    TimeTravel()
    GameVariables().commentator.comment([{'text': "great scott"}])



def fire_jet_pack(*args, **kwargs) -> bool:
    """ fire jet pack """
    GameVariables().player.set_tool(JetPack(GameVariables().player))
    return GameVariables().player.get_tool() is not None



def fire_flare(*args, **kwargs) -> EntityPhysical:
    """ fire flare """
    return create_with_pos_dir_energy(Flare, **kwargs)



def fire_mjolnir_strike(*args, **kwargs) -> EntityPhysical:
    """ fire mjolnir strike """
    MjolnirStrike()



def fire_mjolnir_throw(*args, **kwargs) -> EntityPhysical:
    """ fire mjolnir throw """
    return create_with_pos_dir_energy(MjolnirThrow, **kwargs)



def fire_fly(*args, **kwargs) -> EntityPhysical:
    """ fire fly """
    if not MjolnirFly.flying:
        obj = MjolnirFly(*get_pos_dir_energy(**kwargs))
        return obj



def fire_control_plants(*args, **kwargs) -> EntityPhysical:
    """ fire control plants """
    PlantControl()



def fire_magic_bean(*args, **kwargs) -> EntityPhysical:
    """ fire magic bean """
    pos, direction, energy = get_pos_dir_energy(**kwargs)
    obj = PlantSeed(pos, direction, energy, PlantMode.BEAN)
    return obj



def fire_mine_plant(*args, **kwargs) -> EntityPhysical:
    """ fire mine plant """
    pos, direction, energy = get_pos_dir_energy(**kwargs)
    obj = PlantSeed(pos, direction, energy, PlantMode.MINE)
    return obj



def fire_razor_leaf(*args, **kwargs) -> EntityPhysical:
    """ fire razor leaf """
    return fire_razor_leaf(**kwargs)



def fire_icicle(*args, **kwargs) -> EntityPhysical:
    """ fire icicle """
    return fire_icicle(**kwargs)



def fire_earth_spike(*args, **kwargs) -> EntityPhysical:
    """ fire earth spike """
    return fire_earth_spike(**kwargs)



def fire_fire_ball(*args, **kwargs) -> EntityPhysical:
    """ fire fire ball """
    return fire_fire_ball(**kwargs)



def fire_air_tornado(*args, **kwargs) -> EntityPhysical:
    """ fire air tornado """
    obj = Tornado(GameVariables().player.pos, GameVariables().player.facing)
    return obj



def fire_pick_axe(*args, **kwargs) -> EntityPhysical:
    """ fire pick axe """
    return mine(**kwargs)



def fire_build(*args, **kwargs) -> EntityPhysical:
    """ fire build """
    return build(**kwargs)




weapon_funcs['missile'] = fire_missile
weapon_funcs['gravity missile'] = fire_gravity_missile
weapon_funcs['drill missile'] = fire_drill_missile
weapon_funcs['homing missile'] = fire_homing_missile
weapon_funcs['seeker'] = fire_seeker
weapon_funcs['grenade'] = fire_grenade
weapon_funcs['cluster grenade'] = fire_cluster_grenade
weapon_funcs['sticky bomb'] = fire_sticky_bomb
weapon_funcs['gas grenade'] = fire_gas_grenade
weapon_funcs['electric grenade'] = fire_electric_grenade
weapon_funcs['raon launcher'] = fire_raon_launcher
weapon_funcs['shotgun'] = fire_shotgun
weapon_funcs['long bow'] = fire_long_bow
weapon_funcs['minigun'] = fire_minigun
weapon_funcs['gamma gun'] = fire_gamma_gun
weapon_funcs['spear'] = fire_spear
weapon_funcs['laser gun'] = fire_laser_gun
weapon_funcs['bubble gun'] = fire_bubble_gun
weapon_funcs['petrol bomb'] = fire_petrol_bomb
weapon_funcs['flame thrower'] = fire_flame_thrower
weapon_funcs['TNT'] = fire_TNT
weapon_funcs['mine'] = fire_mine
weapon_funcs['acid bottle'] = fire_acid_bottle
weapon_funcs['sheep'] = fire_sheep
weapon_funcs['snail'] = fire_snail
weapon_funcs['venus fly trap'] = fire_venus_fly_trap
weapon_funcs['covid 19'] = fire_covid_19
weapon_funcs['baseball'] = fire_baseball
weapon_funcs['girder'] = fire_girder
weapon_funcs['rope'] = fire_rope
weapon_funcs['parachute'] = fire_parachute
weapon_funcs['sentry turret'] = fire_sentry_turret
weapon_funcs['portal gun'] = fire_portal_gun
weapon_funcs['ender pearl'] = fire_ender_pearl
weapon_funcs['trampoline'] = fire_trampoline
weapon_funcs['airstrike'] = fire_airstrike
weapon_funcs['napalm strike'] = fire_napalmstrike
weapon_funcs['mine strike'] = fire_minestrike
weapon_funcs['artillery assist'] = fire_artillery_assist
weapon_funcs['chum bucket'] = fire_chum_bucket
weapon_funcs['holy grenade'] = fire_holy_grenade
weapon_funcs['banana'] = fire_banana
weapon_funcs['earthquake'] = fire_earthquake
weapon_funcs['gemino mine'] = fire_gemino_mine
weapon_funcs['bee hive'] = fire_bee_hive
weapon_funcs['vortex grenade'] = fire_vortex_grenade
weapon_funcs['chilli pepper'] = fire_chilli_pepper
weapon_funcs['raging bull'] = fire_raging_bull
weapon_funcs['electro boom'] = fire_electro_boom
weapon_funcs['pokeball'] = fire_pokeball
weapon_funcs['green shell'] = fire_green_shell
weapon_funcs['guided missile'] = fire_guided_missile
weapon_funcs['fireworks'] = fire_firework
weapon_funcs['moon gravity'] = fire_moon_gravity
weapon_funcs['double damage'] = fire_double_damage
weapon_funcs['aim aid'] = fire_aim_aid
weapon_funcs['teleport'] = fire_teleport
weapon_funcs['switch worms'] = fire_switch_worms
weapon_funcs['time travel'] = fire_time_travel
weapon_funcs['jet pack'] = fire_jet_pack
weapon_funcs['flare'] = fire_flare
weapon_funcs['mjolnir strike'] = fire_mjolnir_strike
weapon_funcs['mjolnir throw'] = fire_mjolnir_throw
weapon_funcs['fly'] = fire_fly
weapon_funcs['control plants'] = fire_control_plants
weapon_funcs['magic bean'] = fire_magic_bean
weapon_funcs['mine plant'] = fire_mine_plant
weapon_funcs['razor leaf'] = fire_razor_leaf
weapon_funcs['icicle'] = fire_icicle
weapon_funcs['earth spike'] = fire_earth_spike
weapon_funcs['fire ball'] = fire_fire_ball
weapon_funcs['air tornado'] = fire_air_tornado
weapon_funcs['pick axe'] = fire_pick_axe
weapon_funcs['build'] = fire_build
weapon_funcs['paintball'] = fire_paint_ball