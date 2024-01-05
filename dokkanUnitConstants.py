import numpy as np
import os

#################################################### CONSTANTS ##############################################################################

# IO

CWD = os.getcwd()

# Phases of a Turn
PHASES = ["Start of Turn", "Active / Finish Attacks", "Collect Ki", "Receive Attacks", "Attack Enemy"]

# High-level Unit constants
EXCLUSIVITIES = ["DF", "DFLR", "LR", "CLR", "BU", "F2P", "F2PLR", "Super Strike"]
# elements correspond to EXCLUSIVITIES
RARITIES = ["TUR", "LR", "LR", "LR", "TUR", "TUR", "LR", "TUR"]
UNIQUE_RARITIES = ["TUR", "LR"]
CLASSES = ["S", "E"]
TYPES = ["AGL", "INT", "PHY", "STR", "TEQ"]
HIPO_DUPES = ["55%", "69%", "79%", "90%", "100%"]

# Misc
YES_NO = ["Y", "N"]
LARGE_INT = 1000000

# SBR
ATT_DEBUFF_PASSIVE_CONVERSION_GRADIENT = 10  # 10% attack down for 2 turns = SBR score of +1
DEBUFF_DURATIONS = [0, 1, 2]  # [turns]
SEAL_SCORE_PER_TURN = [0, 0.25, 0.75]  # [SBR metric/chance to seal]
STUN_SCORE_PER_TURN = [0, 0.5, 1.5]  # [SBR metric/chance to stun]
ATT_DEBUFF_SCORE_PER_TURN = [0, 1 / 3, 1]  # [SBR metirc/attack debuff score]
ATT_DEBUFF_ON_ATT_NAMES = ["Lowers", "Greatly Lowers"]
ATT_DEBUFF_ON_ATT_SCORE = [
    0.25,
    0.5,
]  # [attack debuff scrore for lower and greatly lower]
MULTIPLE_ENEMY_BUFF_TIERS = ["NA", "Minor", "Moderate", "Major", "Huge"]
MULTIPLE_ENEMY_BUFF_SCORES = [0.25, 0.5, 1, 2]  # [SBR metric]
ATTACK_ALL_SCORE = [0, 1]  # [SBR metric]
ATTACK_ALL_DEBUFF_FACTOR = [1, 3]  # [-]
SBR_DF = 0.25  # Discount factor of SBR ability per turn

# Leader Skill
LEADER_SKILL_TIERS = [
    "<150%",
    "1 x 150%",
    "2 x 150%",
    "2 x 150-170% / 1 x 170%",
    "2 x 170% / 1 x 180%",
    "200% limited",
    "200% small",
    "200% medium",
    "200% large",
]
LEADER_SKILL_SCORES = [0, 1, 2, 4, 5, 7, 8, 9, 10]  # [-]
LEADER_SKILL_KI = 6.0
LEADER_SKILL_STATS = 4.0

# Super Attack
KI_MODIFIERS_12 = ["1.4", "1.45", "1.5", "1.6"]  # [-]
SUPER_ATTACK_MULTIPLIER_NAMES = [
    "Destructive",
    "Supreme",
    "Immense",
    "Colossal",
    "Mega-Colossal",
]
SUPER_ATTACK_CATEGORIES = ["12 Ki", "18 Ki"]
SUPER_ATTACK_NAMES = ["regular_super_attack", "ultra_super_attack"]
DEFAULT_SUPER_ATTACK_MULTIPLIER_NAMES = {"12 Ki": "Immense", "18 Ki": "Mega-Colossal"}
TUR_SUPER_ATTACK_LEVELS = [10, 15]
LR_SUPER_ATTACK_LEVELS = [20, 25]
SUPER_ATTACK_LEVELS = TUR_SUPER_ATTACK_LEVELS + LR_SUPER_ATTACK_LEVELS
DESTRUCTIVE_MULTIPLIERS = [2.9, 3.4, 4.3, 4.7]
SUPREME_MULTIPLIERS = [4.3, 5.3, 6.3, 0]
IMMENSE_MULTIPLIERS = [5.05, 6.3, 0, 0]
COLOSSAL_MULTIPLIERS = [0, 0, 4.25, 4.5]
MEGA_COLOSSAL_MULTIPLIERS = [0, 0, 5.7, 6.2]

# Counters
COUNTER_ATTACK_MULTIPLIER_NAMES = ["NA", "Tremendous", "Furocious"]
COUNTER_ATTACK_MULTIPLIERS = [0, 3.0, 4.0]

# Special Attacks
SPECIAL_ATTACK_MULTIPLIER_NAMES = [
    "NA",
    "Mega-Colossal",
    "Super-Intense",
    "Ultimate",
    "Super-Ultimate",
]
SPECIAL_ATTACK_MULTIPLIERS = [0, 4.4, 5.0, 5.5, 7.5]

