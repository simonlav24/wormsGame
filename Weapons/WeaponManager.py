
import xml.etree.ElementTree as ET
from enum import Enum
from pydantic import BaseModel
from typing import List, Dict

import pygame
import globals
from Constants import GREY, PLAYER_CONTROL_1
from Common import * 

# todo: rename some of this enums

class WeaponStyle(Enum):
    CHARGABLE = 0
    GUN = 1
    PUTABLE = 2
    CLICKABLE = 3
    UTILITY = 4


class WeaponCategory(Enum):
    MISSILES = 0
    GRENADES = 1
    GUNS = 2
    FIREY = 3
    BOMBS = 4
    TOOLS = 5
    AIRSTRIKE = 6
    LEGENDARY = 7
    UTILITIES = 8
    ARTIFACTS = 9


class ArtifactType(Enum):
    NONE = 0
    MJOLNIR = 1
    PLANT_MASTER = 2
    AVATAR = 3
    MINECRAFT = 4

weapon_bg_color = {
    WeaponCategory.MISSILES : (255, 255, 255),
    WeaponCategory.GRENADES : (204, 255, 204),
    WeaponCategory.GUNS : (255, 204, 153),
    WeaponCategory.FIREY : (255, 204, 204),
    WeaponCategory.BOMBS : (200, 255, 200),
    WeaponCategory.TOOLS : (224, 224, 235),
    WeaponCategory.AIRSTRIKE : (204, 255, 255),
    WeaponCategory.LEGENDARY : (255, 255, 102),
    WeaponCategory.UTILITIES : (254, 254, 254),
    WeaponCategory.ARTIFACTS : (255, 255, 101),
}

class Weapon(BaseModel):
    ''' weapon base model '''
    index: int
    name: str
    style: WeaponStyle
    category: WeaponCategory
    initial_amount: int
    is_fused: bool = False
    round_delay: int = 0
    artifact: ArtifactType = ArtifactType.NONE

    def get_bg_color(self) -> ColorType:
        ''' returns weapons background color '''
        return weapon_bg_color[self.category]



# todo: why is missile amount 1??? 

