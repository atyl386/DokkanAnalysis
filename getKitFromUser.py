import click as clc
import datetime as dt
import numpy as np
from scipy.stats import poisson

# I think need a function/Questionaire for every type of passive ability, e.g. one for rainbow orbs, might be good to use classes here. I think this is the only way to cater for all the complexities of Dokkan passives in an automated way

# TODO:
# - Instead of asking user how many of something, should ask until they enteran exit key aka while loop instead of for loop
# - How are we dealing with unit-super attacks? I think this works if user specifies the correct activation probabilities
# - Should read up on python optimisation techniques once is running and se how long it takes. But try be efficient you go.
# - I think the 20x3 state matrix needs to be used to compute the best path
# - Whilst the state matrix is the ideal way, for now just assume a user inputed slot for each form
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
MAX_TURN = 20
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
PEAK_TURN = 5 # Most important turn
NUM_ENEMY_PHASES = 2 # Average number of enemy phases (in Red Zone fights)
PROBABILITY_KILL_ENEMY_PER_TURN = NUM_ENEMY_PHASES / PEAK_TURN
PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING = np.array([0.0, PROBABILITY_KILL_ENEMY_PER_TURN / 3, PROBABILITY_KILL_ENEMY_PER_TURN * 2 / 3]) # Factors in the fact that the later slots are less likely to their turn
PROBABILITY_KILL_ENEMY_AFTER_ATTACKING = np.flip(PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING) # Probability that kill enemy later than after attacking in each slot
PROBABILITY_KILL_ENEMY_BEFORE_RECEIVING_ALL_ATTACKS = np.array([PROBABILITY_KILL_ENEMY_PER_TURN / 3, PROBABILITY_KILL_ENEMY_PER_TURN * 2 / 3, PROBABILITY_KILL_ENEMY_PER_TURN])
NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING = (1.0 - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING) * np.array([NUM_ATTACKS_PER_TURN / 4, NUM_ATTACKS_PER_TURN / 2, NUM_ATTACKS_PER_TURN - NUM_ATTACKS_PER_TURN / 4])
SLOTS = [1, 2, 3]
NUM_SLOTS = len(SLOTS)
RETURN_PERIOD_PER_SLOT = [2, 2, 3]
FRAC_PHYSICAL_SA = 0.075
FRAC_MELEE_SA = 0.2
FRAC_KI_BLAST_SA = 0.4
FRAC_OTHER_SA = 1.0 - FRAC_PHYSICAL_SA - FRAC_MELEE_SA - FRAC_KI_BLAST_SA
PROBABILITY_SUPER_ATTACK_TYPE = [FRAC_PHYSICAL_SA, FRAC_MELEE_SA, FRAC_KI_BLAST_SA, FRAC_OTHER_SA, 1.0]
SUPER_ATTACK_TYPES = ["Physical", "Melee", "Ki-Blast", "Other", "Any"]
SUPER_ATTACK_NULLIFICATION_TYPES = ["Nullify " + superAttackType for superAttackType in SUPER_ATTACK_TYPES]
EFFECTS = ["None", "Raise ATK", "Raise DEF", "Raise Ki", "Lower ATK", "Lower DEF", "All-Target Super Attack", "Seal Super Attack", "Stun",
           "Disable Action", "Delay Target", "Attack Effective to All", "Damage Reduction", "Damage Reduction Before Attacking",
           "Damage Reduction After Attacking", "Guard", "Disable Guard", "Forsee Super Attack", "Critical Hit",
           "Change Ki Spheres to Same Type", "Change Double Ki Spheres to Same Type", "Change Ki Spheres to Rainbow", "AdditionalSuper",
           "AAWithChanceToSuper", "Guaranteed Hit", "Evasion", "Remove Status Effects", "Survive K.O. Attack"]
