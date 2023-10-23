import click as clc
import datetime as dt
import numpy as np
from scipy.stats import poisson

# I think need a function/Questionaire for every type of passive ability, e.g. one for rainbow orbs, might be good to use classes here. I think this is the only way to cater for all the complexities of Dokkan passives in an automated way

# TODO:
# - Incorporate Super attack and SBR abilities into abilitQuestionaire format
# - Should put at may not be relevant tag onto end of the prompts that may not always be relevant.
# - Should print out relavant parameters back to user, like activationTurn for special ability
# - Group constants so easier to manage
# - Still need to get stats out of links, but can mostly copy whats in dokkanUnit.py
# - Should determine which slot is best for the unit
# - Make separate file where all constants and imports are stored
# - Ideally would just pull data from database, but not up in time for new units. Would be amazing for old units though.
# - Leader skill weight should decrease from 5 as new structure adds more variability between leader skills
# - Make the outputted variables get saved to a file that can be modified later. Also record the inputs if transformed to unrecognizable form. Or can set defaults of quiz as previously input values.
# - Once calculate how many supers do on turn 1, use this in the SBR calculation for debuffs on super. i.e. SBR should be one of the last things to be calculated

# CONSTANTS
YES_NO = ['Y', 'N']
EXCLUSIVITIES = ['DF', 'DFLR', 'LR', 'CLR', 'BU', 'F2P', 'F2PLR', 'Super Strike']
RARITIES = ['TUR', 'LR', 'LR', 'LR', 'TUR', 'TUR', 'LR', 'TUR']
UNIQUE_RARITIES = ['TUR', 'LR']
CLASSES = ['S', 'E']
TYPES = ['AGL', 'INT', 'PHY', 'STR', 'TEQ']
ATT_DEBUFF_PASSIVE_CONVERSION_GRADIENT = 10 # 10% attack down for 2 turns = SBR score of +1
LEADER_SKILL_TIERS = ['<150%', '1 x 150%', '2 x 150%', '2 x 150-170% / 1 x 170%', '2 x 170% / 1 x 180%', '200% limted', '200% small',
                      '200% medium', '200% large']
LEADER_SKILL_SCORES = [0, 1, 2, 4, 5, 7, 8, 9, 10] # [-]
DEBUFF_DURATIONS = ['0', '1', '2'] # [turns]
SEAL_SCORE_PER_TURN = [0, 0.25, 0.75] # [SBR metric/chance to seal]
STUN_SCORE_PER_TURN = [0, 0.5, 1.5] # [SBR metric/chance to stun]
ATT_DEBUFF_SCORE_PER_TURN = [0, 1/3, 1] # [SBR metirc/attack debuff score]
ATT_DEBUFF_ON_ATT_NAMES = ['Lowers', 'Greatly Lowers']
ATT_DEBUFF_ON_ATT_SCORE = [0.25, 0.5] # [attack debuff scrore for lower and greatly lower]
MULTIPLE_ENEMY_BUFF_TIERS = ['None', 'Minor', 'Moderate', 'Major', 'Huge']
MULTIPLE_ENEMY_BUFF_SCORES = [0.25, 0.5, 1, 2] # [SBR metric]
ATTACK_ALL_SCORE = [0, 1] # [SBR metric]
ATTACK_ALL_DEBUFF_FACTOR = [1, 3] # [-]
KI_MODIFIERS_12 = ['1.4', '1.45', '1.5', '1.6'] # [-]
SUPER_ATTACK_MULTIPLIER_NAMES = ['Destructive', 'Supreme', 'Immense', 'Colossal', 'Mega-Colossal']
TUR_SUPER_ATTACK_LEVELS = [10, 15]
LR_SUPER_ATTACK_LEVELS = [20, 25]
SUPER_ATTACK_LEVELS = TUR_SUPER_ATTACK_LEVELS + LR_SUPER_ATTACK_LEVELS
DESTRUCTIVE_MULTIPLIERS = [2.9, 3.4, 4.3, 4.7]
SUPREME_MULTIPLIERS = [4.3, 5.3, 6.3, None]
IMMENSE_MULTIPLIERS = [5.05, 6.3, None, None]
COLOSSAL_MULTIPLIERS = [None, None, 4.25, 4.5]
MEGA_COLOSSAL_MULTIPLIERS = [None, None, 5.7, 6.2]
COUNTER_ATTACK_MULTIPLIER_NAMES = ['NA', 'Tremendous', 'Furocious']
COUNTER_ATTACK_MULTIPLIERS = [0.0, 3.0, 4.0]
SPECIAL_ATTACK_MULTIPLIER_NAMES = ['NA', '', 'Super-Intense','Mega-Colossal', 'Ultimate', 'Super-Ultimate']
SPECIAL_ATTACK_MULTIPLIERS = [0.0, 1.0 , 5.0, 5.4, 6.5, 7.5]
GIANT_RAGE_DURATION = ['0', '1', '2'] # Turns
MAX_TURN = 10
MAX_NUM_LINKS = 7
LINKS = ["All in the Family", "Android Assault", "Attack of the Clones", "Auto Regeneration", "Battlefield Diva", "Berserker", "Big Bad Bosses",
         "Blazing Battle", "Bombardment", "Brainiacs", "Brutal Beatdown", "Budding Warrior", "Champion's Strength", "Cold Judgement",
         "Connoisseur", "Cooler's Armored Squad", "Cooler's Underling", "Courage", "Coward", "Crane School", "Deficit Boost", "Demonic Power",
         "Demonic Ways", "Destroyer of the Universe", "Dismal Future", "Dodon Ray", "Energy Absorption", "Evil Autocrats",
         "Experienced Fighters", "Family Ties", "Fear and Faith", "Fierce Battle", "Flee", "Formidable Enemy", "Fortuneteller Baba's Fighter",
         "Frieza's Army","Frieza's Minion", "Fused Fighter", "Fusion", "Fusion Failure", "Galactic Warriors", "Galactuc Visitor",
         "Gaze of Respect", "Gentleman", "Godly Power", "Golden Warrior", "Golden Z-Fighter", "GT", "Guidance of the Dragon Balls",
         "Hardened Grudge", "Hatred of Saiyans", "Hero", "Hero of Justice", "High Compatility", "Infighter", "Infinite Energy",
         "Infinite Regeneration", "Kamehameha", "Legendary Power", "Limit-Breaking Form", "Loyalty", "Majin", "Majin Resurrection Plan",
         "Master of Magic", "Mechanical Menaces", "Messenger from the Future", "Metamorphosis", "Money Money Money", "More Than Meets the Eye",
         "Namekians", "New", "New Frieza Army", "Nightmare", "None", "Organic Upgrade", "Otherworld Warriors", "Over 9000", "Over in a Flash",
         "Patrol", "Penguin Village Adventure", "Power Bestowed by God", "Prepared for Battle", "Prodigies", "Respect", "Resurrection F",
         "Revival", "Royal Lineage:", "RR Army", "Saiyan Pride", "Saiyan Roar", "Saiyan Warrior Race", "Scientist", "Shadow Dragons",
         "Shattering the Limit", "Shocking Speed", "Signature Pose", "Solid Support", "Soul vs Soul", "Speedy Retribution", "Strength in Unity",
         "Strongest Clan in Space", "Super Saiyan", "Super Strike", "Super-God Combat", "Supreme Power", "Supreme Warrior", "Tag Team of Terror",
         "Team Bardock", "Team Turles", "Telekinesis", "Telepathy", "The First Awakened", "The Ginyu Force", "The Hera Clan",
         "The Incredible Adventure", "The Innocents", "The Saiyan Lineage", "The Students", "The Wall Standing Tall", "Thirst for Conquest",
         "Tough as Nails", "Tournament of Power", "Transform", "Turtle School", "Twin Terrors", "Ultimate Lifeform", "Unbreakable Bond",
         "Universe's Most Malevolent", "Warrior Gods", "Warriors of Universe 6", "World Tournament Champion", "World Tournament Reborn",
         "Xenoverse", "Z Fighters"]
