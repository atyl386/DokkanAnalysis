import click as clc
import datetime as dt
import numpy as np

# I think need a function/Questionaire for every type of passive ability, e.g. one for rainbow orbs, might be good to use classes here. I think this is the only way to cater for all the complexities of Dokkan passives in an automated way

# TODO:
# - Make separate file where all constants and imports are stored
# - Ideally would just pull data from database, but not up in time for new units. Would be amazing for old units though.
# - Leader skill weight should decrease from 5 as new structure adds more variability between leader skills
# - Make another command that goes through each turn 1-10 for those parameters
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
# SA multipliers for SA lv 10, 15, 20, 25
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
NUM_ATTACKS_RECIEVED = [4, 2, 2] # Average number of attacks recieved per turn. 3 elements correspons to slot 1, 2 and 3.
SLOTS = ['1', '2', '3']
TYPES_OF_BUFFS = ["Att", "Def"]

# Helper dicts
yesNo2Bool = dict(zip(YES_NO, [True, False]))
bool2Binary = dict(zip([True, False], [1, 0]))
exclusivity2Rarity = dict(zip(EXCLUSIVITIES, RARITIES))
leaderSkillConversion = dict(zip(LEADER_SKILL_TIERS,LEADER_SKILL_SCORES))
sealTurnConversion = dict(zip(DEBUFF_DURATIONS,SEAL_SCORE_PER_TURN))
stunTurnConversion = dict(zip(DEBUFF_DURATIONS,STUN_SCORE_PER_TURN))
attDebuffTurnConversion = dict(zip(DEBUFF_DURATIONS,ATT_DEBUFF_SCORE_PER_TURN))
attDebuffOnAttackConversion = dict(zip(ATT_DEBUFF_ON_ATT_NAMES,ATT_DEBUFF_ON_ATT_SCORE))
multipleEnemyBuffConversion = dict(zip(MULTIPLE_ENEMY_BUFF_TIERS,MULTIPLE_ENEMY_BUFF_SCORES))
attackAllConversion = dict(zip(YES_NO, ATTACK_ALL_SCORE))
attackAllDebuffConversion = dict(zip(ATTACK_ALL_SCORE, ATTACK_ALL_DEBUFF_FACTOR))
counterAttackConversion = dict(zip(COUNTER_ATTACK_MULTIPLIER_NAMES,COUNTER_ATTACK_MULTIPLIERS))
specialAttackConversion = dict(zip(SPECIAL_ATTACK_MULTIPLIER_NAMES,SPECIAL_ATTACK_MULTIPLIERS))
superAttackEZALevels = [
    dict(zip([False, True], TUR_SUPER_ATTACK_LEVELS)),
    dict(zip([False, True], LR_SUPER_ATTACK_LEVELS))
]
superattackMultiplerConversion = [
    dict(zip(SUPER_ATTACK_LEVELS,DESTRUCTIVE_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS,SUPREME_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS,IMMENSE_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS,COLOSSAL_MULTIPLIERS)),
    dict(zip(SUPER_ATTACK_LEVELS,MEGA_COLOSSAL_MULTIPLIERS)),
]
superAttackLevelConversion = dict(zip(UNIQUE_RARITIES,superAttackEZALevels ))
superAttackConversion = dict(zip(SUPER_ATTACK_MULTIPLIER_NAMES,superattackMultiplerConversion))

 # A kit has PassiveAbilities
class PassiveAbility: # Informal Interface
    def __init__(self, kit, start, end):
        self.kit = kit
        self.start = start # Turn the passive ability starts from
        self.end = end # Turn the passive ability ends
    def setEffect(self):
        pass

class perAttackReceived(PassiveAbility):
    def __init__(self, kit, start, end, increment, max):
        super().__init__(kit, start, end)
        self.increment = increment
        self.max = max

class defPerAttackReceived(perAttackReceived):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def setEffect(self):
        for turn in range(self.start, self.end):
            self.kit.p2DefA[turn] = min(((2 * turn + 1) * NUM_ATTACKS_RECIEVED[self.kit.slot - 1] - 1) * self.increment / 2, self.max)