EFFECTS.extend(SUPER_ATTACK_NULLIFICATION_TYPES)
AOE_PROBABILITY_PER_ATTACK = 0.01 # Complete guess
NUM_AOE_ATTACKS_BEFORE_ATTACKING = AOE_PROBABILITY_PER_ATTACK * NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING # Probablity of an aoe attack per turn before each slot attacks
NUM_ATTACKS_NOT_DIRECTED = np.array([NUM_ATTACKS_PER_TURN / 2, NUM_ATTACKS_PER_TURN* 3 / 4, NUM_ATTACKS_PER_TURN * 3 / 4])
NUM_AOE_ATTACKS = AOE_PROBABILITY_PER_ATTACK * NUM_ATTACKS_NOT_DIRECTED * (1.0 - PROBABILITY_KILL_ENEMY_AFTER_ATTACKING)
NUM_ATTACKS_DIRECTED = np.array([NUM_ATTACKS_PER_TURN / 2, NUM_ATTACKS_PER_TURN / 4, NUM_ATTACKS_PER_TURN / 4]) # Average number of attacks recieved per turn. 3 elements correspons to slot 1, 2 and 3.
NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING = np.array([NUM_ATTACKS_PER_TURN / 4, 0.0, 0.0])
NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING = NUM_AOE_ATTACKS_BEFORE_ATTACKING + NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING
NUM_ATTACKS_DIRECTED_AFTER_ATTACKING = NUM_ATTACKS_DIRECTED - NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING
NUM_ATTACKS_RECEIVED = NUM_AOE_ATTACKS + NUM_ATTACKS_DIRECTED * (1.0 - PROBABILITY_KILL_ENEMY_BEFORE_RECEIVING_ALL_ATTACKS * NUM_ATTACKS_DIRECTED_AFTER_ATTACKING / NUM_ATTACKS_DIRECTED)
P_NULLIFY_FROM_DISABLE_ACTIVE = NUM_SUPER_ATTACKS_PER_TURN / NUM_ATTACKS_PER_TURN
P_NULLIFY_FROM_DISABLE_SUPER = (NUM_ATTACKS_PER_TURN - NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING) * P_NULLIFY_FROM_DISABLE_ACTIVE
RESTRICTIONS = ["Turn", "Max HP", "Min HP", "Max Enemy HP", "Min Enemy HP"]
REVIVE_UNIT_SUPPORT_BUFF = 0.75 # Just revives this unit
REVIVE_ROTATION_SUPPORT_BUFF = 1.0 # Revive whole rotation
NUM_OTHER_TYPE_ORBS_NO_ORB_CHANGING = 1.75
NUM_SAME_TYPE_ORBS_NO_ORB_CHANGING = 1.75
NUM_RAINBOW_ORBS_NO_ORB_CHANGING = 1.0
KI_PER_SAME_TYPE_ORB = 2.0
LEADER_SKILL_KI = 6.0
LEADER_SKILL_STATS = 4.0
KI_SUPPORT = 1.0
LINK_DATA = np.genfromtxt('C:/Users/Tyler/Documents/DokkanAnalysis/LinkTable.csv', dtype='str', delimiter=',',skip_header=True)
LINK_NAMES = list(LINK_DATA[:,0])

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
slot2ReturnPeriod = dict(zip(SLOTS, RETURN_PERIOD_PER_SLOT))
saFracConversion = dict(zip(SUPER_ATTACK_NULLIFICATION_TYPES, PROBABILITY_SUPER_ATTACK_TYPE))

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
            turnRestriction = min(clc.prompt("What is the turn restriction (relative to the form's starting turn)?", default=3), turnRestriction)
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

def abilityQuestionaire(form, abilityPrompt, abilityClass, parameterPrompts=[], types=[], defaults=[]):
    parameters = []
    numAbilities = clc.prompt(abilityPrompt, default=0)
    abilities = []
    for i in range(numAbilities): 
        for j, parameterPrompt in enumerate(parameterPrompts):
            if len(types) == 0: # If don't care about prompt choices
                parameters.append(clc.prompt(parameterPrompt))
            else:
                parameters.append(clc.prompt(parameterPrompt, type = types[j], default = defaults[j]))
        if issubclass(abilityClass, PassiveAbility):
            effect = clc.prompt("What type of buff does the unit get?",type=clc.Choice(EFFECTS, case_sensitive=False), default="Raise ATK")
            activationProbability = clc.prompt("What is the probability this ability activates?", default=1.0)
            buff = clc.prompt("What is the value of the buff?", default=0.0)
            ability = abilityClass(form, activationProbability, effect, buff, parameters)
        elif issubclass(abilityClass, SingleTurnAbility):
            ability = abilityClass(form, parameters)
        abilities.append(ability)
    return abilities


