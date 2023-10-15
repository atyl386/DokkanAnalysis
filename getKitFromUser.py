import click as clc
import datetime as dt
import numpy as np

# I think need a function/Questionaire for every type of passive ability, e.g. one for rainbow orbs, might be good to use classes here. I think this is the only way to cater for all the complexities of Dokkan passives in an automated way

# TODO:
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
LEADER_SKILL_TIERS = ['<150%', '1 x 150%', '2 x 150%', '2 x 150-170% / 1 x 170%', '2 x 170% / 1 x 180%', '200% limted', '200% small', '200% medium', '200% large']
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
LINKS = ["All in the Family", "Android Assault", "Attack of the Clones", "Auto Regeneration", "Battlefield Diva", "Berserker", "Big Bad Bosses", "Blazing Battle", "Bombardment", "Brainiacs", "Brutal Beatdown", "Budding Warrior", "Champion's Strength", "Cold Judgement", "Connoisseur", "Cooler's Armored Squad", "Cooler's Underling", "Courage", "Coward", "Crane School", "Deficit Boost", "Demonic Power", "Demonic Ways", "Destroyer of the Universe", "Dismal Future", "Dodon Ray", "Energy Absorption", "Evil Autocrats", "Experienced Fighters", "Family Ties", "Fear and Faith", "Fierce Battle", "Flee", "Formidable Enemy", "Fortuneteller Baba's Fighter", "Frieza's Army","Frieza's Minion", "Fused Fighter", "Fusion", "Fusion Failure", "Galactic Warriors", "Galactuc Visitor", "Gaze of Respect", "Gentleman", "Godly Power", "Golden Warrior", "Golden Z-Fighter", "GT", "Guidance of the Dragon Balls", "Hardened Grudge", "Hatred of Saiyans", "Hero", "Hero of Justice", "High Compatility", "Infighter", "Infinite Energy", "Infinite Regeneration", "Kamehameha", "Legendary Power", "Limit-Breaking Form", "Loyalty", "Majin", "Majin Resurrection Plan", "Master of Magic", "Mechanical Menaces", "Messenger from the Future", "Metamorphosis", "Money Money Money", "More Than Meets the Eye", "Namekians", "New", "New Frieza Army", "Nightmare", "None", "Organic Upgrade", "Otherworld Warriors", "Over 9000", "Over in a Flash", "Patrol", "Penguin Village Adventure", "Power Bestowed by God", "Prepared for Battle", "Prodigies", "Respect", "Resurrection F", "Revival", "Royal Lineage:", "RR Army", "Saiyan Pride", "Saiyan Roar", "Saiyan Warrior Race", "Scientist", "Shadow Dragons", "Shattering the Limit", "Shocking Speed", "Signature Pose", "Solid Support", "Soul vs Soul", "Speedy Retribution", "Strength in Unity", "Strongest Clan in Space", "Super Saiyan", "Super Strike", "Super-God Combat", "Supreme Power", "Supreme Warrior", "Tag Team of Terror", "Team Bardock", "Team Turles", "Telekinesis", "Telepathy", "The First Awakened", "The Ginyu Force", "The Hera Clan", "The Incredible Adventure", "The Innocents", "The Saiyan Lineage", "The Students", "The Wall Standing Tall", "Thirst for Conquest", "Tough as Nails", "Tournament of Power", "Transform", "Turtle School", "Twin Terrors", "Ultimate Lifeform", "Unbreakable Bond", "Universe's Most Malevolent", "Warrior Gods", "Warriors of Universe 6", "World Tournament Champion", "World Tournament Reborn", "Xenoverse", "Z Fighters"]
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
EFFECTS = ["None", "Ki", "Att", "Def", "SEAAT", "Crit", "Guard", "Disable", "KiPerTypeKiSphere"]
AOE_PROBABILITY_PER_ATTACK = 0.01 # Complete guess
NUM_AOE_ATTACKS_BEFORE_ATTACKING = AOE_PROBABILITY_PER_ATTACK * NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING # Probablity of an aoe attack per turn before each slot attacks
NUM_ATTACKS_NOT_DIRECTED = np.array([NUM_ATTACKS_PER_TURN / 2, NUM_ATTACKS_PER_TURN* 3 / 4, NUM_ATTACKS_PER_TURN * 3 / 4])
NUM_AOE_ATTACKS = AOE_PROBABILITY_PER_ATTACK * NUM_ATTACKS_NOT_DIRECTED * (1.0 - PROBABILITY_KILL_ENEMY_AFTER_ATTACKING)
NUM_ATTACKS_DIRECTED = np.array([NUM_ATTACKS_PER_TURN / 2, NUM_ATTACKS_PER_TURN / 4, NUM_ATTACKS_PER_TURN / 4]) # Average number of attacks recieved per turn. 3 elements correspons to slot 1, 2 and 3.
NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING = np.array([NUM_ATTACKS_PER_TURN / 4, 0.0, 0.0])
NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING = NUM_AOE_ATTACKS_BEFORE_ATTACKING + NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING
NUM_ATTACKS_DIRECTED_AFTER_ATTACKING = NUM_ATTACKS_DIRECTED - NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING
NUM_ATTACKS_RECEIVED = NUM_AOE_ATTACKS + NUM_ATTACKS_DIRECTED * (1.0 - PROBABILITY_KILL_ENEMY_BEFORE_RECEIVING_ALL_ATTACKS * NUM_ATTACKS_DIRECTED_AFTER_ATTACKING / NUM_ATTACKS_DIRECTED)
RESTRICTIONS = ["Max HP", "Min HP"]
REVIVE_UNIT_SUPPORT_BUFF = 0.75 # Just revives this unit
REVIVE_ROTATION_SUPPORT_BUFF = 1.0 # Revive whole rotation
NUM_RAINBOW_ORBS_NO_ORB_CHANGING = 1.0

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