class WeaponManager:
    ''' weapons manager '''
    _wm = None
    def __init__(self):
        WeaponManager._wm = self
        globals.weapon_manager = self
        self.weapons: List[Weapon] = [] #	  name					style	amount	category	fused	delay
        weapon_index = 0

        self.cool_down_list: List[Weapon] = [] # weapon cool down list
        self.cool_down_list_surfaces: List[pygame.Surface] = []

        # styleDict = {"CHARGABLE": CHARGABLE, "GUN": GUN, "PUTABLE": PUTABLE, "CLICKABLE": CLICKABLE, "UTILITY": UTILITY}
        # categDict = {"MISSILES": MISSILES, "GRENADES": GRENADES, "GUNS": GUNS, "FIREY": FIREY, "BOMBS": BOMBS, "TOOLS": TOOLS,
        #                 "AIRSTRIKE": AIRSTRIKE, "LEGENDARY": LEGENDARY}
        # artifDict = {"MJOLNIR": MJOLNIR, "PLANT_MASTER": PLANT_MASTER, "AVATAR": AVATAR, "MINECRAFT": MINECRAFT}

        groups = ET.parse('weapons.xml').getroot()
        for weapon in groups[0]:
            name = weapon.attrib["name"]
            style = WeaponStyle[weapon.attrib["style"]]
            amount = int(weapon.attrib["amount"])
            category = WeaponCategory[weapon.attrib["category"]]
            fused = True if weapon.attrib["fused"] == "True" else False
            delay = int(weapon.attrib["delay"])
            
            weapon = Weapon(index=weapon_index, name=name, style=style, category=category, initial_amount=amount, is_fused=fused, round_delay=delay)
            weapon_index += 1
            self.weapons.append(weapon)

        for weapon in groups[1]:
            name = weapon.attrib["name"]
            style = WeaponStyle[weapon.attrib["style"]]
            weapon = Weapon(index=weapon_index, name=name, style=style, category=WeaponCategory.UTILITIES, initial_amount=0)
            weapon_index += 1
            self.weapons.append(weapon)

        for weapon in groups[2]:
            name = weapon.attrib["name"]
            style = WeaponStyle[weapon.attrib["style"]]
            artifact = ArtifactType[weapon.attrib["artifact"]]
            weapon = Weapon(index=weapon_index, name=name, style=style, category=WeaponCategory.ARTIFACTS, initial_amount=0, artifact=artifact)
            weapon_index += 1
            self.weapons.append(weapon)

        self.weaponCount = len(groups[0])
        self.utilityCount = len(groups[1])
        self.artifactCount = len(groups[2])

        mapped = map(lambda x: x.name, self.weapons)
        self.weapon_dict: Dict[str, Weapon] = {key: value for key, value in zip(list(mapped), self.weapons)}

        # basic set for teams 
        self.basic_set: List[int] = [weapon.initial_amount for weapon in self.weapons]

        self.currentWeapon: Weapon = self.weapons[0]
        self.surf = globals.pixelFont5.render(self.currentWeapon.name, False, globals.game_manager.HUDColor)
        self.multipleFires = ["flame thrower", "minigun", "laser gun", "bubble gun", "razor leaf"]
        
        # todo: this
        #self.artifactDict = {MJOLNIR: Mjolnir, PLANT_MASTER: MagicLeaf, AVATAR: Avatar, MINECRAFT: PickAxeArtifact}

        # read weapon set if exits and adjust basic set
        if globals.game_manager.game_config.weapon_set is not None:
            # zero out basic set
            self.basic_set = [0 for i in self.basic_set]

            weaponSet = ET.parse('./assets/weaponsSets/' + globals.game_manager.game_config.weapon_set + '.xml').getroot()
            for weapon in weaponSet:
                name = weapon.attrib["name"]
                amount = int(weapon.attrib["amount"])
                self.basic_set[self.weaponDict[name]] = amount

    # def getStyle(self, string):
    #     return self.weapons[self.weaponDict[string]][1]
    # def getCurrentStyle(self):
    #     return self.getStyle(self.currentWeapon)
    # def getCurrentDelay(self):
    #     return self.weapons[self.weaponDict[self.currentWeapon]][5]
    # def getFused(self, string):
    #     return self.weapons[self.weaponDict[string]][4]
    # def getBackColor(self, string):
    #     return self.weapons[self.weaponDict[string]][3]
    # def getCategory(self, string):
    #     if self.weapons[self.weaponDict[string]][1] == UTILITY:
    #         return CATEGORY_UTILITIES
    #     index = self.weaponDict[string]
    #     if index < self.weaponCount:
    #         return CATEGORY_WEAPONS
    #     elif index < self.weaponCount + self.utilityCount:
    #         return CATEGORY_UTILITIES
    #     else:
    #         return CATEGORY_ARTIFACTS

    def add_to_cool_down(self, weapon: Weapon) -> None:
        ''' add weapon to list of cool downs '''
        self.cool_down_list_surfaces.append(globals.pixelFont5halo.render(weapon.name, False, globals.game_manager.HUDColor))
        self.cool_down_list.append(weapon)

        if len(self.cool_down_list) > 4:
            self.cool_down_list_surfaces.pop(0)
            self.cool_down_list.pop(0)

    def get_weapons_list_of_category(self, category: WeaponCategory) -> List[Weapon]:
        return [weapon for weapon in self.weapons if weapon.category == category]

    def get_surface_portion(self, weapon: Weapon) -> Tuple[pygame.Surface, Tuple[int, int, int, int]] | None:
        index = weapon.index
        x = index % 8
        y = 9 + index // 8
        rect = (x * 16, y * 16, 16, 16)
        return (globals.game_manager.sprites, rect)

    def get_weapon(self, name: str) -> Weapon:
        ''' get weapon by name '''
        return self.weapon_dict[name]

    def can_shoot(self) -> bool:
        ''' check if can shoot current weapon '''
        # if no ammo
        if globals.team_manager.currentTeam.ammo(WeaponManager._wm.currentWeapon) == 0:
            return False
        
        # if not active
        if not self.is_current_weapon_active():
            return False

        # if in use list
        if globals.game_manager.game_config.option_cool_down and self.currentWeapon in self.cool_down_list:
            return False
        
        if (not globals.game_manager.playerControl) or (not globals.game_manager.playerMoveable) or (not globals.game_manager.playerShootAble):
            return False
        
        return True

    def switchWeapon(self, weapon: Weapon, force=False):
        """ switch weapon and draw weapon sprite """
        self.currentWeapon = weapon
        self.renderWeaponCount()

        globals.game_manager.weaponHold.fill((0,0,0,0))
        if False and canShoot(force):
            if self.getBackColor(string) in [GRENADES, GUNS, TOOLS, LEGENDARY, FIREY, BOMBS] or string in [""]:
                if string in ["covid 19", "parachute", "earthquake"]:
                    return
                if string == "gemino mine":
                    WeaponManager._wm.blitWeaponSprite(globals.game_manager.weaponHold, (0,0), "mine")
                    return
                WeaponManager._wm.blitWeaponSprite(globals.game_manager.weaponHold, (0,0), string)
                return
            if string in ["flare", "artillery assist"]:
                WeaponManager._wm.blitWeaponSprite(globals.game_manager.weaponHold, (0,0), "flare")
                return
            if self.getBackColor(string) in [MISSILES]:
                globals.game_manager.weaponHold.blit(globals.game_manager.sprites, (0,0), (64,112,16,16))
            if self.getBackColor(string) in [AIRSTRIKE]:
                if string == "chum bucket":
                    globals.game_manager.weaponHold.blit(globals.game_manager.sprites, (0,0), (16,96,16,16))
                    return
                globals.game_manager.weaponHold.blit(globals.game_manager.sprites, (0,0), (64,64,16,16))
    
    def addArtifactMoves(self, artifact):
        # when team pick up artifact add them to weaponCounter
        for w in self.weapons[self.weaponCount + self.utilityCount:]:
            if w[6] == artifact:
                if w[0] in ["magic bean", "pick axe", "build"]:
                    globals.team_manager.currentTeam.ammo(w[0], 1, True)
                    continue
                if w[0] == "fly":
                    globals.team_manager.currentTeam.ammo(w[0], 3, True)
                    continue
                globals.team_manager.currentTeam.ammo(w[0], -1, True)

    def currentArtifact(self):
        if self.currentWeapon.category == WeaponCategory.ARTIFACTS:
            return self.weapons[self.currentIndex()][6]

    def currentIndex(self):
        return self.currentWeapon.index
    
    def is_current_weapon_active(self) -> bool:
        ''' check if current weapon active in this round '''
        return (self.currentWeapon.round_delay <= globals.game_manager.roundCounter and
                not self.currentWeapon in self.cool_down_list)
    
    def renderWeaponCount(self):
        ''' changes surf to fit current weapon '''
        color = globals.game_manager.HUDColor
        # if no ammo in current team
        ammo = globals.team_manager.currentTeam.ammo(WeaponManager._wm.currentWeapon)
        if ammo == 0 or not self.is_current_weapon_active() or (globals.game_manager.game_config.option_cool_down and self.currentWeapon in self.cool_down_list):
            color = GREY
        weaponStr = self.currentWeapon.name

        # special addings
        if self.currentWeapon == "bunker buster":
            weaponStr += " (drill)" if BunkerBuster.mode else " (rocket)"
        
        # add quantity
        if ammo != -1:
            weaponStr += " " + str(ammo)
            
        # add fuse
        if self.currentWeapon.is_fused:
            weaponStr += "  delay: " + str(globals.game_manager.fuseTime // globals.fps)
            
        self.surf = globals.pixelFont5halo.render(weaponStr, False, color)

    def updateDelay(self):
        for w in self.weapons:
            if not w[5] == 0:
                w[5] -= 1

    def handle_event(self, event) -> bool:
        ''' handle pygame events '''
        # weapon change by keyboard
        if globals.game_manager.state == PLAYER_CONTROL_1:
            if not event.type == pygame.KEYDOWN:
                return False
            weaponsSwitch = False
            if event.key == pygame.K_1:
                keyWeapons = [self.weapon_dict[w] for w in ["missile", "gravity missile", "homing missile"]]
                weaponsSwitch = True
            elif event.key == pygame.K_2:
                keyWeapons = [self.weapon_dict[w] for w in ["grenade", "sticky bomb", "electric grenade"]]
                weaponsSwitch = True
            elif event.key == pygame.K_3:
                keyWeapons = [self.weapon_dict[w] for w in ["mortar", "raon launcher"]]
                weaponsSwitch = True
            elif event.key == pygame.K_4:
                keyWeapons = [self.weapon_dict[w] for w in ["petrol bomb", "flame thrower"]]
                weaponsSwitch = True
            elif event.key == pygame.K_5:
                keyWeapons = [self.weapon_dict[w] for w in ["TNT", "mine", "sheep"]]
                weaponsSwitch = True
            elif event.key == pygame.K_6:
                keyWeapons = [self.weapon_dict[w] for w in ["shotgun", "long bow", "gamma gun", "laser gun"]]
                weaponsSwitch = True
            elif event.key == pygame.K_7:
                keyWeapons = [self.weapon_dict[w] for w in ["girder", "baseball"]]
                weaponsSwitch = True
            elif event.key == pygame.K_8:
                keyWeapons = [self.weapon_dict[w] for w in ["bunker buster", "laser gun", "minigun"]]
                weaponsSwitch = True
            elif event.key == pygame.K_9:
                keyWeapons = [self.weapon_dict[w] for w in ["minigun"]]
                weaponsSwitch = True
            elif event.key == pygame.K_0:
                keyWeapons = []
                for i, w in enumerate(TeamManager._tm.currentTeam.weaponCounter):
                    if w > 0 or w == -1:
                        if WeaponManager._wm.weapons[i][3] in [LEGENDARY, ARTIFACTS]:
                            keyWeapons.append(WeaponManager._wm.weapons[i][0])
                weaponsSwitch = True
            elif event.key == pygame.K_MINUS:
                keyWeapons = ["rope"]
                weaponsSwitch = True
            elif event.key == pygame.K_EQUALS:
                keyWeapons = ["parachute"]
                weaponsSwitch = True
            if weaponsSwitch:
                if len(keyWeapons) > 0:
                    if WeaponManager._wm.currentWeapon in keyWeapons:
                        index = keyWeapons.index(WeaponManager._wm.currentWeapon)
                        index = (index + 1) % len(keyWeapons)
                        weaponSwitch = keyWeapons[index]
                    else:
                        weaponSwitch = keyWeapons[0]
                WeaponManager._wm.switchWeapon(weaponSwitch)
                WeaponManager._wm.renderWeaponCount()
        return False

    def draw(self) -> None:
        # draw use list
        win = globals.game_manager.win
        space = 0
        for i, surf in enumerate(self.cool_down_list_surfaces):
            if i == 0:
                win.blit(surf, (30 + 80 * i, globals.winHeight - 5 - surf.get_height()))
            else:
                space += self.cool_down_list_surfaces[i-1].get_width() + 10
                win.blit(surf, (30 + space, globals.winHeight - 5 - surf.get_height()))

    def drawWeaponIndicators(self) -> None:
        ''' draw specific weapon indicator '''
        return
        if WeaponManager._wm.currentWeapon.name in ["homing missile", "seeker"] and HomingMissile.showTarget:
            drawTarget(HomingMissile.Target)
        if WeaponManager._wm.currentWeapon == "girder" and globals.game_manager.state == PLAYER_CONTROL_1:
            globals.game_manager.drawGirderHint()
        if WeaponManager._wm.currentWeapon == "trampoline" and globals.game_manager.state == PLAYER_CONTROL_1:
            globals.game_manager.drawTrampolineHint()
        if WeaponManager._wm.getBackColor(WeaponManager._wm.currentWeapon) == AIRSTRIKE:
            mousePos = pygame.mouse.get_pos()
            mouse = Vector(mousePos[0]/scalingFactor + globals.game_manager.camPos.x, mousePos[1]/scalingFactor + globals.game_manager.camPos.y)
            win.blit(pygame.transform.flip(globals.game_manager.airStrikeSpr, False if globals.game_manager.airStrikeDir == RIGHT else True, False), point2world(mouse - tup2vec(globals.game_manager.airStrikeSpr.get_size())/2))
        if WeaponManager._wm.currentWeapon == "earth spike" and globals.game_manager.state in [PLAYER_CONTROL_1, FIRE_MULTIPLE] and globals.team_manager.currentTeam.ammo("earth spike") != 0:
            spikeTarget = calcEarthSpikePos()
            if spikeTarget:
                drawTarget(spikeTarget)

    def blitWeaponSprite(self, dest, pos, weapon_name: str):
        weapon = self.get_weapon(weapon_name)
        index = weapon.index
        x = index % 8
        y = 9 + index // 8
        rect = (x * 16, y * 16, 16, 16)
        dest.blit(globals.game_manager.sprites, pos, rect)