class Kit:
    def __init__(self, id):
        self.id = id # unique ID for unit
        self.getConstants()
        self.getSBR()
        self.getForms()
        self.getStates()

    def getConstants(self):
        self.exclusivity = clc.prompt("What is the unit's exclusivity?", type=clc.Choice(EXCLUSIVITIES, case_sensitive=False), default='DF')
        self.rarity = exclusivity2Rarity[self.exclusivity]
        self.name = clc.prompt("What is the unit's name?", default='Super Saiyan Goku')
        self._class = clc.prompt("What is the unit's class?", type=clc.Choice(CLASSES, case_sensitive=False), default='S')
        self._type = clc.prompt("What is the unit's type?", type=clc.Choice(TYPES, case_sensitive=False), default='AGL')
        self.eza = yesNo2Bool[clc.prompt("Has the unit EZA'd?", type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False), default='N')]
        self.jp_date = dt.datetime.strptime(clc.prompt("When did the unit release on the Japanse version of Dokkan? (MM/YY)", default='01/24'),'%m/%y')
        self.gbl_date = dt.datetime.strptime(clc.prompt("When did the unit release on the Global version of Dokkan? (MM/YY)", default='01/24'),'%m/%y')
        self.HP = clc.prompt("What is the unit's base HP stat?", default=0)
        self.ATK = clc.prompt("What is the unit's base ATT stat?", default=0)
        self.DEF = clc.prompt("What is the unit's base DEF stat?", default=0)
        self.leader_skill = leaderSkillConversion[clc.prompt("How would you rate the unit's leader skill on a scale of 1-10?\n200% limited - e.g. LR Hatchiyak Goku\n 200% small - e.g. LR Metal Cooler\n 200% medium - e.g. PHY God Goku\n 200% large - e.g. LR Vegeta & Trunks\n", type=clc.Choice(leaderSkillConversion.keys(), case_sensitive=False), default='<150%')]
        self.teams = clc.prompt("How many categories is the unit on? If the unit's viability is limited to certain categories, take this into account.", default=1)
        self.kiMod12 = float(clc.prompt("What is the unit's 12 ki attck modifer?", type=clc.Choice(KI_MODIFIERS_12), default='1.5'))
        self.keepStacking = yesNo2Bool[clc.prompt("Does the unit have the ability to keep stacking before transforming?", type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False), default='N')]
        self.giantRageDuration = clc.prompt("How many turns does the unit's giant/rage mode last for?", type=clc.Choice(GIANT_RAGE_DURATION), default='0')

    def getSBR(self):
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
            
            self.sbr = attackAllDebuffConversion[attackAll] * (seal + stun + attDebuffOnAtk) + attDebuffPassive + multipleEnemyBuff + attackAll
        return self.sbr
    
    def getForms(self):
        startTurn = 1
        self.forms = []
        numForms = clc.prompt("How many forms does the unit have?", default = 1)
        for i in range(numForms):
            slot = int(clc.prompt(f"Which slot is form # {i + 1} best suited for?", default = 2))
            if i == numForms - 1:
                endTurn = MAX_TURN
            else:
                transformationProbabilityPerTurn, maxTransformationTurn = restrictionQuestionaire()
                endTurn = startTurn + int(min(RETURN_PERIOD_PER_SLOT[slot - 1] * round(1 / transformationProbabilityPerTurn), maxTransformationTurn)) - 1 # Mean of geometric distribution is 1/p
            self.forms.append(Form(startTurn, endTurn, slot))
            startTurn = endTurn + 1
        for form in self.forms:        
            form.saMult12 = superAttackConversion[clc.prompt("What is the form's 12 ki super attack multiplier?", type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES), default='Immense')][superAttackLevelConversion[self.rarity][self.eza]]
            superAttackEffects = abilityQuestionaire(form, "How many effects does this unit's 12 ki super attack have?", SuperAttack, ["How many turns does the effect last for?"], [None], [1])
            for superAttackEffect in superAttackEffects:
                superAttackEffect.setSuperAttack()
            if self.rarity == "LR":
                form.intentional12Ki = yesNo2Bool[clc.prompt("Should a 12 Ki be targetted for this form?", default='N')]
                if not(form.intentional12Ki):
                    ultraSuperAttackEffects = abilityQuestionaire(form, "How many effects does this unit's 18 ki super attack have?", SuperAttack, ["How many turns does the effect last for?"], [None], [1])
                    for ultraSuperAttackEffect in ultraSuperAttackEffects:
                        ultraSuperAttackEffect.setUltraSuperAttack()
            form.normalCounterMult = counterAttackConversion[clc.prompt("What is the unit's normal counter multiplier?", type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False), default='NA')]
            form.saCounterMult = counterAttackConversion[clc.prompt("What is the unit's super attack counter multiplier?", type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False), default='NA')]
            form.getLinks()
            #assert len(np.unique(links))==MAX_NUM_LINKS, 'Duplicate links'
            form.abilities.extend(abilityQuestionaire(form, "How many unconditional buffs does the form have?", StartOfTurn))
            form.abilities.extend(abilityQuestionaire(form, "How many turn dependent buffs does the form have?", TurnDependent, ["What turn does the buff start from?", "What turn does the buff end on?"], [None, None], [form.startTurn, form.endTurn]))
            form.abilities.extend(abilityQuestionaire(form, "How many different buffs does the form get on attacks received?", PerAttackReceived, ["What is the maximum buff?"], [None], [1.0]))
            form.abilities.extend(abilityQuestionaire(form, "How many different buffs does the form get within the same turn after receiving an attack?", WithinSameTurnAfterReceivingAttack))
            form.abilities.extend(abilityQuestionaire(form, "How many slot specific buffs does the form have?", SlotDependent, ["Which slot is required?"], [None], [1]))
            #form.updateRandomKi(start, end) # Compute the average ki each turn which has a random component because need to be able to compute how much ki the unit gets on average for ki dependent effects
            form.abilities.extend(abilityQuestionaire(form, "How many ki dependent buffs does the form have?", KiDependent, ["What is the required ki?"], [None], [24]))
            form.abilities.extend(abilityQuestionaire(form, "How many different nullification abilities does the form have?", Nullification, ["Does this nullification have counter?"], [YES_NO], ["N"]))
            form.abilities.extend(abilityQuestionaire(form, "How many revive skills does the form have?", Revive, ["How much HP is revived with?", "Does the revive only apply to this unit?"], [None, None], [0.7, 'N']))
            form.abilities.extend(abilityQuestionaire(form, "How many active skill attacks does the form have?", ActiveSkillAttack, ["What is the attack multiplier?", "What is the additional attack buff when performing thes attack?"], [clc.Choice(specialAttackConversion.keys()), None], ['Ultimate', 0.0]))

    def getStates(self):
        self.states = []
        turn = 1
        formIdx = 0
        while turn <= MAX_TURN:
            form = self.forms[formIdx]
            slot = form.slot
            state = State(slot, turn)
            for ability in form.abilities:
                ability.applyToState(state)
            self.states.append(state)
            turn += RETURN_PERIOD_PER_SLOT[slot - 1]
            if turn > form.endTurn:
                formIdx += 1
            