NUM_ATTACKS_PER_TURN = 8
NUM_SUPER_ATTACKS_PER_TURN = 1.0
PEAK_TURN = 3 # Most important turn (actually more like double this, but this is relative to a unit)
NUM_ENEMY_PHASES = 2 # Average number of enemy phases (in Red Zone fights)
PROBABILITY_KILL_ENEMY_PER_TURN = NUM_ENEMY_PHASES / (PEAK_TURN * 2)
PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING = np.array([0.0, PROBABILITY_KILL_ENEMY_PER_TURN / 3, PROBABILITY_KILL_ENEMY_PER_TURN * 2 / 3]) # Factors in the fact that the later slots are less likely to their turn
PROBABILITY_KILL_ENEMY_AFTER_ATTACKING = np.flip(PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING) # Probability that kill enemy later than after attacking in each slot
PROBABILITY_KILL_ENEMY_BEFORE_RECEIVING_ALL_ATTACKS = np.array([PROBABILITY_KILL_ENEMY_PER_TURN / 3, PROBABILITY_KILL_ENEMY_PER_TURN * 2 / 3, PROBABILITY_KILL_ENEMY_PER_TURN])
NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING = (1.0 - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING) * np.array([NUM_ATTACKS_PER_TURN / 4, NUM_ATTACKS_PER_TURN / 2, NUM_ATTACKS_PER_TURN - NUM_ATTACKS_PER_TURN / 4])
SLOTS = ['1', '2', '3']
NUM_SLOTS = len(SLOTS)
EFFECTS = ["None", "Raise ATK", "Raise DEF", "Raise Ki", "Lower ATK", "Lower DEF", "All-Target Super Attack", "Seal Super Attack", "Stun",
           "Disable Action", "Delay Target", "Attack Effective to All", "Damage Reduction", "Damage Reduction Before Attacking",
           "Damage Reduction After Attacking", "NullifyPhysical", "NullifyMelee", "NullifyKi-Blast", "NullifyOther", "NullifyAll", "Guard",
           "Disable Guard", "Forsee Super Attack", "Critical Hit", "Change Ki Spheres to Same Type", "Change Double Ki Spheres to Same Type",
           "Change Ki Spheres to Rainbow", "AdditionalSuper", "AAWithChanceToSuper", "Guaranteed Hit", "Evasion", "Remove Status Effects",
           "Survive K.O. Attack"]
