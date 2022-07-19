# Worms Game
![Alt text](wormsShoot.png?raw=true "Worms")
game development practice in python for educational purposes and fun.

**requirements**: Python3, Pygame, PySimpleGui

# :question: ​how to play
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

# :crossed_swords: Weapons
## :rocket: Missiles

![](/assets/anims/missile.gif)

- **MISSILE** - shoot a missile, wind sensitive.
- **GRAVITY MISSILE** - shoot a missile. worms hit by gravity missile will change their gravity orientation. wind sensitive.
- **BUNKER BUSTER** - shoot a missile that drills through the terrain and explodes when reaches air. press tab to switch from "rocket" mode to "drill" mode
- **HOMING MISSILE** - mouse click to select target and shoot. 
- **SEEKER** - target seeking missile.

## :comet: Grenades

![](/assets/anims/grenade.gif)

- **GRENADE** - throw a grenade. all grenades delay time can be changed by pressing tab.
- **MORTAR** - throw a mortar grenade. release cluster on explosion.
- **STICKY BOMB** - a sticky grenade.
- **GAS GRENADE** - emit a toxic gas before exploding.
- **ELECTRIC GRENADE** - electrifying grenade
- **RAON LAUNCHER** - shoot two raons - small proximity mines that moving closer to target every turn. will explode if electrocuted.

## :gun: Guns

![](/assets/anims/minigun.gif)

- **SHOTGUN** - fire shotgun. 3 rounds.
- **LONG BOW** - shoot arrows. 3 arrows. press tab for sleeping poison. sleeping worms will lose their next turn.
- **MINIGUN** - fire minigun.
- **GAMMA GUN** - fire gamma radiation pulse. make worms sick and mutate venus fly traps. can pass through terrain.
- **SPEAR** - throw spear, impale all worms in its way. 2 spears.
- **LASER GUN** - destructive laser destroy destructively every thing on its way.
- **BUBBLE GUN** - shoot bubbles that captures worms and more

## :fire: Incendiary

![](/assets/anims/fire.gif)

- **PETROL BOMB** - explosive fire spreader.
- **FLAME THROWER** - it werfs flammen

## :bomb: Bombs and Animals

![](/assets/anims/snail.gif)

- **TNT** - explosive TNT bomb.
- **MINE** - mine.
- **ACID BOTTLE** - throw a bottle of hydrofluoric acid that corrode the earth and is deadly to worms.
- **SHEEP** - baaaa.
- **SNAIL** - quick and sticky snail.
- **VENUS FLY TRAP** - throw seed that grows a venus fly trap - vicious plant that will devour anything. can turn to MUTANT VENUS FLY TRAP if hit by GAMMA GUN radiation. press tab to switch to PLANT BOMB that grows on impact in all directions.
- **COVID19** - very contagious. sick worms will cough and spread the virus.

## :wrench: Tools

![](/assets/anims/tools.gif)

- **BASEBALL** - home running worms away.
- **GIRDER** - place a girder. press tab for rotation and scaling.
- **ROPE** - swing your way to action.
- **PARACHUTE** - glide down safely. wind sensitive.
- **SENTRY GUN** - place a sentry gun. fires at nearby worms at the end of the turn.
- **PORTAL GUN** - the cake is a deception.
- **ENDER PEARL** - throw and teleport to where it lands.
- **TRAMPOLINE** - place a trampoline. any object will bounce off.

## :small_airplane: Aerial

![](/assets/anims/airstrike.gif)

- **ARTILLERY ASSISTANCE** - throw a flare to mark area for bombing.
- **CHUM BUCKET** - throw chum. attracts seagulls. *experimental*
- **AIRSTRIKE** - missile strike, wind sensitive.
- **NAPALM STRIKE** - smelly, firey mess. wind sensitive.
- **MINE STRIKE** - mine strike.

## :hot_pepper: Super weapons

![](/assets/anims/electro.gif)

 Legendary weapons can be obtained by weapon crates.