# Giant/Rage Form
GIANT_RAGE_SUPPORT = 2  # Support for nullifying super attacks for a turn

# Domain
DOMAIN_TYPES = ["Increase Damage Received"]

# Turns
MAX_TURN = 20
PEAK_TURN = 5  # Most important turn

# Evaluation
NUM_CONSTANT_ATTRIBUTES = 3
NUM_COPIES_MAX = 5
AVG_PEAK_TURN = 3.471591
PEAK_TURN_STD = 1.857813
ATTTRIBUTE_NAMES = [
    "Leader Skill",
    "SBR",
    "HP",
    "Useability",
    "Healing",
    "Support",
    "APT",
    "Normal Defence",
    "Super Attack Defence",
    "Slot Bonus",
]
NUM_ATTRIBUTES = len(ATTTRIBUTE_NAMES)
EVAL_TURNS = np.arange(1, MAX_TURN + 1, 2)
NUM_EVAL_TURNS = len(EVAL_TURNS)

# Slots
SLOTS = [1, 2, 3]
NUM_SLOTS = len(SLOTS)
RETURN_PERIOD_PER_SLOT = [2, 2, 3]
SLOT_FACTOR_POWER = -1
SLOT_1 = [1] * round(MAX_TURN / RETURN_PERIOD_PER_SLOT[0])
SLOT_2 = [2] * round(MAX_TURN / RETURN_PERIOD_PER_SLOT[1])
SLOT_3 = [3] * round(MAX_TURN / RETURN_PERIOD_PER_SLOT[2])

# Teams
NUM_TEAMS_MAX = 21

# Attacking factors
AVG_ENEMY_DEF = 100000
AVG_ATK_STAT = 5000000
BYPASS_DEFENSE_FACTOR = 1 + AVG_ENEMY_DEF / AVG_ATK_STAT
CRIT_MULTIPLIER = 1.875  # https://docs.google.com/document/d/1Kjk7QnNmfax80qXM8LL4b9woN_GxR0rqyAibR8BoDFY/edit
AEAAT_MULTIPLIER = 1.5  # https://docs.google.com/document/d/1Kjk7QnNmfax80qXM8LL4b9woN_GxR0rqyAibR8BoDFY/edit
DISABLE_GUARD_MULTIPLIER = 1.12  # https://docs.google.com/document/d/1Kjk7QnNmfax80qXM8LL4b9woN_GxR0rqyAibR8BoDFY/edit
AVG_TYPE_ADVANATGE = 1.11  # https://docs.google.com/document/d/1Kjk7QnNmfax80qXM8LL4b9woN_GxR0rqyAibR8BoDFY/edit

# Guard
AVG_GUARD_FACTOR = (
    0.8  # https://www.reddit.com/r/DBZDokkanBattle/comments/weidle/how_damage_taken_works_dokkan_battle_complete/
)
GUARD_MOD = (
    0.5  # https://www.reddit.com/r/DBZDokkanBattle/comments/weidle/how_damage_taken_works_dokkan_battle_complete/
)

# Dodge
DODGE_CANCEL_FACTOR = 0.05

# Health
AVG_HEALTH = 650000
EXPECTED_HEALTH_FRAC = 2 / 3
LESS_HEALTH_REMAINING_MIN = 0.2
MORE_HEALTH_REMAINING_MIN = 0.1