AOE_PROBABILITY_PER_ATTACK = 0.01 # Complete guess
NUM_AOE_ATTACKS_BEFORE_ATTACKING = AOE_PROBABILITY_PER_ATTACK * NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING # Probablity of an aoe attack per turn before each slot attacks
NUM_ATTACKS_NOT_DIRECTED = np.array([NUM_ATTACKS_PER_TURN / 2, NUM_ATTACKS_PER_TURN* 3 / 4, NUM_ATTACKS_PER_TURN * 3 / 4])
NUM_AOE_ATTACKS = AOE_PROBABILITY_PER_ATTACK * NUM_ATTACKS_NOT_DIRECTED * (1.0 - PROBABILITY_KILL_ENEMY_AFTER_ATTACKING)
NUM_ATTACKS_DIRECTED = np.array([NUM_ATTACKS_PER_TURN / 2, NUM_ATTACKS_PER_TURN / 4, NUM_ATTACKS_PER_TURN / 4]) # Average number of attacks recieved per turn. 3 elements correspons to slot 1, 2 and 3.
NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING = np.array([NUM_ATTACKS_PER_TURN / 4, 0.0, 0.0])
NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING = NUM_AOE_ATTACKS_BEFORE_ATTACKING + NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING
NUM_ATTACKS_DIRECTED_AFTER_ATTACKING = NUM_ATTACKS_DIRECTED - NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING
NUM_ATTACKS_RECEIVED = NUM_AOE_ATTACKS + NUM_ATTACKS_DIRECTED * (1.0 - PROBABILITY_KILL_ENEMY_BEFORE_RECEIVING_ALL_ATTACKS * NUM_ATTACKS_DIRECTED_AFTER_ATTACKING / NUM_ATTACKS_DIRECTED)
RESTRICTIONS = ["Turn", "Max HP", "Min HP", "Max Enemy HP", "Min Enemy HP"]
REVIVE_UNIT_SUPPORT_BUFF = 0.75 # Just revives this unit
REVIVE_ROTATION_SUPPORT_BUFF = 1.0 # Revive whole rotation
NUM_OTHER_TYPE_ORBS_NO_ORB_CHANGING = 1.75
NUM_SAME_TYPE_ORBS_NO_ORB_CHANGING = 1.75
NUM_RAINBOW_ORBS_NO_ORB_CHANGING = 1.0
KI_PER_SAME_TYPE_ORB = 2.0
LEADER_SKILL_KI = 6.0
KI_SUPPORT = 1.0
LINK_DATA = np.genfromtxt('C:/Users/Tyler/Documents/DokkanAnalysis/LinkTable.csv', dtype='str', delimiter=',',skip_header=True)
LINK_NAMES = list(LINK_DATA[:,0])
SUPER_ATTACK_TYPES = ["Physical", "Melee", "Ki-Blast", "Other", "All"]
FRAC_PHYSICAL_SA = 0.075
FRAC_MELEE_SA = 0.2
FRAC_KI_BLAST_SA = 0.4
FRAC_OTHER_SA = 1.0 - FRAC_PHYSICAL_SA - FRAC_MELEE_SA - FRAC_KI_BLAST_SA

# Helper dicts
yesNo2Bool = dict(zip(YES_NO, [True, False]))
bool2Binary = dict(zip([True, False], [1, 0]))
exclusivity2Rarity = dict(zip(EXCLUSIVITIES, RARITIES))
leaderSkillConversion = dict(zip(LEADER_SKILL_TIERS, LEADER_SKILL_SCORES))
sealTurnConversion = dict(zip(DEBUFF_DURATIONS, SEAL_SCORE_PER_TURN))
stunTurnConversion = dict(zip(DEBUFF_DURATIONS, STUN_SCORE_PER_TURN))
attDebuffTurnConversion = dict(zip(DEBUFF_DURATIONS, ATT_DEBUFF_SCORE_PER_TURN))
attDebuffOnAttackConversion = dict(zip(ATT_DEBUFF_ON_ATT_NAMES, ATT_DEBUFF_ON_ATT_SCORE))
multipleEnemyBuffConversion = dict(zip(MULTIPLE_ENEMY_BUFF_TIERS, MULTIPLE_ENEMY_BUFF_SCORES))
attackAllConversion = dict(zip(YES_NO, ATTACK_ALL_SCORE))
attackAllDebuffConversion = dict(zip(ATTACK_ALL_SCORE, ATTACK_ALL_DEBUFF_FACTOR))
counterAttackConversion = dict(zip(COUNTER_ATTACK_MULTIPLIER_NAMES, COUNTER_ATTACK_MULTIPLIERS))
specialAttackConversion = dict(zip(SPECIAL_ATTACK_MULTIPLIER_NAMES, SPECIAL_ATTACK_MULTIPLIERS))
superAttackEZALevels = [
    dict(zip([False, True], TUR_SUPER_ATTACK_LEVELS)),
    dict(zip([False, True], LR_SUPER_ATTACK_LEVELS))
]
superattackMultiplerConversion = [
    dict(zip(SUPER_ATTACK_LEVELS, DESTRUCTIVE_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS, SUPREME_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS, IMMENSE_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS, COLOSSAL_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS, MEGA_COLOSSAL_MULTIPLIERS)),
]
superAttackLevelConversion = dict(zip(UNIQUE_RARITIES, superAttackEZALevels))
superAttackConversion = dict(zip(SUPER_ATTACK_MULTIPLIER_NAMES, superattackMultiplerConversion))