class Ability:
    def __init__(self, kit, start, end, activationProbability):
        self.kit = kit
        self.start = start
        self.end = end
        self.duration = end - start
        self.activationProbability = activationProbability
    def setEffect(self):
        pass


class SpecialAbility(Ability):
    def __init__(self, *args, **kwargs):
        super().__init__(kit, *args, **kwargs)
        self.activationTurn = int(max(self.start + round(1 / self.activationProbability), PEAK_TURN - 1)) # Mean of geometric distribution is 1/p
    def setEffect(self):
        pass


class ActiveSkillAttack(SpecialAbility):
    def __init__(self, kit, start, end, activationProbability, attackMultiplier, attackBuff):
        super().__init__(kit, start, end, activationProbability)
        self.attackMultiplier = attackMultiplier
        self.attackBuff = attackBuff
    def setEffect(self):
        self.kit.activeAttackTurn = self.activationTurn
        self.kit.activeMult = specialAttackConversion[self.attackMultiplier] + self.attackBuff
        abilityQuestionaire(self.kit, self.activationTurn, self.activationTurn + 1, "How many additional single-turn buffs does this active skill attack have?", TurnDependentAbility)


class Revive(SpecialAbility):
    def __init__(self, kit, start, end, activationProbability, hpRegen, isThisCharacterOnly):
        super().__init__(kit, start, end, activationProbability)
        self.hpRegen = hpRegen
        self.isThisCharacterOnly = isThisCharacterOnly
    def setEffect(self):
        self.kit.healing[self.activationTurn + 1][:] += np.minimum([self.hpRegen] * NUM_SLOTS, 1.0)
        if self.isThisCharacterOnly:
            self.kit.support[self.activationTurn][:] += [REVIVE_UNIT_SUPPORT_BUFF] * NUM_SLOTS
        else:
            self.kit.support[self.activationTurn][:] += [REVIVE_ROTATION_SUPPORT_BUFF] * NUM_SLOTS
        abilityQuestionaire(self.kit, self.activationTurn, self.end, "How many additional constant buffs does this revive have?", TurnDependentAbility)


class PassiveAbility(Ability):
    def __init__(self, kit, start, end, activationProbability, effect, buff):
        super().__init__(kit, start, end, activationProbability)
        self.effect = effect
        self.buff = buff * activationProbability
    def setEffect(self):
        pass      


class TurnDependentAbility(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
        if args != None: # If called it with overwriting turns
            self.start = args[0]
            self.end = args[1]
            self.duration = self.end - self.start
    def setEffect(self):
        match self.effect:
            case "Att":
                self.kit.p1Att[self.start:self.end][:] += self.buff
            case "Def":
                self.kit.p1Def[self.start:self.end][:] += self.buff
            case "Guard":
                self.kit.guard[self.start:self.end][:] += self.buff
            case "Crit":
                self.kit.crit[self.start:self.end][:] += self.buff
            case "Disable":
                pNullify = NUM_SUPER_ATTACKS_PER_TURN / NUM_ATTACKS_PER_TURN * np.ones((self.duration, NUM_SLOTS))
                self.kit.pNullify[self.start:self.end][:] = pNullify * (1.0 - self.kit.pNullify[self.start:self.end]) + (1.0 - pNullify) * self.kit.pNullify[self.start:self.end]
            case "KiPerTypeKiSphere":
                self.kit.kiPerTypeKiSphere[self.start:self.end][:] +=  self.buff


class PerAttackReceived(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
        self.max = args[0]
    def setEffect(self):
        for i, turn in enumerate(range(self.start, self.end)):
            match self.effect:
                case "Ki":
                    self.kit.ki[turn][:] += np.minimum(self.buff * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING + i * NUM_ATTACKS_RECEIVED), self.max)
                case "Att":
                    self.kit.p2Att[turn][:] += np.minimum(self.buff * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING + i * NUM_ATTACKS_RECEIVED), self.max)
                case "Def":
                    self.kit.p2DefA[turn][:] += np.minimum(((2 * i + 1) * NUM_ATTACKS_RECEIVED - 1) * self.buff / 2, self.max)            


