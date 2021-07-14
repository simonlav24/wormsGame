# Worms Game
![Alt text](wormsShoot.png?raw=true "Worms")
game development practice in python for educational purposes and fun. pygame required.

# how to play
- right/left arrow keys - movement.
- up/down arrow keys - pointing.
- enter - jump in pointing direction.
- space - hold to shoot chargeable (missiles, grenades etc) weapons, press to shoot non chargeable weapons.
- tab - change some weapons mode, changes delay time for grenades.
- p - toggle game pause.
- F2 - toggle health visualization mode.
- mouse left click - press for clickable weapons. (airstrikes, teleport etc).
- mouse right click - open weapons menu.
- mouse scroll - scroll weapons menu.

# Weapons
## Missiles
- **MISSILE** - chargeable, shoot a missile, wind sensitive.
- **GRAVITY MISSILE** - chargeable, shoot a missile. worms hit by gravity missile will change their gravity orientation. wind sensitive.
- **BUNKER BUSTER** - chargeable, shoot a missile that drills through the terrain and explodes when reaches air. press tab to switch from "rocket" mode to "drill" mode
- **HOMING MISSILE** - chargeable, mouse click to select target and shoot.
- **ARTILLERY ASSISTANCE** - chargeable, throw a flare to mark area for bombing.

## Grenades
- **GRENADE** - chargeable, throw a grenade. all grenades delay time can be changed by pressing tab.
- **MORTAR** - chargeable, throw a mortar grenade. release cluster on explosion.
- **STICKY BOMB** - chargeable, a sticky grenade.
- **GAS GRENADE** - chargeable, emit a toxic gas before exploding.
- **ELECTRIC GRENADE** - chargeable, electrifying nearby worms. bouncy.
- **RAON LAUNCHER** - chargeable, shooting two raons - small proximity mines that moving closer to target every turn. will explode if electrocuted.

## Guns
- **SHOTGUN** - fire shotgun. 3 rounds.
- **MINIGUN** - fire minigun.
- **GAMMA GUN** - fire gamma radiation pulse. make worms sick and mutate venus fly traps. can pass through terrain.
- **LONG BOW** - shoot arrows. 3 arrows. press tab for sleeping poison. sleeping worms will lose their next turn.
- **SPEAR** - throw spear, impale all worms in its way. 2 spears.
- **LASER GUN** - destructive laser destroy destructively every thing on its way.
- **PORTAL GUN** - the cake is a deception. obtainable by utility crate.
- **BUBBLE GUN** - shoot bubbles that captures worms and more.

## Fire weapons
- **PETROL BOMB** - chargeable, throw a petrol bomb, explosive fire spreader.
- **FLAME THROWER** - it werfs flammen.

## Place and run

- **MINE** - mine.
- **TNT** - explosive TNT bomb.
- **COVID19** - very contagious. sick worms will cough and spread the virus. obtainable by weapon crate.
- **SHEEP** - baaaa.
- **SNAIL** - chargeable, quick  and sticky snail.

## Misc

- **BASEBALL** - home running worms away.
- **GIRDER** - clickable, place a girder. press tab for rotation and scaling.
- **ROPE** - swing your way to action.
- **PARACHUTE** - glide down safely. wind sensitive.
- **VENUS FLY TRAP** - chargeable, throw seed that grows a venus fly trap - vicious plant that will devour anything. can turn to MUTANT VENUS FLY TRAP if hit by GAMMA GUN radiation. press tab to switch to PLANT BOMB that grows on impact in all directions.
- **SENTRY GUN** - place a sentry gun. fires at nearby worms at the end of the turn. obtainable by weapon crate.
- **ENDER PEARL** - throw and teleport to where it lands.
- **ACID BOTTLE** - throw a bottle of hydrofluoric acid that corrode the earth and is deadly to worms.

## Aerial
- **AIRSTRIKE** - clickable, missile strike, wind sensitive.
- **NAPALM STRIKE** - clickable, smelly, firey mess. wind sensitive.
- **MINE STRIKE** - clickable, mine strike.

## Super weapons
 Legendary weapons can be obtained by weapon crates marked with "W".
- **HOLY GRENADE** - chargeable, feast upon the lambs and sloths and carp and anchovies and orangutans and breakfast cereals, and fruit bats. lobbest thou thy Holy Hand Grenade of Antioch towards thy foe, who, being naughty in My sight, shall snuff it.
- **BANANA** - chargeable, multiplying banana of mass destruction.
- **EARTHQUAKE** - quakes the earth.
- **GEMINO MINE** - chargeable, throw a mine cursed by the gemino curse.
- **BEE HIVE** - chargeable, wake the bees at impact.
- **VORTEX GRENADE** - chargeable, create a tear in the space time continuum.
- **CHILLI PEPPER** - chargeable, red hot chilli pepper.
- **RAGING BULL** - moooo bi%%h get out the way.
- **ELECTRO BOOM** - like the electric grenade but with exploding electrical pulse and wider range. team friendly.
- **POKEBALL** - catch worms. store them until the ball is damaged.
- **GREEN SHELL** - actual Koopa Troopa shell.
- **GUIDED MISSILE** - controllable missile. use RIGHT KEY and LEFT KEY to control.

# Utilities:
 Utilities can be obtained by utility crates marked with "?".
- **moon gravity** - big step for wormanity.
- **double damage** - twice as fun.
- **aim aid** - laser sight for guns.
- **teleport** - activate and click somewhere.
- **switch worms** - activate and press tab to switch worms in team.
- **time travel** - activate and continue with your turn. shoot a 'chargeable' weapon or 'place and run'. 
- **jet pack** - thrust with arrow keys.
- **portal gun** - to use in weapons.
- **traveling kit** - more ropes and parachutes.

## Game modes

- Battle - last team standing wins.
- Points - damage = points. The team with the most points wins.
- Targets - shoot targets to get points. The team with the most points wins.
- Capture the flag - the team that holds the flag at the end of the turn wins a point. The team with the most points wins.
- Terminator - each turn you have a targeted worm. Hitting the target = 1 point. Terminating the target = 2 points.
- David vs Goliath - starter worm receives 50% of all teammate's health.

## Options

- Cooldown - weapons have a cooldown for 4 turns.
- Warped - horizontal map warp. *experimental*
- Random - the worm of the next turn is randomly picked. "Teams" means completely random worm and team. "Worms" means random worm but team cycle regularly.
- Manual placing - place worms manually.
- Darkness - dark game mode. use flares to illuminate areas near you.
- Closed map - cant exit the map bounding box.
- Forts - teammates spawn in cluster.
- Digging - worms are underground. dig your way around. recommended with darkness.