# Enemy Attacks
NUM_ATTACKS_PER_TURN = 8
NUM_SUPER_ATTACKS_PER_TURN = 1
NUM_ENEMY_PHASES = 2  # Average number of enemy phases (in Red Zone fights)
PROBABILITY_KILL_ENEMY_PER_TURN = NUM_ENEMY_PHASES / PEAK_TURN
PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING = np.array(
    [0, PROBABILITY_KILL_ENEMY_PER_TURN / 3, PROBABILITY_KILL_ENEMY_PER_TURN * 2 / 3]
)  # Factors in the fact that the later slots are less likely to get their turn
PROBABILITY_KILL_ENEMY_AFTER_ATTACKING = np.flip(PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING)
# Probability that kill enemy later than after attacking in each slot
PROBABILITY_KILL_ENEMY_BEFORE_RECEIVING_ALL_ATTACKS = np.array(
    [
        PROBABILITY_KILL_ENEMY_PER_TURN / 3,
        PROBABILITY_KILL_ENEMY_PER_TURN * 2 / 3,
        PROBABILITY_KILL_ENEMY_PER_TURN,
    ]
)
NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING = (1 - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING) * np.array(
    [
        NUM_ATTACKS_PER_TURN / 4,
        NUM_ATTACKS_PER_TURN / 2,
        NUM_ATTACKS_PER_TURN - NUM_ATTACKS_PER_TURN / 4,
    ]
)
FRAC_PHYSICAL_SA = 0.075
FRAC_MELEE_SA = 0.2
FRAC_KI_BLAST_SA = 0.4
FRAC_OTHER_SA = 1 - FRAC_PHYSICAL_SA - FRAC_MELEE_SA - FRAC_KI_BLAST_SA
PROBABILITY_SUPER_ATTACK_TYPE = [
    FRAC_PHYSICAL_SA,
    FRAC_MELEE_SA,
    FRAC_KI_BLAST_SA,
    FRAC_OTHER_SA,
    1,
]
FRAC_NORMAL = (NUM_ATTACKS_PER_TURN - NUM_SUPER_ATTACKS_PER_TURN) / NUM_ATTACKS_PER_TURN
SUPER_ATTACK_TYPES = ["Physical", "Melee", "Ki-Blast", "Other", "Any"]
SUPER_ATTACK_NULLIFICATION_TYPES = ["Nullify " + superAttackType for superAttackType in SUPER_ATTACK_TYPES]
NUM_ATTACKS_SLOT_SPECIFIC = np.array(
    [NUM_ATTACKS_PER_TURN / 2, NUM_ATTACKS_PER_TURN / 4, NUM_ATTACKS_PER_TURN / 4]
)  # Average number of attacks recieved per turn. 3 elements correspons to slot 1, 2 and 3.
NUM_ATTACKS_NOT_SLOT_SPECIFIC = NUM_ATTACKS_PER_TURN - NUM_ATTACKS_SLOT_SPECIFIC
PRE_SLOT_1_ATTACK_FRAC = 0.5
NUM_ATTACKS_SLOT_SPECIFIC_BEFORE_ATTACKING = np.array([NUM_ATTACKS_SLOT_SPECIFIC[0] * PRE_SLOT_1_ATTACK_FRAC, 0, 0])
AOE_PROBABILITY_PER_ATTACK = 0.01  # Complete guess
# Probablity of an aoe attack per turn before each slot attacks
NUM_AOE_ATTACKS_BEFORE_ATTACKING = AOE_PROBABILITY_PER_ATTACK * (
    NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING - NUM_ATTACKS_SLOT_SPECIFIC_BEFORE_ATTACKING
)
NUM_AOE_ATTACKS = (
    AOE_PROBABILITY_PER_ATTACK * NUM_ATTACKS_NOT_SLOT_SPECIFIC * (1 - PROBABILITY_KILL_ENEMY_AFTER_ATTACKING)
)
NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING = NUM_AOE_ATTACKS_BEFORE_ATTACKING + NUM_ATTACKS_SLOT_SPECIFIC_BEFORE_ATTACKING
NUM_ATTACKS_SLOT_SPECIFIC_AFTER_ATTACKING = NUM_ATTACKS_SLOT_SPECIFIC - NUM_ATTACKS_SLOT_SPECIFIC_BEFORE_ATTACKING
NUM_ATTACKS_DIRECTED = (
    NUM_AOE_ATTACKS
    + NUM_ATTACKS_SLOT_SPECIFIC_BEFORE_ATTACKING
    + NUM_ATTACKS_SLOT_SPECIFIC_AFTER_ATTACKING * (1 - PROBABILITY_KILL_ENEMY_BEFORE_RECEIVING_ALL_ATTACKS)
)
P_NULLIFY_FROM_DISABLE_ACTIVE = NUM_SUPER_ATTACKS_PER_TURN / NUM_ATTACKS_PER_TURN
P_NULLIFY_FROM_DISABLE_SUPER = (
    (NUM_ATTACKS_PER_TURN - NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING)
    / NUM_ATTACKS_PER_TURN
    * P_NULLIFY_FROM_DISABLE_ACTIVE
)
NUM_SUPER_ATTACKS_SLOT_SPECIFIC = NUM_SUPER_ATTACKS_PER_TURN / NUM_ATTACKS_PER_TURN * NUM_ATTACKS_SLOT_SPECIFIC
NUM_SUPER_ATTACKS_DIRECTED_BEFORE_ATTACKING = np.array(
    [NUM_SUPER_ATTACKS_SLOT_SPECIFIC[0] * PRE_SLOT_1_ATTACK_FRAC, 0, 0]
)
NUM_SUPER_ATTACKS_SLOT_SPECIFIC_AFTER_ATTACKING = (
    NUM_SUPER_ATTACKS_SLOT_SPECIFIC - NUM_SUPER_ATTACKS_DIRECTED_BEFORE_ATTACKING
)
NUM_SUPER_ATTACKS_DIRECTED_AFTER_ATTACKING = NUM_SUPER_ATTACKS_SLOT_SPECIFIC_AFTER_ATTACKING * (
    1 - PROBABILITY_KILL_ENEMY_BEFORE_RECEIVING_ALL_ATTACKS
)
NUM_SUPER_ATTACKS_DIRECTED = NUM_SUPER_ATTACKS_DIRECTED_BEFORE_ATTACKING + NUM_SUPER_ATTACKS_DIRECTED_AFTER_ATTACKING
NUM_NORMAL_ATTACKS_DIRECTED_BEFORE_ATTACKING = NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING * FRAC_NORMAL
NUM_NORMAL_ATTACKS_DIRECTED_AFTER_ATTACKING = (
    NUM_ATTACKS_DIRECTED * FRAC_NORMAL - NUM_ATTACKS_SLOT_SPECIFIC_BEFORE_ATTACKING
)
NUM_NORMAL_ATTACKS_DIRECTED = NUM_NORMAL_ATTACKS_DIRECTED_BEFORE_ATTACKING + NUM_NORMAL_ATTACKS_DIRECTED_AFTER_ATTACKING