class Link:
    def __init__(self,name, commonality):
        self.name = name
        i = LINK_NAMES.index(self.name)
        self.ki = float(LINK_DATA[i,1])
        self.att_SoT = float(LINK_DATA[i,2])
        self.defence = float(LINK_DATA[i,3])
        self.att_OnSuper = float(LINK_DATA[i,4])
        self.crit = float(LINK_DATA[i,5])
        self.dmgRed = float(LINK_DATA[i,6])
        self.dodge = float(LINK_DATA[i,7])
        self.healing = float(LINK_DATA[i,8])
        if commonality == -1:
            self.commonality = float(LINK_DATA[i,9])
        else:
            self.commonality = float(commonality)

class Ability:
    def __init__(self, kit, start):
        self.kit = kit
        self.start = start
    def applyToKit(self):
        pass


class SpecialAbility(Ability):
    def __init__(self, kit, start):
        super().__init__(kit, start)
        self.activationProbability, self.maxTurnRestriction = restrictionQuestionaire()
    def applyToKit(self):
        pass


class Transformation(SpecialAbility):
    def __init__(self, kit, start):
        super().__init__(kit, start)
        self.activationTurn = int(min(self.start + round(1 / self.activationProbability), self.maxTurnRestriction)) # Mean of geometric distribution is 1/p
    def applyToKit(self):
        pass


class SingleTurnAbility(SpecialAbility):
    def __init__(self, kit, start, end):
        super().__init__(kit, start)
        self.end = end
        self.activationTurn = int(max(min(self.start + round(1 / self.activationProbability), self.maxTurnRestriction), PEAK_TURN - 1)) # Mean of geometric distribution is 1/p
    def applyToKit(self):
        pass


class ActiveSkillAttack(SingleTurnAbility):
    def __init__(self, kit, start, end, args):
        super().__init__(kit, start, end)
        self.attackMultiplier = args[0]
        self.attackBuff = args[1]
    def applyToKit(self):
        self.kit.activeAttackTurn = self.activationTurn
        self.kit.activeMult = specialAttackConversion[self.attackMultiplier] + self.attackBuff
        abilityQuestionaire(self.kit, "How many additional single-turn buffs does this active skill attack have?", TurnDependent, self.activationTurn, self.activationTurn + 1)


class Revive(SingleTurnAbility):
    def __init__(self, kit, start, end, args):
        super().__init__(kit, start, end)
        self.hpRegen = args[0]
        self.isThisCharacterOnly = args[1]
    def applyToKit(self):
        self.kit.healing[self.activationTurn + 1][:] += np.minimum([self.hpRegen] * NUM_SLOTS, 1.0)
        if self.isThisCharacterOnly:
            self.kit.support[self.activationTurn][:] += [REVIVE_UNIT_SUPPORT_BUFF] * NUM_SLOTS
        else:
            self.kit.support[self.activationTurn][:] += [REVIVE_ROTATION_SUPPORT_BUFF] * NUM_SLOTS
        abilityQuestionaire(self.kit, "How many additional constant buffs does this revive have?", TurnDependent, self.activationTurn, self.end)


class PassiveAbility(Ability):
    def __init__(self, kit, start, end, activationProbability, effect, buff):
        super().__init__(kit, start)
        self.end = end
        self.duration = end - start
        self.activationProbability = activationProbability
        self.effect = effect
        self.buff = buff * activationProbability
    def applyToKit(self):
        pass