class withinSameTurnAfterReceivingAttack(PassiveAbility):
    def __init__(self, kit, start, end, buff):
        super().__init__(kit, start, end)
        self.buff = buff

class defWithinSameTurnAfterReceivingAttack(withinSameTurnAfterReceivingAttack):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def setEffect(self):
        self.kit.p2DefA[self.start:self.end] = [(NUM_ATTACKS_RECIEVED[self.kit.slot - 1] - 1) / NUM_ATTACKS_RECIEVED[self.kit.slot - 1]] * (self.end - self.start)



class Kit:
    def __init__(self, id):
        self.id = id
        # Initialise arrays
        self.sa_mult_12 = np.zeros(MAX_TURN); self.sa_mult_18 = np.zeros(MAX_TURN); self.sa_12_att_buff = np.zeros(MAX_TURN); self.sa_12_def_buff = np.zeros(MAX_TURN); self.sa_18_att_buff = np.zeros(MAX_TURN); self.sa_18_def_buff = np.zeros(MAX_TURN); self.sa_12_att_stacks = np.zeros(MAX_TURN); self.sa_12_def_stacks = np.zeros(MAX_TURN); self.sa_18_att_stacks = np.zeros(MAX_TURN); self.sa_18_def_stacks = np.zeros(MAX_TURN); self.intentional12Ki = np.zeros(MAX_TURN); self.links = [['' for x in range(MAX_NUM_LINKS)] for y in range(MAX_TURN)]; self.p2DefA = np.zeros(MAX_TURN)

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
        self.special_skill_turn = clc.prompt("What is the earliest turn the unit can reliably use their single-turn active/standby skill?", default=0)
        self.special_skill_att_mult = 0.0
        if self.special_skill_turn != 0:
            self.special_skill_att_mult += specialAttackConversion[clc.prompt("What is the special attack multiplier?", clc.Choice(specialAttackConversion.keys()), default='Ultimate')]
            self.special_skill_att_mult += clc.prompt("What is the additional attack buff when performing the special attack?", default=0.0)
        self.revival_skill_turn = clc.prompt("What is the earliest turn the unit can reliably use their revive?", default=0)
        self.giant_rage_duration = clc.prompt("How many turns does the unit's giant/rage mode last for?", type=clc.Choice(GIANT_RAGE_DURATION), default='0')
        self.slot = int(clc.prompt("What slot is this unit best suited for?", type=clc.Choice(SLOTS), default='2'))

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


    def perAttackReceivedQuestionaire(self, start, end):
        numPerAttackReceivedAbilities = clc.prompt("How many different buffs does the unit get on attacks received?", default=0)
        for perAttackReceivedAbilities in range(numPerAttackReceivedAbilities):
            buffPerAttackReceived = clc.prompt("What buff does the unit get on attack received?",type=clc.Choice(TYPES_OF_BUFFS, case_sensitive=False), default="Def")
            increment = clc.prompt("How much is the buff per attack received?", default=0.2)
            max = clc.prompt("What is the maximum buff?", default=1.0)
            match buffPerAttackReceived:
                case "Def":
                    defPerAttackReceived(self, start, end, increment, max).setEffect()


    def withinSameTurnAfterReceivingAttackQuestionaire(self, start, end):
        numWithinSameTurnAfterReceivingAttackAbilities = clc.prompt("How many different buffs does the unit get within the same turn after receiving an attack?", default=0)
        for perAttackReceivedAbilities in range(numWithinSameTurnAfterReceivingAttackAbilities):
            buffAfterReceivingAttack = clc.prompt("What buff does the unit get after receiving an attack?",type=clc.Choice(TYPES_OF_BUFFS, case_sensitive=False), default="Def")
            buff = clc.prompt("How much is the buff after receiving an attack?", default=0.5)
            match buffAfterReceivingAttack:
                case "Def":
                    defPerAttackReceived(self, start, end, buff).setEffect()        

    def turnBasedQuestionaire(self):
        # Ask the user the bunch of questions then, go through the while loop to do the calcs
        # Links first
        formTurnStarts = [1] # Every unit starts on their first turn
        while(formTurnStarts[-1] != MAX_TURN+1):
            formTurnStarts.append(clc.prompt(f"On what turn does the unit transform? Will keep asking until enter {MAX_TURN+1}", default=MAX_TURN+1))
        for form in range(len(formTurnStarts)-1): # Don't do last one as that indicates end
            turn = formTurnStarts[form] - 1 # Get the first turn of 'form'. Subtract 1 to make indexing easier.
            formDuration = formTurnStarts[form + 1] - 1 - turn
            self.sa_mult_12[turn:turn + formDuration] = [superAttackConversion[clc.prompt("What is the unit's 12 ki super attack multiplier?", type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES), default='Immense')][superAttackLevelConversion[self.rarity][self.eza]]]*formDuration
            self.sa_12_att_buff[turn:turn + formDuration] = [clc.prompt("What is the unit's 12 ki attack buff?", default=0.0)]*formDuration
            if self.sa_12_att_buff[turn] != 0:
                self.sa_12_att_stacks[turn:turn + formDuration] = [clc.prompt("How many turns does unit's 12 ki attack buff last for?", default=1)]*formDuration
            self.sa_12_def_buff[turn:turn + formDuration] = [clc.prompt("What is the unit's 12 ki defense buff?", default=0.0)]*formDuration
            if self.sa_12_def_buff[turn] != 0:
                self.sa_12_def_stacks[turn:turn + formDuration] = [clc.prompt("How many turns does unit's 12 ki defense buff last for?", default=1)]*formDuration
            if self.rarity == 'LR':
                self.sa_mult_18[turn:turn + formDuration] = [superAttackConversion[clc.prompt("What is the unit's 18 ki super attack multiplier?", type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES), default='Mega-Colossal')][superAttackLevelConversion[self.rarity][self.eza]]]*formDuration
                self.sa_18_att_buff[turn:turn + formDuration] = [clc.prompt("What is the unit's 18 ki attack buff?", default=0.0)]*formDuration
                if self.sa_18_att_buff[turn] != 0:
                    self.sa_18_att_stacks[turn:turn + formDuration] = [clc.prompt("How many turns does unit's 18 ki attack buff last for?", default=1)]*formDuration
                self.sa_18_def_buff[turn:turn + formDuration] = [clc.prompt("What is the unit's 18 ki defense buff?", default=0.0)]*formDuration
                if self.sa_18_def_buff[turn] != 0:
                    self.sa_18_def_stacks[turn:turn + formDuration] = [clc.prompt("How many turns does unit's 18 ki defense buff last for?", default=1)]*formDuration
                self.intentional12Ki[turn:turn + formDuration] = [yesNo2Bool[clc.prompt("Should a 12 Ki be targetted for this unit?", default='N')]]*formDuration
            for link in range(MAX_NUM_LINKS):
                self.links[turn:turn + formDuration][link] = [clc.prompt(f"What is the unit's link # {link+1}", type = clc.Choice(LINKS, case_sensitive=False), default='Fierce Battle')]*formDuration
            #assert len(np.unique(self.links))==MAX_NUM_LINKS, 'Duplicate links'
            # for each passiveAbility subclass
            # Ask user if has those abilities
            # Do this recursively till get to bottom of class inheritance
            # call class.getEffect(self, arguments gotten from questions)
            self.perAttackReceivedQuestionaire(turn, turn + formDuration)
            self.withinSameTurnAfterReceivingAttackQuestionaire(turn, turn + formDuration)


    """  def calculateStats(self):
        isFullyBuiltUp = False
        turn = 1
        while not(isFullyBuiltUp) or turn > MAX_TURN:
            turn  += 1 """
    def getKitFromUser(self):
        clc.echo(f'Hello! This program will guide you through inputting the data required to enter Dokkan unit ID={self.id} into the database')
        self.initialQuestionaire()
        self.turnBasedQuestionaire()
        self.sbrQuestionaire()


if __name__ == '__main__':
    kit = Kit(1).getKitFromUser()