# Attacks Performned
NUM_ATTACKS_PERFORMED_PER_UNIT_PER_TURN = 2
PROBABILITY_KILL_ENEMY_PER_ATTACK = (
    PROBABILITY_KILL_ENEMY_PER_TURN / NUM_SLOTS / NUM_ATTACKS_PERFORMED_PER_UNIT_PER_TURN
)

# Enemy Damage
LOOK_AHEAD_FACTOR = 1.2  # Want to know which units will be good in the future when enemies hit even harder
AVG_DAM_VARIANCE = 1.015
MAX_T1_NORMAL_DAM = 550000  # Not including divine wrath and mortal will as can just spam items
MAX_NORMAL_DAM = 700000  # Not including divine wrath and mortal will as can just spam items
MAX_T1_SA_DAM = 1540000  # Not including divine wrath and mortal will as can just spam items
MAX_SA_DAM = 1855000  # Not including divine wrath and mortal will as can just spam items
MAX_NORMAL_DAM_PER_TURN = (
    LOOK_AHEAD_FACTOR
    * AVG_DAM_VARIANCE
    * np.append(
        np.linspace(MAX_T1_NORMAL_DAM, MAX_NORMAL_DAM, PEAK_TURN),
        [MAX_NORMAL_DAM] * (MAX_TURN - PEAK_TURN),
        axis=0,
    )
)
MAX_SA_DAM_PER_TURN = (
    LOOK_AHEAD_FACTOR
    * AVG_DAM_VARIANCE
    * np.append(
        np.linspace(MAX_T1_SA_DAM, MAX_SA_DAM, PEAK_TURN),
        [MAX_SA_DAM] * (MAX_TURN - PEAK_TURN),
        axis=0,
    )
)
AVG_SA_DAM = MAX_SA_DAM_PER_TURN[PEAK_TURN] / LOOK_AHEAD_FACTOR
# maxDefence = LOOK_AHEAD_FACTOR* np.append(np.linspace(100000,110000,PEAK_TURN),[110000]*(MAX_TURN-PEAK_TURN),axis=0)