class WithinSameTurnAfterReceivingAttack(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
    def setEffect(self):
        match self.effect:
            case "Def":
                self.kit.p2DefA[self.start:self.end][:] += [self.buff * (NUM_ATTACKS_RECEIVED - 1) / NUM_ATTACKS_RECEIVED] * self.duration
            case "SEAAT":
                self.kit.SEAAT[self.start:self.end][:] = [self.buff * np.minimum(NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING, 1.0)] * self.duration        


class PerRainbowOrb(PassiveAbility):
    def __init__(self, kit, start, end, activationProbability, effect, buff, args):
        super().__init__(kit, start, end, activationProbability, effect, buff)
    def setEffect(self):
        match self.effect:
            case "Crit":
                self.kit.crit[self.start:self.end][:] += self.buff * self.kit.numRainbowOrbs

class Kit:
    def __init__(self, id):
        self.id = id
        # Initialise arrays
        self.sa_mult_12 = np.zeros(MAX_TURN); self.sa_mult_18 = np.zeros(MAX_TURN); self.sa_12_att_buff = np.zeros(MAX_TURN); self.sa_12_def_buff = np.zeros(MAX_TURN); self.sa_18_att_buff = np.zeros(MAX_TURN); self.sa_18_def_buff = np.zeros(MAX_TURN); self.sa_12_att_stacks = np.zeros(MAX_TURN); self.sa_12_def_stacks = np.zeros(MAX_TURN); self.sa_18_att_stacks = np.zeros(MAX_TURN); self.sa_18_def_stacks = np.zeros(MAX_TURN); self.intentional12Ki = np.zeros(MAX_TURN); self.links = [['' for x in range(MAX_NUM_LINKS)] for y in range(MAX_TURN)]; self.ki=np.zeros((MAX_TURN, NUM_SLOTS)); self.p1Att=np.zeros((MAX_TURN, NUM_SLOTS)); self.p1Def=np.zeros((MAX_TURN, NUM_SLOTS)); self.p2Att = np.zeros((MAX_TURN, NUM_SLOTS)); self.p2DefA = np.zeros((MAX_TURN, NUM_SLOTS)); self.SEAAT = np.zeros((MAX_TURN, NUM_SLOTS)); self.crit = np.zeros((MAX_TURN, NUM_SLOTS)); self.healing = np.zeros((MAX_TURN, NUM_SLOTS)); self.support = np.zeros((MAX_TURN, NUM_SLOTS)); self.pNullify = np.zeros((MAX_TURN, NUM_SLOTS)); self.kiPerTypeKiSphere = np.ones((MAX_TURN, NUM_SLOTS)); self.numRainbowOrbs = NUM_RAINBOW_ORBS_NO_ORB_CHANGING * np.ones((MAX_TURN, NUM_SLOTS))

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
        self.ki_mod_12 = float(clc.prompt("What is the unit's 12 ki attck modifer?", type=clc.Choice(KI_MODIFIERS_12), default='1.5'))
        self.normal_counter_mult = counterAttackConversion[clc.prompt("What is the unit's normal counter multiplier?", type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False), default='NA')]
        self.sa_counter_mult = counterAttackConversion[clc.prompt("What is the unit's super attack counter multiplier?", type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False), default='NA')]
        self.keep_stacking = yesNo2Bool[clc.prompt("Does the unit have the ability to keep stacking before transforming?", type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False), default='N')]
        self.giant_rage_duration = clc.prompt("How many turns does the unit's giant/rage mode last for?", type=clc.Choice(GIANT_RAGE_DURATION), default='0')

        # Default Parameters
        

    def sbrQuestionaire(self):
        self.sbr = 0.0        
        if yesNo2Bool[clc.prompt("Does the unit have any SBR abilities?", type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False), default='N')]:
            attack_all = attackAllConversion[clc.prompt("Does the unit attack all enemies on super?",type=clc.Choice(yesNo2Bool.keys(),case_sensitive=False), default='N')]

            seal = sealTurnConversion[clc.prompt("How many turns does the unit seal for?", type=clc.Choice(sealTurnConversion.keys()), default='0')]
            if seal != 0:
                seal *= clc.prompt("What is the unit's chance to seal?", default=0.0) # Scale by number of enemies for all enemy seal, same for stun

            stun = stunTurnConversion[clc.prompt("How many turns does the unit stun for?", type=clc.Choice(stunTurnConversion.keys()), default='0')]
            if stun != 0:
                stun *= clc.prompt("What is the unit's chance to stun?", default=0.0)
            
            att_debuff_on_att = attDebuffTurnConversion[clc.prompt("How many turns does the unit lower the enemy attack by attacking?", type=clc.Choice(attDebuffTurnConversion.keys()), default='0')]
            if att_debuff_on_att != 0:
                att_debuff_on_att *= attDebuffOnAttackConversion[clc.prompt("How much is attack lowered by on attack?", type=clc.Choice(attDebuffOnAttackConversion.keys(), case_sensitive=False), default='Lowers')]

            att_debuff_passive = attDebuffTurnConversion[clc.prompt("How many turns does the unit lower the enemy attack passively?", type=clc.Choice(attDebuffTurnConversion.keys()), default='0')]
            if att_debuff_passive != 0:
                att_debuff_passive *= clc.prompt("How much is attack lowered passively?", default=0.3)
            
            multiple_enemy_buff = multipleEnemyBuffConversion[clc.prompt("How much of a buff does the unit get when facing multiple enemies?",type=clc.Choice(multipleEnemyBuffConversion.keys(), case_sensitive=False), default='None')]
            
            self.sbr += attackAllDebuffConversion[attack_all] * (seal + stun + att_debuff_on_att) + att_debuff_passive + multiple_enemy_buff + attack_all

    def turnBasedQuestionaire(self):
        formTurnStarts = [1] # Every unit starts on their first turn
        while(formTurnStarts[-1] != MAX_TURN+1):
            formTurnStarts.append(clc.prompt(f"On what turn does the unit transform? Will keep asking until enter {MAX_TURN+1}", default=MAX_TURN+1))
        for form in range(len(formTurnStarts)-1): # Don't do last one as that indicates end
            start = formTurnStarts[form] - 1 # Get the first turn of 'form'. Subtract 1 to make indexing easier.
            end = formTurnStarts[form + 1] - 1
            formDuration = end - start
            self.ki[start:end][:] += [clc.prompt("What is the form's start of turn ki?", default=0)]
            self.p1Att[start:end][:] += [clc.prompt("What is the form's start of turn Attack?", default=2.0)]
            self.p1Def[start:end][:] += [clc.prompt("What is the form's start of turn Defence?", default=2.0)]
            self.sa_mult_12[start:end] = [superAttackConversion[clc.prompt("What is the form's 12 ki super attack multiplier?", type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES), default='Immense')][superAttackLevelConversion[self.rarity][self.eza]]]*formDuration
            self.sa_12_att_buff[start:end] = [clc.prompt("What is the form's 12 ki attack buff?", default=0.0)]*formDuration
            if self.sa_12_att_buff[start] != 0:
                self.sa_12_att_stacks[start:end] = [clc.prompt("How many turns does the form's 12 ki attack buff last for?", default=1)]*formDuration
            self.sa_12_def_buff[start:end] = [clc.prompt("What is the form's 12 ki defense buff?", default=0.0)]*formDuration
            if self.sa_12_def_buff[start] != 0:
                self.sa_12_def_stacks[start:end] = [clc.prompt("How many turns does the form's 12 ki defense buff last for?", default=1)]*formDuration
            if self.rarity == 'LR':
                self.sa_mult_18[start:end] = [superAttackConversion[clc.prompt("What is the form's 18 ki super attack multiplier?", type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES), default='Mega-Colossal')][superAttackLevelConversion[self.rarity][self.eza]]]*formDuration
                self.sa_18_att_buff[start:end] = [clc.prompt("What is the form's 18 ki attack buff?", default=0.0)]*formDuration
                if self.sa_18_att_buff[start] != 0:
                    self.sa_18_att_stacks[start:end] = [clc.prompt("How many turns does the form's 18 ki attack buff last for?", default=1)]*formDuration
                self.sa_18_def_buff[start:end] = [clc.prompt("What is the form's 18 ki defense buff?", default=0.0)]*formDuration
                if self.sa_18_def_buff[start] != 0:
                    self.sa_18_def_stacks[start:end] = [clc.prompt("How many turns does form's 18 ki defense buff last for?", default=1)]*formDuration
                self.intentional12Ki[start:end] = [yesNo2Bool[clc.prompt("Should a 12 Ki be targetted for this form?", default='N')]]*formDuration
            for link in range(MAX_NUM_LINKS):
                self.links[start:end][link] = [clc.prompt(f"What is the form's link # {link+1}", type = clc.Choice(LINKS, case_sensitive=False), default='Fierce Battle')]*formDuration
            #assert len(np.unique(self.links))==MAX_NUM_LINKS, 'Duplicate links'
            abilityQuestionaire(self, start, end, "How many other unconditional buffs does the form have?", ["What is the value of the buff?"], TurnDependentAbility)
            abilityQuestionaire(self, start, end, "How many turn dependent buffs does the form have?", TurnDependentAbility, ["What turn does the buff start from?", "What turn does the buff end on?"], [None, None], [start, end])
            abilityQuestionaire(self, start, end, "How many different buffs does the form get on attacks received?", PerAttackReceived, ["How much is the buff per attack received?", "What is the maximum buff?"], [None, None], [0.2, 1.0])
            abilityQuestionaire(self, start, end, "How many different buffs does the form get within the same turn after receiving an attack?", WithinSameTurnAfterReceivingAttack, ["How much is the buff upon receiving an attack?"], [None], [0.5])
            abilityQuestionaire(self, start, end, "How many revive skills does the form have?", Revive, ["How much HP is revived with?", "Does the revive only apply to this unit?"], [None, None], [0.7, 'N'])
            abilityQuestionaire(self, start, end, "How many active skill attacks does the form have?", ActiveSkillAttack, ["What is the attack multiplier?", "What is the additional attack buff when performing thes attack?"], [clc.Choice(specialAttackConversion.keys()), None], ['Ultimate', 0.0])

    def getKitFromUser(self):
        clc.echo(f'Hello! This program will guide you through inputting the data required to enter Dokkan unit ID={self.id} into the database')
        self.initialQuestionaire()
        self.turnBasedQuestionaire()
        self.sbrQuestionaire()

