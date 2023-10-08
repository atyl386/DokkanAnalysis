import click as clc
import datetime as dt

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
CLASSES = ['S', 'E']
TYPES = ['AGL', 'INT', 'PHY', 'STR', 'TEQ']
ATT_DEBUFF_PASSIVE_CONVERSION_GRADIENT = 10 # 10% attack down for 2 turns = SBR score of +1
LEADER_SKILL_TIERS = ['<150%', '1 x 150%', '2 x 150%', '2 x 150-170% / 1 x 170%', '2 x 170% / 1 x 180%', '200% limted', '200% small', '200% medium', '200% large']
LEADER_SKILL_SCORES = [0, 1, 2, 4, 5, 7, 8, 9, 10] # [-]
DEBUFF_DURATIONS = ['0', '1', '2'] # [turns]
SEAL_SCORE_PER_TURN = [0, 0.25, 0.75] # [SBR metric/chance to seal]
STUN_SCORE_PER_TURN = [0, 0.5, 1.5] # [SBR metric/chance to stun]
ATT_DEBUFF_SCORE_PER_TURN = [0, 1/3, 1] # [SBR metirc/attack debuff score]
ATT_DEBUFF_ON_ATT_TYPES = ['Lowers', 'Greatly Lowers']
ATT_DEBUFF_ON_ATT_SCORE = [0.25, 0.5] # [attack debuff scrore for lower and greatly lower]
MULTIPLE_ENEMY_BUFF_TIERS = ['None', 'Minor', 'Moderate', 'Major', 'Huge']
MULTIPLE_ENEMY_BUFF_SCORES = [0.25, 0.5, 1, 2] # [SBR metric]
ATTACK_ALL_SCORE = [0, 1] # [SBR metric]
ATTACK_ALL_DEBUFF_FACTOR = [1, 3] # [-]
KI_MODIFIERS_12 = ['1.4', '1.45', '1.5', '1.6'] # [-]
SUPER_ATTACK_MULTIPLIER_NAMES = ['Destructive', 'Supreme', 'Immense', 'Colossal', 'Mega-Colossal']
COUNTER_ATTACK_MULTIPLIER_NAMES = ['NA', 'Tremendous', 'Furocious']
COUNTER_ATTACK_MULTIPLIERS = [0.0, 3.0, 4.0]
SPECIAL_ATTACK_MULTIPLIER_NAMES = ['NA', '', 'Super-Intense','Mega-Colossal', 'Ultimate', 'Super-Ultimate']
SPECIAL_ATTACK_MULTIPLIERS = [0.0, 1.0 , 5.0, 5.4, 6.5, 7.5]
GIANT_RAGE_DURATION = ['0', '1', '2'] # Turns
MAX_TURN = 10

# Helper dicts
yesNo2Bool = dict(zip(YES_NO, [True, False]))
leaderSkillConversion = dict(zip(LEADER_SKILL_TIERS,LEADER_SKILL_SCORES))
sealTurnConversion = dict(zip(DEBUFF_DURATIONS,SEAL_SCORE_PER_TURN))
stunTurnConversion = dict(zip(DEBUFF_DURATIONS,STUN_SCORE_PER_TURN))
attDebuffTurnConversion = dict(zip(DEBUFF_DURATIONS,ATT_DEBUFF_SCORE_PER_TURN))
attDebuffOnAttackConversion = dict(zip(ATT_DEBUFF_ON_ATT_TYPES,ATT_DEBUFF_ON_ATT_SCORE))
multipleEnemyBuffConversion = dict(zip(MULTIPLE_ENEMY_BUFF_TIERS,MULTIPLE_ENEMY_BUFF_SCORES))
attackAllConversion = dict(zip(YES_NO, ATTACK_ALL_SCORE))
attackAllDebuffConversion = dict(zip(ATTACK_ALL_SCORE, ATTACK_ALL_DEBUFF_FACTOR))
counterAttackConversion = dict(zip(COUNTER_ATTACK_MULTIPLIER_NAMES,COUNTER_ATTACK_MULTIPLIERS))
specialAttackConversion = dict(zip(SPECIAL_ATTACK_MULTIPLIER_NAMES,SPECIAL_ATTACK_MULTIPLIERS))

class Kit:
    def __init__(self, id):
        self.id = id

    def initialQuestionaire(self):
        self.exclusivity = clc.prompt("What is the unit's exclusivity?", type=clc.Choice(EXCLUSIVITIES, case_sensitive=False), default='DF')
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

    def sbrQuestionaire(self):
        sbr_abilities = clc.prompt("Does the unit have any SBR abilities?", type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False), default='N')
        self.sbr = 0.0
        if sbr_abilities:
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
        self.sa_mult_12 = clc.prompt("What is the unit's 12 ki super attack multiplier?", type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES), default='Immense')
        if 'LR' in self.exclusivity:
            self.sa_mult_18 = clc.prompt("What is the unit's 18 ki super attack multiplier?", type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES, case_sensitive=False), default='Mega-Colossal')


    def getKitFromUser(self):
        clc.echo(f'Hello! This program will guide you through inputting the data required to enter Dokkan unit ID={self.id} into the database')
        self.initialQuestionaire()
        self.turnBasedQuestionaire()
        self.sbrQuestionaire()


if __name__ == '__main__':
    kit = Kit(1).getKitFromUser()