# Links
MAX_NUM_LINKS = 7
LINKS = [
    "All in the Family",
    "Android Assault",
    "Attack of the Clones",
    "Auto Regeneration",
    "Battlefield Diva",
    "Berserker",
    "Big Bad Bosses",
    "Blazing Battle",
    "Bombardment",
    "Brainiacs",
    "Brutal Beatdown",
    "Budding Warrior",
    "Champion's Strength",
    "Cold Judgement",
    "Connoisseur",
    "Cooler's Armored Squad",
    "Cooler's Underling",
    "Courage",
    "Coward",
    "Crane School",
    "Deficit Boost",
    "Demonic Power",
    "Demonic Ways",
    "Destroyer of the Universe",
    "Dismal Future",
    "Dodon Ray",
    "Energy Absorption",
    "Evil Autocrats",
    "Experienced Fighters",
    "Family Ties",
    "Fear and Faith",
    "Fierce Battle",
    "Flee",
    "Formidable Enemy",
    "Fortuneteller Baba's Fighter",
    "Frieza's Army",
    "Frieza's Minion",
    "Fused Fighter",
    "Fusion",
    "Fusion Failure",
    "Galactic Warriors",
    "Galactuc Visitor",
    "Gaze of Respect",
    "Gentleman",
    "Godly Power",
    "Golden Warrior",
    "Golden Z-Fighter",
    "GT",
    "Guidance of the Dragon Balls",
    "Hardened Grudge",
    "Hatred of Saiyans",
    "Hero",
    "Hero of Justice",
    "High Compatility",
    "Infighter",
    "Infinite Energy",
    "Infinite Regeneration",
    "Kamehameha",
    "Legendary Power",
    "Limit-Breaking Form",
    "Loyalty",
    "Majin",
    "Majin Resurrection Plan",
    "Master of Magic",
    "Mechanical Menaces",
    "Messenger from the Future",
    "Metamorphosis",
    "Money Money Money",
    "More Than Meets the Eye",
    "Namekians",
    "New",
    "New Frieza Army",
    "Nightmare",
    "None",
    "Organic Upgrade",
    "Otherworld Warriors",
    "Over 9000",
    "Over in a Flash",
    "Patrol",
    "Penguin Village Adventure",
    "Power Bestowed by God",
    "Prepared for Battle",
    "Prodigies",
    "Respect",
    "Resurrection F",
    "Revival",
    "Royal Lineage",
    "RR Army",
    "Saiyan Pride",
    "Saiyan Roar",
    "Saiyan Warrior Race",
    "Scientist",
    "Shadow Dragons",
    "Shattering the Limit",
    "Shocking Speed",
    "Signature Pose",
    "Solid Support",
    "Soul vs Soul",
    "Speedy Retribution",
    "Strength in Unity",
    "Strongest Clan in Space",
    "Super Saiyan",
    "Super Strike",
    "Super-God Combat",
    "Supreme Power",
    "Supreme Warrior",
    "Tag Team of Terror",
    "Team Bardock",
    "Team Turles",
    "Telekinesis",
    "Telepathy",
    "The First Awakened",
    "The Ginyu Force",
    "The Hera Clan",
    "The Incredible Adventure",
    "The Innocents",
    "The Saiyan Lineage",
    "The Students",
    "The Wall Standing Tall",
    "Thirst for Conquest",
    "Tough as Nails",
    "Tournament of Power",
    "Transform",
    "Turtle School",
    "Twin Terrors",
    "Ultimate Lifeform",
    "Unbreakable Bond",
    "Universe's Most Malevolent",
    "Warrior Gods",
    "Warriors of Universe 6",
    "World Tournament Champion",
    "World Tournament Reborn",
    "Xenoverse",
    "Z Fighters",
]
LINK_DATA = np.genfromtxt(
    "C:/Users/Tyler/Documents/DokkanAnalysis/LinkTable.csv",
    dtype="str",
    delimiter=",",
    skip_header=False,
)
LINK_NAMES = list(LINK_DATA[1:, 0])
LINK_EFFECT_NAMES = list(LINK_DATA[0, 1:10])

# Ki
MAX_KI = [12, 24]

# Effects

SPECIAL_SUPPORT_EFFECTS = ["Delay Target"]

ORB_CHANGING_EFFECTS = ["Orb Change", "Double Orb Change", "Rainbow Orb Change"]

REGULAR_SUPPORT_EFFECTS = [
    "Ki Support",
    "ATK Support",
    "DEF Support",
    "Scouter",
    "Remove Status Effects",
    "Survive K.O. Attack",
    "P3 ATK Support",
    "P3 DEF Support",
]
SUPPORT_EFFECTS = REGULAR_SUPPORT_EFFECTS + ORB_CHANGING_EFFECTS + SPECIAL_SUPPORT_EFFECTS
EFFECTS = [
    "None",
    "ATK",
    "P2 ATK",
    "DEF",
    "Ki",
    "Lower ATK",
    "Lower DEF",
    "AOE",
    "Seal",
    "Stun",
    "Disable Action",
    "AEAAT",
    "Dmg Red",
    "Dmg Red A",
    "Dmg Red B",
    "Dmg Red against Normals",
    "Guard",
    "Disable Guard",
    "Crit",
    "AdditionalSuper",
    "AAChance",
    "SuperChance",
    "Guaranteed Hit",
    "Evasion",
    "Ki (Type Ki Sphere)",
    "Ki (Ki Sphere)",
    "Ki (Ki Sphere)",
    "Ki (Same Type Ki Sphere)",
    "Ki (Rainbow Ki Sphere)",
    "Heal",
]
EFFECTS.extend(SUPPORT_EFFECTS)
EFFECTS.extend(SUPER_ATTACK_NULLIFICATION_TYPES)
STACK_EFFECTS = ["ATK", "DEF"]
P3_EFFECTS_SUFFIX = ["ATK", "DEF", "Crit", "Evasion", "Disable Action", "ATK Support", "DEF Support"]
SUPPORT_SUPER_ATTACK_EFFECTS = ["Raise Allies ATK"]
ATK_SUPPORT_100_FACTOR = 2  # 100% atk increase support == 2 support points
DEF_SUPPORT_100_FACTOR = 3  # 100% def increase support == 3 support points
AVG_SA_MULT = 5
SUPER_ATTACK_SUPPORT_FACTORS = [ATK_SUPPORT_100_FACTOR / AVG_SA_MULT]
OTHER_SUPER_ATTACK_EFFECTS = ["Crit", "Disable Action", "Lowers ATK", "Lowers DEF", "Attack All"]
SUPER_ATTACK_EFFECTS = STACK_EFFECTS + SUPPORT_SUPER_ATTACK_EFFECTS + OTHER_SUPER_ATTACK_EFFECTS
EXTRA_BUFF_EFFECTS = ["ATK", "DEF", "Crit", "Ki", "Dmg Red", "Evasion"]