# Helper functions

def maxHealthCDF(maxHealth):
    return 4 / 3 * maxHealth ** 3 - maxHealth ** 2 + 2 / 3 * maxHealth

def restrictionQuestionaire():
    numRestrictions = clc.prompt("How many different restrictions does this ability have?", default=0)
    totalRestrictionProbability = 0.0
    for restriction in range(numRestrictions):
        restrictionType = clc.prompt("What type of restriction is it?", type=clc.Choice(RESTRICTIONS,case_sensitive=False), default="Max HP")
        match restrictionType:
            case "Max HP":
                restrictionProbability = 1.0 - maxHealthCDF(clc.prompt("What is the maximum HP restriction?", default=0.7))
            case "Min HP":
                restrictionProbability =  maxHealthCDF(clc.prompt("What is the minimum HP restriction?", default=0.7))
        # Assume independence
        totalRestrictionProbability = (1.0 - totalRestrictionProbability) * restrictionProbability + (1.0 - restrictionProbability) * totalRestrictionProbability
    return 1.0 - totalRestrictionProbability

def abilityQuestionaire(kit, start, end, abilityPrompt, abilityClass, parameterPrompts=[], types=[], defaults=[]):
    numAbilities = clc.prompt(abilityPrompt, default=0)
    for ability in range(numAbilities):
        parameters = []
        for i, parameterPrompt in enumerate(parameterPrompts):
            if types[i] == None:
                parameters.append(clc.prompt(parameterPrompt), default = defaults[i])
            else:
                parameters.append(clc.prompt(parameterPrompt), type = types[i], default = defaults[i])
        if issubclass(abilityClass, PassiveAbility):
            effect = clc.prompt("What type of buff does the unit get?",type=clc.Choice(EFFECTS, case_sensitive=False), default="Att")
            activationProbability = clc.prompt("What is the probability this ability activates?", default=1.0)
            abilityClass(kit, start, end, activationProbability, effect, parameters).setEffect()
        elif issubclass(abilityClass, SpecialAbility):
            probabilityPerTurn = restrictionQuestionaire()
            abilityClass(kit, start, end, probabilityPerTurn, parameters).setEffect()       
        

if __name__ == '__main__':
    kit = Kit(1).getKitFromUser()