class SuperAttack(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
        self.effectDuration = args[0]
    def applyToKit(self):
        match self.effect:
            case "Raise ATK":
                self.kit.sa12AtkBuff[self.start:self.end] += self.buff
                self.kit.sa12AtkStacks[self.start:self.end] += self.effectDuration # Assuming this doesn't vary in a unit super attack
            case "Raise DEF":
                self.kit.sa12DefBuff[self.start:self.end] += self.buff
                self.kit.sa12DefStacks[self.start:self.end] += self.effectDuration # Assuming this doesn't vary in a unit super attack
        numUnitSuperAttacks = clc.prompt("How many 12 ki unit super attacks does this form have?", default=0)
        for unitSuperAttack in range(numUnitSuperAttacks):
            abilityQuestionaire(self, "How many effects does this unit super attack have?", SuperAttack, ["How many turns does the effect last for?"], [None], [1])  


class TurnDependent(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
        if len(args) > 0: # If called it with overwriting turns
            self.start = args[0]
            self.end = args[1]
            self.duration = self.end - self.start
    def applyToKit(self):
        match self.effect:
            case "Ki":
                self.kit.constantKi[self.start:self.end][:] += self.buff
            case "ATK":
                self.kit.p1Atk[self.start:self.end][:] += self.buff
            case "DEF":
                self.kit.p1Def[self.start:self.end][:] += self.buff
            case "Guard":
                self.kit.guard[self.start:self.end][:] += self.buff
            case "Critical Hit":
                self.kit.crit[self.start:self.end][:] += self.buff
            case "Evasion":
                self.kit.pEvade[self.start:self.end][:] += self.buff 
            case "Disable":
                pNullify = NUM_SUPER_ATTACKS_PER_TURN / NUM_ATTACKS_PER_TURN * np.ones((self.duration, NUM_SLOTS))
                self.kit.pNullify[self.start:self.end][:] = pNullify * (1.0 - self.kit.pNullify[self.start:self.end]) + (1.0 - pNullify) * self.kit.pNullify[self.start:self.end]
            case "Raise Ki (Type Ki Sphere)":
                self.kit.kiPerTypeOrb[self.start:self.end][:] +=  self.buff
            case "AdditonalSuper":
                self.kit.aaPSuper[self.start:self.end][:].append(self.activationProbability)
                self.kit.aaPGuarantee[self.start:self.end][:].append(0.0)
            case "AAWithChanceToSuper":
                chanceToSuper = clc.prompt("What is the chance to super given the additional triggered?", default=0)
                self.kit.aaPSuper[self.start:self.end][:].append(chanceToSuper)
                self.kit.aaPGuarantee[self.start:self.end][:].append(self.activationProbability)

class KiDependent(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
        self.kiRequired = args[0]
        self.pHaveKi = 1.0 - ZTP_CDF(self.kiRequired - 1 - kit.constantKi[start:end][:], kit.randomKi[start:end][:])
        self.activationProbability = activationProbability * self.pHaveKi
    def applyToKit(self):
        match self.effect:
            case "AdditonalSuper":
                self.kit.aaPSuper[self.start:self.end][:].append(self.activationProbability)
                self.kit.aaPGuarantee[self.start:self.end][:].append(0.0)
            case "AAWithChanceToSuper":
                chanceToSuper = clc.prompt("What is the chance to super given the additional triggered?", default=0)
                self.kit.aaPSuper[self.start:self.end][:].append(chanceToSuper)
                self.kit.aaPGuarantee[self.start:self.end][:].append(self.activationProbability)
            case "Attack Effective to All":
                self.kit.SEAAT[self.start:self.end][:] += self.activationProbability


class PerAttackReceived(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
        self.max = args[0]
    def applyToKit(self):
        for i, turn in enumerate(range(self.start, self.end)):
            match self.effect:
                case "Ki":
                    self.kit.constantKi[turn][:] += np.minimum(self.buff * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING + i * NUM_ATTACKS_RECEIVED), self.max)
                case "ATK":
                    self.kit.p2Atk[turn][:] += np.minimum(self.buff * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING + i * NUM_ATTACKS_RECEIVED), self.max)
                case "DEF":
                    self.kit.p2DefA[turn][:] += np.minimum(((2 * i + 1) * NUM_ATTACKS_RECEIVED - 1) * self.buff / 2, self.max)
                case "Critical Hit":
                    self.kit.crit[turn][:] += np.minimum(self.buff * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING + i * NUM_ATTACKS_RECEIVED), self.max)


class WithinSameTurnAfterReceivingAttack(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
    def applyToKit(self):
        match self.effect:
            case "DEF":
                self.kit.p2DefA[self.start:self.end][:] += [self.buff * (NUM_ATTACKS_RECEIVED - 1) / NUM_ATTACKS_RECEIVED] * self.duration
            case "Attack Effective to All":
                self.kit.SEAAT[self.start:self.end][:] = [self.buff * np.minimum(NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING, 1.0)] * self.duration        


class PerRainbowOrb(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
        self.buffFromRainbowOrbs = self.buff * self.kit.numRainbowOrbs
    def applyToKit(self):
        match self.effect:
            case "Critical Hit":
                self.kit.crit[self.start:self.end][:] += self.buffFromRainbowOrbs
            case "Damage Reduction":
                self.kit.dmgRedA[self.start:self.end][:] += self.buffFromRainbowOrbs
                self.kit.dmgRedB[self.start:self.end][:] += self.buffFromRainbowOrbs
            case "Evasion":
                self.kit.pEvade[self.start:self.end][:] += self.buffFromRainbowOrbs


class SlotDepedent(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
        self.slotRequired = args[0]
    def applyToKit(self):
        match self.effect:
            case "ATK":
                self.kit.p1Atk[self.start:self.end][self.slotRequired] += self.buff
            case "DEF":
                self.kit.p1Def[self.start:self.end][self.slotRequired] += self.buff
            case "Gaurd":
                self.kit.guard[self.start:self.end][self.slotRequired] += self.buff


class Nullification(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
        self.hasCounter = args[0]
    def applyToKit(self):
        match self.effect:
            case "NullifyPhysical":
                saFrac = FRAC_PHYSICAL_SA
            case "NullifyMelee":
                saFrac = FRAC_MELEE_SA
            case "NullifyKi-Blast":
                saFrac = FRAC_KI_BLAST_SA
            case "NullifyOther":
                saFrac = FRAC_OTHER_SA
            case "All":
                saFrac = 1.0
        pNullify = self.activationProbability * (1.0 - (1.0 - saFrac) ** 2)
        self.kit.pNullify = (1.0 - self.kit.pNullify) * pNullify + (1.0 - pNullify) * self.kit.pNullify
        if self.hasCounter:
            self.kit.pCounterSA = (1.0 - self.kit.pCounterSA) * pNullify + (1.0 - pNullify) * self.kit.pCounterSA


class Kit:
    def __init__(self, id):
        self.id = id
        # Initialise arrays
        self.saMult12 = np.zeros(MAX_TURN); self.saMult18 = np.zeros(MAX_TURN); self.sa12AtkBuff = np.zeros(MAX_TURN); self.sa12DefBuff = np.zeros(MAX_TURN); self.sa18AtkBuff = np.zeros(MAX_TURN); self.sa18DefBuff = np.zeros(MAX_TURN); self.sa12AtkStacks = np.zeros(MAX_TURN); self.sa12DefStacks = np.zeros(MAX_TURN); self.sa18AtkStacks = np.zeros(MAX_TURN); self.sa18DefStacks = np.zeros(MAX_TURN); self.intentional12Ki = np.zeros(MAX_TURN); self.links = np.array([[None for x in range(MAX_TURN)] for y in range(MAX_NUM_LINKS)]); self.constantKi=LEADER_SKILL_KI*np.ones((MAX_TURN, NUM_SLOTS)); self.kiPerOtherTypeOrb = np.ones((MAX_TURN, NUM_SLOTS)); self.numRainbowOrbs = NUM_RAINBOW_ORBS_NO_ORB_CHANGING * np.ones((MAX_TURN, NUM_SLOTS)); self.numOtherTypeOrbs = NUM_OTHER_TYPE_ORBS_NO_ORB_CHANGING*np.ones((MAX_TURN, NUM_SLOTS)); self.kiPerSameTypeOrb = KI_PER_SAME_TYPE_ORB*np.ones((MAX_TURN, NUM_SLOTS)); self.numSameTypeOrbs = NUM_SAME_TYPE_ORBS_NO_ORB_CHANGING*np.ones((MAX_TURN, NUM_SLOTS)); self.kiPerRainbowKiSphere =np.ones((MAX_TURN, NUM_SLOTS)); self.randomKi = np.zeros((MAX_TURN, NUM_SLOTS)); self.p1Atk=np.zeros((MAX_TURN, NUM_SLOTS)); self.p1Def=np.zeros((MAX_TURN, NUM_SLOTS)); self.p2Atk = np.zeros((MAX_TURN, NUM_SLOTS)); self.p2DefA = np.zeros((MAX_TURN, NUM_SLOTS)); self.SEAAT = np.zeros((MAX_TURN, NUM_SLOTS)); self.guard = np.zeros((MAX_TURN, NUM_SLOTS)); self.crit = np.zeros((MAX_TURN, NUM_SLOTS)); self.pEvade = np.zeros((MAX_TURN, NUM_SLOTS)); self.healing = np.zeros((MAX_TURN, NUM_SLOTS)); self.support = np.zeros((MAX_TURN, NUM_SLOTS)); self.pNullify = np.zeros((MAX_TURN, NUM_SLOTS)); self.aaPSuper = [[[] for x in range(NUM_SLOTS)] for y in range(MAX_TURN)]; self.aaPGuarantee = [[[] for x in range(NUM_SLOTS)] for y in range(MAX_TURN)]; self.linkCommonality = np.zeros(MAX_TURN); self.linkKi= np.zeros(MAX_TURN); self.linkAtkSoT= np.zeros(MAX_TURN); self.linkDef= np.zeros(MAX_TURN); self.linkCrit= np.zeros(MAX_TURN); self.linkAtkOnSuper= np.zeros(MAX_TURN); self.linkDodge=np.zeros(MAX_TURN); self.linkDmgRed= np.zeros(MAX_TURN); self.linkHealing = np.zeros(MAX_TURN); self.dmgRedA = np.zeros((MAX_TURN, NUM_SLOTS)); self.dmgRedB = np.zeros((MAX_TURN, NUM_SLOTS)); self.normalCounterMult = np.zeros((MAX_TURN, NUM_SLOTS)); self.saCounterMult = np.zeros((MAX_TURN, NUM_SLOTS)); self.pCounterSA = np.zeros((MAX_TURN, NUM_SLOTS))
    
    def getLinkEffects(self, start, end):
        for turn in range(start, end):
            for link in self.links[:, turn]:
                self.linkCommonality[turn] += link.commonality
                self.linkKi[turn] += link.commonality*link.ki
                self.linkAtkSoT[turn] += link.commonality*link.att_SoT
                self.linkDef[turn] += link.commonality*link.defence
                self.linkCrit[turn] += link.commonality*link.crit
                self.linkAtkOnSuper[turn] += link.commonality*link.att_OnSuper
                self.linkDodge[turn] += link.commonality*link.dodge
                self.linkDmgRed[turn] += link.commonality*link.dmgRed
                self.linkHealing[turn] += link.commonality*link.healing
        self.linkCommonality /= 7

    def setRandomKi(self, start, end):
        kiCollect = self.kiPerOtherTypeOrb[start:end][:] * self.numOtherTypeOrbs[start:end][:] + self.kiPerSameTypeOrb[start:end][:] * self.numSameTypeOrbs[start:end][:] + self.numRainbowOrbs[start:end][:] * self.kiPerRainbowKiSphere[start:end][:]
        self.randomKi = kiCollect + np.array([self.linkKi[start:end]] * NUM_SLOTS).T + KI_SUPPORT

    def initialQuestionaire(self):
        self.exclusivity = clc.prompt("What is the unit's exclusivity?", type=clc.Choice(EXCLUSIVITIES, case_sensitive=False), default='DF')
        self.rarity = exclusivity2Rarity[self.exclusivity]
        self.name = clc.prompt("What is the unit's name?", default='Super Saiyan Goku')
        self._class = clc.prompt("What is the unit's class?", type=clc.Choice(CLASSES, case_sensitive=False), default='S')
        self._type = clc.prompt("What is the unit's type?", type=clc.Choice(TYPES, case_sensitive=False), default='AGL')
        self.eza = yesNo2Bool[clc.prompt("Has the unit EZA'd?", type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False), default='N')]
        self.jp_date = dt.datetime.strptime(clc.prompt("When did the unit release on the Japanse version of Dokkan? (MM/YY)", default='01/24'),'%m/%y')
        self.gbl_date = dt.datetime.strptime(clc.prompt("When did the unit release on the Global version of Dokkan? (MM/YY)", default='01/24'),'%m/%y')
        self.hp = clc.prompt("What is the unit's base HP stat?", default=0)
        self.att = clc.prompt("What is the unit's base ATT stat?", default=0)
        self._def = clc.prompt("What is the unit's base DEF stat?", default=0)
        self.leader_skill = leaderSkillConversion[clc.prompt("How would you rate the unit's leader skill on a scale of 1-10?\n200% limited - e.g. LR Hatchiyak Goku\n 200% small - e.g. LR Metal Cooler\n 200% medium - e.g. PHY God Goku\n 200% large - e.g. LR Vegeta & Trunks\n", type=clc.Choice(leaderSkillConversion.keys(), case_sensitive=False), default='<150%')]
        self.teams = clc.prompt("How many categories is the unit on? If the unit's viability is limited to certain categories, take this into account.", default=1)
        self.kiMod12 = float(clc.prompt("What is the unit's 12 ki attck modifer?", type=clc.Choice(KI_MODIFIERS_12), default='1.5'))
        self.keepStacking = yesNo2Bool[clc.prompt("Does the unit have the ability to keep stacking before transforming?", type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False), default='N')]
        self.giantRageDuration = clc.prompt("How many turns does the unit's giant/rage mode last for?", type=clc.Choice(GIANT_RAGE_DURATION), default='0')
        

    def sbrQuestionaire(self):
        self.sbr = 0.0        
        if yesNo2Bool[clc.prompt("Does the unit have any SBR abilities?", type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False), default='N')]:
            attackAll = attackAllConversion[clc.prompt("Does the unit attack all enemies on super?",type=clc.Choice(yesNo2Bool.keys(),case_sensitive=False), default='N')]

            seal = sealTurnConversion[clc.prompt("How many turns does the unit seal for?", type=clc.Choice(sealTurnConversion.keys()), default='0')]
            if seal != 0:
                seal *= clc.prompt("What is the unit's chance to seal?", default=0.0) # Scale by number of enemies for all enemy seal, same for stun

            stun = stunTurnConversion[clc.prompt("How many turns does the unit stun for?", type=clc.Choice(stunTurnConversion.keys()), default='0')]
            if stun != 0:
                stun *= clc.prompt("What is the unit's chance to stun?", default=0.0)
            
            attDebuffOnAtk = attDebuffTurnConversion[clc.prompt("How many turns does the unit lower the enemy attack by attacking?", type=clc.Choice(attDebuffTurnConversion.keys()), default='0')]
            if attDebuffOnAtk != 0:
                attDebuffOnAtk *= attDebuffOnAttackConversion[clc.prompt("How much is attack lowered by on attack?", type=clc.Choice(attDebuffOnAttackConversion.keys(), case_sensitive=False), default='Lowers')]

            attDebuffPassive = attDebuffTurnConversion[clc.prompt("How many turns does the unit lower the enemy attack passively?", type=clc.Choice(attDebuffTurnConversion.keys()), default='0')]
            if attDebuffPassive != 0:
                attDebuffPassive *= clc.prompt("How much is attack lowered passively?", default=0.3)
            
            multipleEnemyBuff = multipleEnemyBuffConversion[clc.prompt("How much of a buff does the unit get when facing multiple enemies?",type=clc.Choice(multipleEnemyBuffConversion.keys(), case_sensitive=False), default='None')]
            
            self.sbr += attackAllDebuffConversion[attackAll] * (seal + stun + attDebuffOnAtk) + attDebuffPassive + multipleEnemyBuff + attackAll

    def turnBasedQuestionaire(self):
        start = 0
        transformations = abilityQuestionaire(self, "How many transformations does the unit have?", Transformation, start)
        numForms = len(transformations) + 1 # Plus 1 to account for base form
        for form in range(numForms):
            # First determine end turn for each form
            if transformations:
                end = (transformations[0]).activationTurn
                transformations.pop(0)
            else:
                end = MAX_TURN
            formDuration = end - start
            self.saMult12[start:end] = [superAttackConversion[clc.prompt("What is the form's 12 ki super attack multiplier?", type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES), default='Immense')][superAttackLevelConversion[self.rarity][self.eza]]]*formDuration
            abilityQuestionaire(self, "How many effects does this unit's 12 ki super attack have?", SuperAttack, ["How many turns does the effect last for?"], [None], [1])
            if self.rarity == 'LR':
                abilityQuestionaire(self, "How many effects does this unit's 18 ki super attack have?", SuperAttack, ["How many turns does the effect last for?"], [None], [1])
                self.intentional12Ki[start:end] = [yesNo2Bool[clc.prompt("Should a 12 Ki be targetted for this form?", default='N')]]*formDuration
            self.normalCounterMult[start:end][:] += [counterAttackConversion[clc.prompt("What is the unit's normal counter multiplier?", type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False), default='NA')]]
            self.saCounterMult[start:end][:] += [counterAttackConversion[clc.prompt("What is the unit's super attack counter multiplier?", type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False), default='NA')]]
            for linkIndex in range(MAX_NUM_LINKS):
                linkName = clc.prompt(f"What is the form's link # {linkIndex+1}", type = clc.Choice(LINKS, case_sensitive=False), default='Fierce Battle')
                linkCommonality = clc.prompt("If has an ideal linking partner, what is the chance this link is active?", default=-1.0)
                self.links[linkIndex][start:end] = [Link(linkName, linkCommonality)] * formDuration 
            self.getLinkEffects(start, end)
            #assert len(np.unique(self.links))==MAX_NUM_LINKS, 'Duplicate links'
            abilityQuestionaire(self, "How many unconditional buffs does the form have?", TurnDependent, start, end)
            abilityQuestionaire(self, "How many turn dependent buffs does the form have?", TurnDependent, start, end, ["What turn does the buff start from?", "What turn does the buff end on?"], [None, None], [start, end])
            abilityQuestionaire(self, "How many different buffs does the form get on attacks received?", PerAttackReceived, start, end, ["What is the maximum buff?"], [None], [1.0])
            abilityQuestionaire(self, "How many different buffs does the form get within the same turn after receiving an attack?", WithinSameTurnAfterReceivingAttack, start, end)
            abilityQuestionaire(self, "How many slot specific buffs does the form have?", SlotDepedent, start, end, ["Which slot is required?"], [clc.Choice(SLOTS)], [1])
            self.setRandomKi(start, end) # Compute the average ki each turn which has a random component because need to be able to compute how much ki the unit gets on average for ki dependent effects
            abilityQuestionaire(self, "How many ki dependent buffs does the form have?", KiDependent, start, end, ["What is the required ki?"], [None], [24])
            abilityQuestionaire(self, "How many different nullification abilities does the form have?", Nullification, start, end, ["Does this nullification have counter?"], [YES_NO], ["N"])
            abilityQuestionaire(self, "How many revive skills does the form have?", Revive, start, end,  ["How much HP is revived with?", "Does the revive only apply to this unit?"], [None, None], [0.7, 'N'])
            abilityQuestionaire(self, "How many active skill attacks does the form have?", ActiveSkillAttack, start, end, ["What is the attack multiplier?", "What is the additional attack buff when performing thes attack?"], [clc.Choice(specialAttackConversion.keys()), None], ['Ultimate', 0.0])
            start = end # set this for next form
    def getKitFromUser(self):
        clc.echo(f'Hello! This program will guide you through inputting the data required to enter Dokkan unit ID={self.id} into the database')
        self.initialQuestionaire()
        self.turnBasedQuestionaire()
        self.sbrQuestionaire()