class Form:
    def __init__(self, startTurn, endTurn, slot):
        self.startTurn = startTurn
        self.endTurn = endTurn
        self.slot = slot
        self.linkNames = [''] * MAX_NUM_LINKS 
        self.linkCommonality = 0.0; self.linkKi= 0.0; self.linkAtkSoT= 0.0; self.linkDef= 0.0; self.linkCrit = 0.0
        self.linkAtkOnSuper = 0.0; self.linkDodge = 0.0; self.linkDmgRed = 0.0; self.linkHealing = 0.0
        self.saMult12 = 0.0; self.saMult18 = 0.0; # Super Attack Multipliers
        self.sa12AtkBuff = 0.0; self.sa18AtkBuff = 0.0; # Super Attack ATK buffs
        self.sa12DefBuff = 0.0; self.sa18DefBuff = 0.0; # Super Attack DEF buffs
        self.sa12Disable = False; self.sa18Disable = False # Super Attack disable action effects
        self.sa12Crit = 0.0; self.sa18Crit = 0.0 # Super Attack crit effects
        self.sa12AtkStacks = 0; self.sa18AtkStacks = 0 # Super Attack ATK stacks
        self.sa12Deftacks = 0; self.sa18DefStacks = 0 # Super Attack DEF stacks
        self.intentional12Ki = False
        self.normalCounterMult = 0.0; self.saCounterMult = 0.0
        self.abilities = [] # This will be a list of Ability objects which will be iterated through each state to call applyToState.

    def getLinks(self):
        for linkIndex in range(MAX_NUM_LINKS):
            self.linkNames[linkIndex] = clc.prompt(f"What is the form's link # {linkIndex+1}", type = clc.Choice(LINKS, case_sensitive=False), default='Fierce Battle')
            linkCommonality = clc.prompt("If has an ideal linking partner, what is the chance this link is active?", default=-1.0)
            link = Link(self.linkNames[linkIndex], linkCommonality)
            self.linkCommonality += link.commonality
            self.linkKi += link.ki
            self.linkAtkSoT += link.att_SoT
            self.linkDef += link.defence
            self.linkCrit += link.crit
            self.linkAtkOnSuper += link.att_OnSuper
            self.linkDodge += link.dodge
            self.linkDmgRed += link.dmgRed
            self.linkHealing += link.healing
        self.linkCommonality /= MAX_NUM_LINKS