# Multi-Chance Effects
MULTI_CHANCE_EFFECTS = ["Crit", "Evasion", "Nullify"]
MULTI_CHANCE_EFFECTS_NO_NULLIFY = [effect for effect in MULTI_CHANCE_EFFECTS if effect != "Nullify"]
CRIT_CHANCES = ["HiPo", "Start of Turn", "Links", "On Super", "Active Skill", "Super Attack Effect"]
EVASION_CHANCES = ["HiPo", "Start of Turn", "Links", "On Super", "Active Skill"]
NULLIFY_CHANCES = ["Disable Action", "SA Counter", "Nullification"]

# Conditions
CONDITIONS = [
    "Turn",
    "Max HP",
    "Min HP",
    "Max Enemy HP",
    "Min Enemy HP",
    "Num Attacks Performed",
    "Num Attacks Received",
    "Finish Skill Activation",
]
CONDITION_LOGIC = ["OR", "AND", "AFTER"]

# Standby Finish Effect Conditions
FINISH_EFFECT_CONDITIONS = ["Ki sphere obtained by allies", "Revive", "Attack performed by allies"]

# Revive
REVIVE_UNIT_SUPPORT_BUFF = 0.75  # Just revives this unit
REVIVE_ROTATION_SUPPORT_BUFF = 1  # Revive whole rotation

# Orb Changing

ORB_REQUIREMENTS = ["Any", "Type", "Rainbow", "Same Type", "Other Type"]
ORB_CHANGING_TYPES = ["No Orb Change"] + ORB_CHANGING_EFFECTS
ORB_TYPES = ["Other", "Same", "Rainbow"]
ORB_COUNTS_NO_ORB_CHANGING = [1.75, 1.75, 1]
ORB_COUNTS_TYPE_ORB_CHANGING = [0.5, 5.25, 1.5]
ORB_COUNTS_DOUBLE_ORB_CHANGING = [0, 6.375, 2]
ORB_COUNTS_RAINBOW_ORB_CHANGING = [2.05, 2.05, 2.7]

KI_PER_SAME_TYPE_ORB = 2.0

# Support
KI_SUPPORT = 1
ATK_DEF_SUPPORT = 0.2
USEABILITY_SUPPORT_FACTOR = 0.2
KI_SUPPORT_FACTOR = 0.25  # Guess
AVG_SOT_STATS = 3
SUPPORT_FACTORS = [
    KI_SUPPORT_FACTOR,
    ATK_SUPPORT_100_FACTOR / AVG_SOT_STATS,
    DEF_SUPPORT_100_FACTOR / AVG_SOT_STATS,
    1,
    0.125,
    0.25,
    ATK_SUPPORT_100_FACTOR,
    DEF_SUPPORT_100_FACTOR,
    0.125,
    0.25,
    0.5,
    6.0,
]