# Helper functions

def maxHealthCDF(maxHealth):
    return 4 / 3 * maxHealth ** 3 - maxHealth ** 2 + 2 / 3 * maxHealth

def ZTP_CDF(x,Lambda):
    return (poisson.cdf(x,Lambda)-poisson.cdf(0,Lambda))/(1-poisson.cdf(0,Lambda))

def restrictionQuestionaire():
    numRestrictions = clc.prompt("How many different restrictions does this ability have?", default=0)
    totalRestrictionProbability = 0.0
    turnRestriction = MAX_TURN
    for restriction in range(numRestrictions):
        restrictionProbability = 0.0
        restrictionType = clc.prompt("What type of restriction is it?", type=clc.Choice(RESTRICTIONS,case_sensitive=False), default="Turn")
        if restrictionType == "Turn":
            turnRestriction = min(clc.prompt("What is the turn restriction (relative to the character)?", default=3), turnRestriction)
        elif restrictionType == "Max HP":
            restrictionProbability = 1.0 - maxHealthCDF(clc.prompt("What is the maximum HP restriction?", default=0.7))
        elif restrictionType == "Min HP":
            restrictionProbability =  maxHealthCDF(clc.prompt("What is the minimum HP restriction?", default=0.7))
        elif restrictionType == "Enemy Max HP":
            restrictionProbability = 1.0 - clc.prompt("What is the maximum enemy HP restriction?", default=0.5)
        elif restrictionType == "Enemy Min HP":
            restrictionProbability = clc.prompt("What is the minimum enemy HP restriction?", default=0.5)
        # Assume independence
        totalRestrictionProbability = (1.0 - totalRestrictionProbability) * restrictionProbability + (1.0 - restrictionProbability) * totalRestrictionProbability
    return 1.0 - totalRestrictionProbability, turnRestriction