class Link:
    def __init__(self,name, commonality):
        self.name = name
        i = LINK_NAMES.index(self.name)
        self.ki = float(LINK_DATA[i,10])
        self.att_SoT = float(LINK_DATA[i,11])
        self.defence = float(LINK_DATA[i,12])
        self.att_OnSuper = float(LINK_DATA[i,13])
        self.crit = float(LINK_DATA[i,14])
        self.dmgRed = float(LINK_DATA[i,15])
        self.dodge = float(LINK_DATA[i,16])
        self.healing = float(LINK_DATA[i,17])
        if commonality == -1:
            self.commonality = float(LINK_DATA[i,9])
        else:
            self.commonality = float(commonality)


class State:
    def __init__(self, slot, turn):
        self.slot = slot # Slot no.
        self.turn = turn
        self.constantKi = LEADER_SKILL_KI; self.randomKi = KI_SUPPORT # Constant and Random ki
        self.kiPerOtherTypeOrb = 1; self.kiPerSameTypeOrb = KI_PER_SAME_TYPE_ORB; self.kiPerRainbowKiSphere = 1 # Ki per orb
        self.numRainbowOrbs = NUM_RAINBOW_ORBS_NO_ORB_CHANGING; self.numOtherTypeOrbs = NUM_OTHER_TYPE_ORBS_NO_ORB_CHANGING
        self.numSameTypeOrbs = NUM_SAME_TYPE_ORBS_NO_ORB_CHANGING # num of orbs
        self.p1Atk = LEADER_SKILL_STATS; self.p1Def = LEADER_SKILL_STATS # Start of turn stats (Phase 1)
        self.p2Atk = 0.0 # Phase 2 ATK
        self.p2DefA = 0.0; self.p2DefB = 0.0 # Phase 2 DEF (Before and after attacking)
        self.AEAAT = 0.0 # Probability for attacks effective against all types
        self.guard = 0.0 # Probability of guarding
        self.crit = 0.0 # Probability of performing a critical hit
        self.pEvade = 0.0 # Probability of evading
        self.healing = 0.0 # Fraction of health healed every turn
        self.support = 0.0 # Support score
        self.pNullify = 0.0 # Probability of nullifying all enemy super attacks
        self.aaPSuper = []; self.aaPGuarantee = [] # Probabilities of doing additional super attacks and guaranteed additionals 
        self.dmgRedA = 0.0; self.dmgRedB = 0.0 # Damage reduction before and after attacking
        self.pCounterSA = 0.0 # Probability of countering an enemy super attack
        self.numAttacksReceived = 0 # Number of attacks received so far in this form. Assuming update the state.numAttacksReceievd after the abilities have been processed for that turn
    
    def updateRandomKi(self, form):
        kiCollect = self.kiPerOtherTypeOrb * self.numOtherTypeOrbs + self.kiPerSameTypeOrb * self.numSameTypeOrbs + self.numRainbowOrbs * self.kiPerRainbowKiSphere
        self.randomKi += kiCollect + form.linkKi
    

class Ability:
    def __init__(self, form):
        self.form = form


class SpecialAbility(Ability):
    def __init__(self, form):
        super().__init__(form)
        self.activationProbability, self.maxTurnRestriction = restrictionQuestionaire()