# Hidden Potential + Equips
HIPO_PHY = np.array(
    [
        [2000, 4100, 4400, 4710, 5400],
        [2000, 3700, 4000, 4700, 5000],
        [2000, 3300, 3600, 3910, 4600],
    ]
)
HIPO_STR = np.array(
    [
        [2000, 3700, 4000, 4310, 5000],
        [2000, 4100, 4400, 5100, 5400],
        [2000, 3300, 3600, 3910, 4600],
    ]
)
HIPO_AGL = np.array(
    [
        [2000, 3300, 3600, 3910, 4600],
        [2000, 3700, 4000, 4700, 5000],
        [2000, 4100, 4400, 4710, 5400],
    ]
)
HIPO_TEQ = np.array(
    [
        [2000, 3300, 3600, 3910, 4600],
        [2000, 4100, 4400, 5100, 5400],
        [2000, 3700, 4000, 4310, 5000],
    ]
)
HIPO_INT = np.array(
    [
        [2000, 3700, 4000, 4310, 5000],
        [2000, 3700, 4000, 4700, 5000],
        [2000, 3700, 4000, 4310, 5000],
    ]
)
HIPO_SA_BOOST = [6, 7, 8, 14, 15]
HIPO_RECOVERY_BOOST = [7, 7, 8, 9, 15]
HIPO_TYPE_DEF_BOOST = [5, 6, 7, 8, 10]
HIPO_TYPE_ATK_BOOST = [5, 6, 7, 9, 10]
SA_BOOST_INC = 0.05
CRIT_TAB_INC = 0.0125
AEAAT_TAB_INC = 0.01
DISABLE_GUARD_TAB_INC = 0.01
DEFAULT_TAB_INC = 0.005
TDB_INC = 0.02
BRZ_STAT = 550
BRZ_HIPO = 0.02
SLV_HIPO = 0.05
GLD_HIPO1 = 0.05
GLD_HIPO2 = 0.02
HIPO_BUILDS = [
    ["ATK", "ADD", "CRT"],
    ["ATK", "ADD", "DGE"],
    ["ATK", "CRT", "DGE"],
    ["ATK", "CRT", "ADD"],
    ["ATK", "DGE", "ADD"],
    ["ATK", "DGE", "CRT"],
    ["DEF", "ADD", "CRT"],
    ["DEF", "ADD", "DGE"],
    ["DEF", "CRT", "DGE"],
    ["DEF", "CRT", "ADD"],
    ["DEF", "DGE", "CRT"],
    ["DEF", "DGE", "ADD"],
    ["ADD", "ADD", "CRT"],
    ["ADD", "ADD", "DGE"],
    ["CRT", "CRT", "DGE"],
    ["CRT", "CRT", "ADD"],
    ["DGE", "DGE", "CRT"],
    ["DGE", "DGE", "ADD"],
]

###################################################### Dicts ##########################################################################

# General
yesNo2Bool = dict(zip(YES_NO, [True, False]))
bool2Binary = dict(zip([True, False], [1, 0]))
exclusivity2Rarity = dict(zip(EXCLUSIVITIES, RARITIES))

# Ki
rarity2MaxKi = dict(zip(UNIQUE_RARITIES, MAX_KI))

# Leader skill
leaderSkillConversion = dict(zip(LEADER_SKILL_TIERS, LEADER_SKILL_SCORES))

# Multi-Chance effects
NULL_CRIT_CHANCE_DICT = dict(zip(CRIT_CHANCES, np.zeros(len(CRIT_CHANCES))))
NULL_EVASION_CHANCE_DICT = dict(zip(EVASION_CHANCES, np.zeros(len(EVASION_CHANCES))))
NULL_NULLIFY_CHANCE_DICT = dict(zip(NULLIFY_CHANCES, np.zeros(len(NULLIFY_CHANCES))))
NULL_MULTI_CHANCE_DICT = dict(
    zip(MULTI_CHANCE_EFFECTS, [NULL_CRIT_CHANCE_DICT, NULL_EVASION_CHANCE_DICT, NULL_NULLIFY_CHANCE_DICT])
)

# SBR
sealTurnConversion = dict(zip(DEBUFF_DURATIONS, SEAL_SCORE_PER_TURN))
stunTurnConversion = dict(zip(DEBUFF_DURATIONS, STUN_SCORE_PER_TURN))
attDebuffTurnConversion = dict(zip(DEBUFF_DURATIONS, ATT_DEBUFF_SCORE_PER_TURN))
attDebuffOnAttackConversion = dict(zip(ATT_DEBUFF_ON_ATT_NAMES, ATT_DEBUFF_ON_ATT_SCORE))
multipleEnemyBuffConversion = dict(zip(MULTIPLE_ENEMY_BUFF_TIERS, MULTIPLE_ENEMY_BUFF_SCORES))
attackAllConversion = dict(zip(YES_NO, [1, 0]))
attackAllDebuffConversion = dict(zip(ATTACK_ALL_SCORE, ATTACK_ALL_DEBUFF_FACTOR))

# Support
supportFactorConversion = dict(zip(SUPPORT_EFFECTS, SUPPORT_FACTORS))
superAttackSupportFactorConversion = dict(zip(SUPPORT_SUPER_ATTACK_EFFECTS, SUPER_ATTACK_SUPPORT_FACTORS))

# Orb Changing
orbTypeNoOrbChangingConversion = dict(zip(ORB_TYPES, ORB_COUNTS_NO_ORB_CHANGING))
orbTypeOrbChangingConversion = dict(zip(ORB_TYPES, ORB_COUNTS_TYPE_ORB_CHANGING))
orbTypeDoubleOrbChangingConversion = dict(zip(ORB_TYPES, ORB_COUNTS_DOUBLE_ORB_CHANGING))
orbTypeRainbowOrbChangingConversion = dict(zip(ORB_TYPES, ORB_COUNTS_RAINBOW_ORB_CHANGING))
orbChangeConversion = dict(
    zip(
        ORB_CHANGING_TYPES,
        [
            orbTypeNoOrbChangingConversion,
            orbTypeOrbChangingConversion,
            orbTypeDoubleOrbChangingConversion,
            orbTypeRainbowOrbChangingConversion,
        ],
    )
)