def abilityQuestionaire(kit, abilityPrompt, abilityClass, start, end = MAX_TURN, parameterPrompts=[], types=[], defaults=[], parameters=[]):
    numAbilities = clc.prompt(abilityPrompt, default=0)
    abilities = []
    for i in range(numAbilities): 
        for j, parameterPrompt in enumerate(parameterPrompts):
            if len(types) == 0: # If don't care about prompt choices
                parameters.append(clc.prompt(parameterPrompt))
            else:
                parameters.append(clc.prompt(parameterPrompt, type = types[j], default = defaults[j]))
        if isinstance(abilityClass, Transformation):
            ability = abilityClass(kit, start)
        elif issubclass(abilityClass, PassiveAbility):
            effect = clc.prompt("What type of buff does the unit get?",type=clc.Choice(EFFECTS, case_sensitive=False), default="ATK")
            activationProbability = clc.prompt("What is the probability this ability activates?", default=1.0)
            buff = clc.prompt("What is the value of the buff?", default=0.0)
            ability = abilityClass(kit, start, end, activationProbability, effect, buff, parameters)
        elif issubclass(abilityClass, SingleTurnAbility):
            ability = abilityClass(kit, start, end, parameters)
        ability.applyToKit()
        abilities.append(ability)
    return abilities
        

if __name__ == '__main__':
    kit = Kit(1).getKitFromUser()