class SingleTurnAbility(SpecialAbility):
    def __init__(self, form):
        super().__init__(form)
        self.activationTurn = int(max(min(round(1 / self.activationProbability), self.maxTurnRestriction), PEAK_TURN - 1)) # Mean of geometric distribution is 1/p


class ActiveSkillAttack(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.attackMultiplier = args[0]
        self.attackBuff = args[1]
        self.activeAttackTurn = self.activationTurn
        self.activeMult = specialAttackConversion[self.attackMultiplier] + self.attackBuff
        self.form.abilities.extend(abilityQuestionaire(self.form, "How many additional single-turn buffs does this active skill attack have?", TurnDependent, ["This is the activation turn. Please press enter to continue", "This is the form's next turn. Please press enter to continue"], [None, None], [self.activationTurn, self.activationTurn + RETURN_PERIOD_PER_SLOT[self.form.slot]]))

    def applyToState(self, state):
        #TODO
        # Should apply the apt for an active skill attack on the activation turn
        pass


class Revive(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.hpRegen = args[0]
        self.isThisCharacterOnly = args[1]
        self.form.abilities.extend(abilityQuestionaire(self.form, "How many additional constant buffs does this revive have?", TurnDependent, ["This is the activation turn. Please press enter to continue", "This is the form's end turn. Please press enter to continue"], [None, None], [self.activationTurn, self.form.endTurn]))
        
    def applyToState(self, state):
        if state.turn == self.activationTurn:
            state.healing = np.min(state.healing + self.hpRegen, 1.0)
        if self.isThisCharacterOnly:
            state.support += REVIVE_UNIT_SUPPORT_BUFF
        else:
            state.support += REVIVE_ROTATION_SUPPORT_BUFF


class PassiveAbility(Ability):
    def __init__(self, form, activationProbability, effect, buff):
        super().__init__(form)
        self.activationProbability = activationProbability
        self.effect = effect
        self.buff = buff * activationProbability


class SuperAttack(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, args):
        super().__init__(form, activationProbability, effect, buff)
        self.effectDuration = args[0]

    def setSuperAttack(self):
        match self.effect:
            case "Raise ATK":
                self.form.sa12AtkBuff += self.buff # += here for unit super attack probability weightings
                self.form.sa12AtkStacks = self.effectDuration # Assuming this doesn't vary in a unit super attack
            case "Raise DEF":
                self.form.sa12DefBuff += self.buff # += here for unit super attack probability weightings
                self.form.sa12DefStacks = self.effectDuration # Assuming this doesn't vary in a unit super attack
            case "Critical Hit":
                self.form.sa12Crit += self.buff # += here for unit super attack probability weightings
        numUnitSuperAttacks = clc.prompt("How many 12 ki unit super attacks does this form have?", default=0)
        for unitSuperAttack in range(numUnitSuperAttacks):
            unitSuperAttackEffects = abilityQuestionaire(self.form, "How many effects does this unit super attack have?", SuperAttack, ["How many turns does the effect last for?"], [None], [1])
            for unitSuperAttackEffect in unitSuperAttackEffects:
                unitSuperAttackEffect.setSuperAttack()

    def setUltraSuperAttack(self):
         match self.effect:
            case "Raise ATK":
                self.form.sa18AtkBuff += self.buff # += here for unit super attack probability weightings
                self.form.sa18AtkStacks = self.effectDuration # Assuming this doesn't vary in a unit super attack
            case "Raise DEF":
                self.form.sa18DefBuff += self.buff # += here for unit super attack probability weightings
                self.form.sa18DefStacks = self.effectDuration # Assuming this doesn't vary in a unit super attack
            case "Disable Action":
                self.form.sa18Disable = bool(self.buff)
            case "Critical Hit":
                self.form.sa18Crit += self.buff # += here for unit super attack probability weightings        


class StartOfTurn(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, start = 0, end = MAX_TURN, ki = 0, slots = SLOTS):
        super().__init__(form, activationProbability, effect, buff)
        self.start = start
        self.end = end
        self.ki = ki
        self.slots = slots

    def applyToState(self, state):
        pHaveKi = 1.0 - ZTP_CDF(self.ki - 1 - state.constantKi, state.randomKi)
        self.buff = self.buff * pHaveKi
        self.activationProbability *= pHaveKi
        if state.turn >= self.start and state.turn <= self.end and state.slot in self.slots:
            match self.effect:
                case "Ki":
                    state.constantKi += self.buff
                case "ATK":
                    state.p1Atk += self.buff
                case "DEF":
                    state.p1Def += self.buff
                case "Guard":
                    state.guard += self.buff
                case "Critical Hit":
                    state.crit += self.buff
                case "Evasion":
                    state.pEvade += self.buff 
                case "Disable Action":
                    state.pNullify = P_NULLIFY_FROM_DISABLE_ACTIVE * (1.0 - state.pNullify) + (1.0 - P_NULLIFY_FROM_DISABLE_ACTIVE) * state.pNullify
                case "Raise Ki (Type Ki Sphere)":
                    state.kiPerTypeOrb +=  self.buff
                case "AdditonalSuper":
                    state.aaPSuper.append(self.activationProbability)
                    state.aaPGuarantee.append(0.0)
                case "AAWithChanceToSuper":
                    chanceToSuper = clc.prompt("What is the chance to super given the additional triggered?", default=0)
                    state.aaPSuper.append(chanceToSuper)
                    state.aaPGuarantee.append(self.activationProbability)
                case "Attack Effective to All":
                    state.AEAAT += self.activationProbability


class TurnDependent(StartOfTurn):
    def __init__(self, form, activationProbability, effect, buff, args):
        start = args[0]
        end = args[1]
        super().__init__(form, activationProbability, effect, buff, start = start, end = end)


class KiDependent(StartOfTurn):
    def __init__(self, form, activationProbability, effect, buff, args):
        ki = args[0]
        super().__init__(form, activationProbability, effect, buff, ki = ki)


class SlotDependent(StartOfTurn):
    def __init__(self, form, activationProbability, effect, buff, args):
        slots = args[0]
        super().__init__(form, activationProbability, effect, buff, slots=slots)


class PerAttackReceived(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, args):
        super().__init__(form, activationProbability, effect, buff)
        self.max = args[0]

    def applyToState(self, state):
        match self.effect:
            case "Ki":
                state.constantKi += np.minimum(self.buff * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot] + state.numAttacksReceived), self.max)
            case "ATK":
                state.p2Atk += np.minimum(self.buff * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot] + state.numAttacksReceived), self.max)
            case "DEF":
                state.p2DefA += np.minimum((2 * state.numAttacksReceived + NUM_ATTACKS_RECEIVED[state.slot] - 1) * self.buff / 2, self.max)
            case "Critical Hit":
                state.crit += np.minimum(self.buff * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot] + state.numAttacksReceived), self.max)