- **HOLY GRENADE** - feast upon the lambs and sloths and carp and anchovies and orangutans and breakfast cereals, and fruit bats. lobbest thou thy Holy Hand Grenade of Antioch towards thy foe, who, being naughty in My sight, shall snuff it.
- **BANANA** - multiplying banana of mass destruction.
- **EARTHQUAKE** - quakes the earth.
- **GEMINO MINE** - throw a mine cursed by the gemino curse.
- **BEE HIVE** - wake the bees at impact.
- **VORTEX GRENADE** - create a tear in the space time continuum.
- **CHILLI PEPPER** - red hot chilli pepper.
- **RAGING BULL** - moooo bi%%h get out the way.
- **ELECTRO BOOM** - like the electric grenade but with exploding electrical pulse and wider range. team friendly.
- **POKEBALL** - catch worms. store them until the ball is damaged.
- **GREEN SHELL** - actual Koopa Troopa shell.
- **GUIDED MISSILE** - controllable missile. use RIGHT KEY and LEFT KEY to control.
- **FIREWORKS** - tie 3 worms or any object to firework rocket and light the sky.

# :hammer: Utilities:

![](/assets/anims/jetpack.gif)

 Utilities can be obtained by utility crates.
- **moon gravity** - big step for wormanity.
- **double damage** - twice as fun.
- **aim aid** - laser sight for guns.
- **teleport** - activate and click somewhere.
- **switch worms** - activate and press tab to switch worms in team.
- **time travel** - activate and continue with your turn. shoot a 'chargeable' weapon or 'place and run'. 
- **jet pack** - thrust with arrow keys.
- **tool set** - receive some useful tools to use in weapons.
- **traveling kit** - more ropes and parachutes.

## :moyai: Artifacts

![](/assets/anims/mjolnir.gif)

Artifacts is a game option that unlocks magical items and weapons. the artifacts will randomly spawn in the map and must be collected to activate their abilities.

* **Mjolnir** - Thor's magical hammar
  * **strike** - strike the hammer with a powerful electric blast
  * **throw** - throw the hammer with a powerful electric blast
  * **fly** - use the hammer to fly. with a powerful electric blast
* **Plant Master** - become master of plants. grants immunity to plant attacks and the ability to control plants.
  * **Control Plants** - activate and use arrow keys to move or rotate plants
  * **Magic Bean** - throw bean that grows a giant beanstalk
  * **Mine Plant** - plant that grows proximity mine flowers
  * **Razor Leaf** - A Grass-type attack that sends sharp-edged leaves at the target. Likely to get a critical hit.
* **Avatar** - become master of all four elements.
  * **Icicle** - shoot freezing icicle
  * **Earth Spike** - bend the earth into a spike to shoot nearby emenies and objects to space
  * **Fire Ball** - a flying blast of fire ball exploding into flames
  * **Air Tornado** - send a violently rotating column of air
* **Minecraft** - become a minecraft builder
  * **Pick Axe** - use a diamond pickaxe to mine the ground
  * **Build** - ability to place dirt blocks around you

## :hammer_and_pick: Game modes

- **Battle** - last team standing wins.
- **Points** - damage = points. The team with the most points wins.
- **Targets** - shoot targets to get points. The team with the most points wins.
- **Capture the flag** - the team that holds the flag at the end of the turn wins a point. The team with the most points wins.
- **Terminator** - each turn you have a targeted worm. Hitting the target = 1 point. Terminating the target = 2 points.
- **David vs Goliath** - starter worm receives 50% of all teammate's health.
- **Arena** - worms get points for standing on top of the arena at the end of each turn. The team with the most points wins.
- **Missions** - each worm is assinged three renewable missions. upon completing a mission the worm receives points. The team with the most points wins.

## :gear: Options

- **Cooldown** - weapons have a cooldown for 4 turns.
- **Warped** - horizontal map warp. *experimental*
- **Random** - the worm of the next turn is randomly picked. "Complete" means completely random worm and team. "In Team" means random worm but team cycle regularly.
- **Manual placing** - place worms manually.
- **Darkness** - dark game mode. use flares to illuminate areas near you.
- **Closed map** - cant exit the map bounding box.
- **Forts** - teammates spawn in cluster.
- **Digging** - worms are underground. dig your way around. recommended with darkness.
- **Artifacts** - enable artifacts in the games.

### :ocean: Sudden Death

Sudden death activates after several number of rounds, defined in the options. the sudden death types are: plague - worms loose half their health and get sick, water rise - water level rising after each turn. the types can both be used.
