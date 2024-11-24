
from typing import Dict, List
from game.sfx import SfxIndex

# sfx
sfx_none = [SfxIndex.NONE]
sfx_throw = [SfxIndex.THROW1, SfxIndex.THROW2, SfxIndex.THROW3]
sfx_missile = [SfxIndex.FIRE_MISSILE]
sfx_gun = [SfxIndex.GUN_SHOT1, SfxIndex.GUN_SHOT2, SfxIndex.GUN_SHOT3]
airstrike = [SfxIndex.AIRSTRIKE]

weapon_creation_sfx: Dict[str, List[SfxIndex]] = {}

weapon_creation_sfx['missile'] = sfx_missile
weapon_creation_sfx['gravity missile'] = sfx_missile
weapon_creation_sfx['drill missile'] = sfx_missile
weapon_creation_sfx['homing missile'] = sfx_missile
weapon_creation_sfx['seeker'] = sfx_missile
weapon_creation_sfx['grenade'] = sfx_throw
weapon_creation_sfx['cluster grenade'] = sfx_throw
weapon_creation_sfx['sticky bomb'] = sfx_throw
weapon_creation_sfx['gas grenade'] = sfx_throw
weapon_creation_sfx['electric grenade'] = sfx_throw
weapon_creation_sfx['raon launcher'] = sfx_throw
weapon_creation_sfx['shotgun'] = sfx_gun
weapon_creation_sfx['long bow'] = [SfxIndex.BOW]
weapon_creation_sfx['minigun'] = sfx_gun
weapon_creation_sfx['gamma gun'] = [SfxIndex.GAMMA_RAY]
weapon_creation_sfx['spear'] = sfx_throw
weapon_creation_sfx['laser gun'] = [SfxIndex.LASER_LOOP]
weapon_creation_sfx['bubble gun'] = [SfxIndex.BUBBLE_BLOW]
weapon_creation_sfx['petrol bomb'] = sfx_throw
weapon_creation_sfx['flame thrower'] = sfx_none
weapon_creation_sfx['TNT'] = sfx_throw
weapon_creation_sfx['mine'] = sfx_throw
weapon_creation_sfx['acid bottle'] = sfx_throw
weapon_creation_sfx['sheep'] = [SfxIndex.SHEEP_BAA1, SfxIndex.SHEEP_BAA2]
weapon_creation_sfx['snail'] = sfx_throw
weapon_creation_sfx['venus fly trap'] = sfx_throw
weapon_creation_sfx['covid 19'] = sfx_none
weapon_creation_sfx['baseball'] = sfx_none
weapon_creation_sfx['girder'] = [SfxIndex.GIRDER]
weapon_creation_sfx['rope'] = [SfxIndex.ROPE]
weapon_creation_sfx['parachute'] = sfx_none
weapon_creation_sfx['sentry turret'] = sfx_throw
weapon_creation_sfx['portal gun'] = [SfxIndex.PORTAL]
weapon_creation_sfx['ender pearl'] = sfx_throw
weapon_creation_sfx['trampoline'] = sfx_none
weapon_creation_sfx['airstrike'] = airstrike
weapon_creation_sfx['napalm strike'] = airstrike
weapon_creation_sfx['mine strike'] = airstrike
weapon_creation_sfx['artillery assist'] = sfx_none
weapon_creation_sfx['chum bucket'] = sfx_throw
weapon_creation_sfx['holy grenade'] = sfx_throw
weapon_creation_sfx['banana'] = sfx_throw
weapon_creation_sfx['earthquake'] = sfx_none
weapon_creation_sfx['gemino mine'] = sfx_throw
weapon_creation_sfx['bee hive'] = sfx_throw
weapon_creation_sfx['vortex grenade'] = sfx_throw
weapon_creation_sfx['chilli pepper'] = sfx_throw
weapon_creation_sfx['raging bull'] = [SfxIndex.BULL]
weapon_creation_sfx['electro boom'] = sfx_throw
weapon_creation_sfx['pokeball'] = sfx_throw
weapon_creation_sfx['green shell'] = sfx_throw
weapon_creation_sfx['guided missile'] = sfx_missile
weapon_creation_sfx['fireworks'] = sfx_none
weapon_creation_sfx['moon gravity'] = sfx_none
weapon_creation_sfx['double damage'] = sfx_none
weapon_creation_sfx['aim aid'] = sfx_none
weapon_creation_sfx['teleport'] = sfx_none
weapon_creation_sfx['switch worms'] = sfx_none
weapon_creation_sfx['time travel'] = sfx_none
weapon_creation_sfx['jet pack'] = sfx_none
weapon_creation_sfx['flare'] = sfx_none
weapon_creation_sfx['mjolnir strike'] = sfx_none
weapon_creation_sfx['mjolnir throw'] = sfx_throw
weapon_creation_sfx['fly'] = sfx_throw
weapon_creation_sfx['control plants'] = sfx_none
weapon_creation_sfx['magic bean'] = sfx_throw
weapon_creation_sfx['mine plant'] = sfx_throw
weapon_creation_sfx['razor leaf'] = sfx_none
weapon_creation_sfx['icicle'] = [SfxIndex.ICICLE]
weapon_creation_sfx['earth spike'] = [SfxIndex.EARTH_SPIKE]
weapon_creation_sfx['fire ball'] = [SfxIndex.FIREBALL]
weapon_creation_sfx['air tornado'] = sfx_none
weapon_creation_sfx['pick axe'] = [SfxIndex.PICKAXE]
weapon_creation_sfx['build'] = [SfxIndex.BUILD]