class WithinSameTurnAfterReceivingAttack(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, args):
        super().__init__(form, activationProbability, effect, buff)

    def applyToState(self, state):
        match self.effect:
            case "DEF":
                state.p2DefA += self.buff * (NUM_ATTACKS_RECEIVED[state.slot] - 1) / NUM_ATTACKS_RECEIVED[state.slot]
            case "Attack Effective to All":
                state.AEAAT = self.buff * np.minimum(NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot], 1.0)      


class PerRainbowOrb(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, args):
        super().__init__(form, activationProbability, effect, buff)

    def applyToState(self, state):
        buffFromRainbowOrbs = self.buff * state.numRainbowOrbs
        match self.effect:
            case "Critical Hit":
                state.crit += buffFromRainbowOrbs
            case "Damage Reduction":
                state.dmgRedA += buffFromRainbowOrbs
                state.dmgRedB += buffFromRainbowOrbs
            case "Evasion":
                state.pEvade += buffFromRainbowOrbs


class Nullification(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, args):
        super().__init__(form, activationProbability, effect, buff)
        self.hasCounter = args[0]

    def applyToState(self, state):
        pNullify = self.activationProbability * (1.0 - (1.0 - saFracConversion[self.effect]) ** 2)
        state.pNullify = (1.0 - state.pNullify) * pNullify + (1.0 - pNullify) * state.pNullify
        if self.hasCounter:
            state.pCounterSA = (1.0 - state.pCounterSA) * pNullify + (1.0 - pNullify) * state.pCounterSA
        

if __name__ == '__main__':
    kit = Kit(1)