# Counters
counterAttackConversion = dict(zip(COUNTER_ATTACK_MULTIPLIER_NAMES, COUNTER_ATTACK_MULTIPLIERS))

# Super Attacks
superAttackNameConversion = dict(zip(SUPER_ATTACK_CATEGORIES, SUPER_ATTACK_NAMES))
specialAttackConversion = dict(zip(SPECIAL_ATTACK_MULTIPLIER_NAMES, SPECIAL_ATTACK_MULTIPLIERS))
superAttackEZALevels = [
    dict(zip([False, True], TUR_SUPER_ATTACK_LEVELS)),
    dict(zip([False, True], LR_SUPER_ATTACK_LEVELS)),
]
superAttackMultiplerConversion = [
    dict(zip(SUPER_ATTACK_LEVELS, DESTRUCTIVE_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS, SUPREME_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS, IMMENSE_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS, COLOSSAL_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS, MEGA_COLOSSAL_MULTIPLIERS)),
]
superAttackLevelConversion = dict(zip(UNIQUE_RARITIES, superAttackEZALevels))
superAttackConversion = dict(zip(SUPER_ATTACK_MULTIPLIER_NAMES, superAttackMultiplerConversion))

# Slot
slot2ReturnPeriod = dict(zip(SLOTS, RETURN_PERIOD_PER_SLOT))

# Enemy Attacks
saFracConversion = dict(zip(SUPER_ATTACK_NULLIFICATION_TYPES, PROBABILITY_SUPER_ATTACK_TYPE))

# Hidden-Potential + Equips
hiddenPotentalStatsConverter = dict(zip(TYPES, [HIPO_AGL, HIPO_INT, HIPO_PHY, HIPO_STR, HIPO_TEQ]))
# ATK, DEF, ADD, CRT, DGE
HIPO_D0 = {
    "AGL": [0, 0, 0.1, 0, 0],
    "INT": [0, 0, 0, 0, 0.05],
    "PHY": [0, 0, 0.1, 0, 0],
    "STR": [0, 0, 0, 0.1, 0],
    "TEQ": [0, 0, 0, 0.1, 0],
}
HIPO_D1 = {
    ("ADD", "CRT"): [0, 0, 0.18, 0.06, 0],
    ("ADD", "DGE"): [0, 0, 0.18, 0, 0.03],
    ("CRT", "DGE"): [0, 0, 0, 0.18, 0.03],
    ("CRT", "ADD"): [0, 0, 0.06, 0.18, 0],
    ("DGE", "ADD"): [0, 0, 0.06, 0, 0.09],
    ("DGE", "CRT"): [0, 0, 0, 0.06, 0.09],
}
HIPO_D2 = {
    ("ADD", "CRT"): [0, 0, 0.12, 0.06, 0],
    ("ADD", "DGE"): [0, 0, 0.12, 0, 0.03],
    ("CRT", "DGE"): [0, 0, 0, 0.12, 0.03],
    ("CRT", "ADD"): [0, 0, 0.06, 0.12, 0],
    ("DGE", "ADD"): [0, 0, 0.06, 0, 0.06],
    ("DGE", "CRT"): [0, 0, 0, 0.06, 0.06],
}
HIPO_BRZ = {
    "ATK": [BRZ_STAT, 0, 0, 0, 0],
    "DEF": [0, BRZ_STAT, 0, 0, 0],
    "ADD": [0, 0, 2 * BRZ_HIPO, 0, 0],
    "CRT": [0, 0, 0, 2 * BRZ_HIPO, 0],
    "DGE": [0, 0, 0, 0, BRZ_HIPO],
}
HIPO_SLV = {
    "ADD": [0, 0, 2 * SLV_HIPO, 0, 0],
    "CRT": [0, 0, 0, 2 * SLV_HIPO, 0],
    "DGE": [0, 0, 0, 0, SLV_HIPO],
}
HIPO_GLD = {
    ("ADD", "CRT"): [0, 0, 2 * GLD_HIPO1, 2 * GLD_HIPO2, 0],
    ("ADD", "DGE"): [0, 0, 2 * GLD_HIPO1, 0, GLD_HIPO2],
    ("CRT", "DGE"): [0, 0, 0, 2 * GLD_HIPO1, GLD_HIPO2],
    ("CRT", "ADD"): [0, 0, 2 * GLD_HIPO2, 2 * GLD_HIPO1, 0],
    ("DGE", "ADD"): [0, 0, 2 * GLD_HIPO2, 0, GLD_HIPO1],
    ("DGE", "CRT"): [0, 0, 0, 2 * GLD_HIPO2, GLD_HIPO1],
}
